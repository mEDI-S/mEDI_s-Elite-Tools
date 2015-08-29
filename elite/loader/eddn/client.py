# -*- coding: UTF8
'''
Created on 29.08.2015

@author: mEDI

update price and insert Shipyard data from  EDDN = Elite:Dangerous Data Network

EDDN very uncertain source
anyone can upload data, does not allow inserts only updates

'''
__sourceID__ = 5

import zlib
import zmq
#import simplejson
import sys
import time
import json

import random    
import threading
import queue
from datetime import datetime, timedelta
from dateutil.parser import parse as dateutil_parse
import elite

class _child(threading.Thread):
    """
        Options
    """
    __relayEDDNList = ['tcp://eddn-relay.elite-markets.net:9500','tcp://eddn-relay.ed-td.space:9500']
    __relayEDDNLast = random.randint(-1, len(__relayEDDNList)-1)

    __relayEDDN = None
    __timeoutEDDN           = 600000

    def __init__(self, data):
        threading.Thread.__init__(self) 
        self.data = data
        self._active = True
    
    def getNextEDDNrelay(self):
        self.__relayEDDNLast += 1 
        
        if self.__relayEDDNLast > len(self.__relayEDDNList)-1:
            self.__relayEDDNLast = 0

        return self.__relayEDDNList[self.__relayEDDNLast]


    def run(self):
    
        context     = zmq.Context()
        subscriber  = context.socket(zmq.SUB)
        
        subscriber.setsockopt(zmq.SUBSCRIBE, b"")
        subscriber.setsockopt(zmq.RCVTIMEO, self.__timeoutEDDN)
    
        while self._active:
            try:
                self.__relayEDDN = self.getNextEDDNrelay()
                print("EDDN connect to: %s" % self.__relayEDDN)
                subscriber.connect(self.__relayEDDN)
                
                while self._active:
                    __message   = subscriber.recv()
                    
                    if __message == False:
                        subscriber.disconnect(self.__relayEDDN)
                        break
                    
                    __message   = zlib.decompress(__message)
                    
                    self.data.put_nowait(__message)           

                    
            except zmq.ZMQError as e:
                print ('ZMQSocketException: ' + str(e))
                sys.stdout.flush()
                subscriber.disconnect(self.__relayEDDN)
                time.sleep(5)

    def stop(self):
        self._active = False        


def convertStrptimeToDatetimeUTC( timestr ):
    #print( "convert", timestr )
    d = dateutil_parse(timestr)

    if not d:
        print("problem mit", timestr )
        return

    if d.utcoffset():
        d = d - d.utcoffset()
    d = d.replace(tzinfo=None)

    return d


class loader(object):

    def __init__(self, mydb=None):
        '''
        Constructor
        '''
        self.__childTask = None
        self.data = queue.Queue()
        
        self.mydb = mydb


    def start(self):      
        if self.__childTask:
            self.__childTask.stop()

        self.__childTask = _child(self.data)
        self.__childTask.daemon=True
        self.__childTask.start()

    def stop(self):
        if self.__childTask:
            self.__childTask.stop()

    def isRunning(self):
        if self.__childTask:
            return self.__childTask.is_alive()

    def get(self):
        return self.data.get()

    def update(self):
        if not self.data.empty():
            while not self.data.empty():
                data = self.data.get()
                if data:
                    data = data.decode(encoding='utf-8',errors='replace')
                    #print("import", data )
                    self.importData(data)

        if self.__childTask and self.isRunning() == False:
            print("restart child")
            self.start()

    def importCommodity2Data(self, timestamp):

        systemID = self.mydb.getSystemIDbyName( self.jsonData["message"]["systemName"] )
        stationID = self.mydb.getStationID(systemID, self.jsonData["message"]["stationName"]  )
        if not stationID: return

        updateItems = []
        for item in self.jsonData["message"]["commodities"]:
            itemID = self.mydb.getItemID(item["name"])
            if itemID:
                updateItems.append( [ item["sellPrice"] , item["buyPrice"], item["demand"], item["supply"], timestamp ,stationID,itemID, timestamp  ] ) 
            else:
                print("EDDN wrong itemname?:", item)
            #print(item)

        if updateItems:
            cur = self.mydb.cursor()

            cur.executemany( " UPDATE price SET StationBuy=?, StationSell=?, Dammand=?, Stock=?, modified=?, source=5 where StationID=? AND ItemID=? AND modified<?", updateItems)
            if cur.rowcount:
                print("update in %s:%s %s items " % (self.jsonData["message"]["systemName"],self.jsonData["message"]["stationName"],cur.rowcount )) 
    
    def importShipyard1Data(self, timestamp):
        systemID = self.mydb.getSystemIDbyName( self.jsonData["message"]["systemName"] )
        stationID = self.mydb.getStationID(systemID, self.jsonData["message"]["stationName"]  )
        if not stationID: return
        cur = self.mydb.cursor()

        ''' Delete first all old Ships from this station'''
        cur.execute( "delete from shipyard where StationID=?", (stationID,))

        for ship in self.jsonData["message"]["ships"]:
            shipID = self.mydb.getShiptID( ship )
            if not shipID:
                print("EDDN new shipname: %s " % ship )
                cur.execute( "insert or IGNORE into ships (Name) values (?) ", (ship,))
                shipID = self.mydb.getShiptID(ship )

            if shipID:
                cur.execute( "insert or ignore into shipyard (SystemID, StationID, ShipID, modifydate ) values (?,?,?,?) ", (systemID, stationID, shipID, timestamp) )
                   

    def importData(self, data):
        self.jsonData = json.loads(data)
        if not self.jsonData: return

        timestamp = convertStrptimeToDatetimeUTC( self.jsonData["message"]["timestamp"] )
        gatewayTime = convertStrptimeToDatetimeUTC( self.jsonData["header"]["gatewayTimestamp"] )

        if not timestamp or not gatewayTime: return
        
        ''' drop data with wrong datetime time or older or newer as 10 min'''
        maxTimeDiff = timedelta(minutes=10) 
        if timestamp-gatewayTime > maxTimeDiff or gatewayTime-timestamp > maxTimeDiff:
            print("drop wrong time", timestamp ,gatewayTime, gatewayTime - timestamp)
            return

        if gatewayTime < timestamp: # Sender computer is in the future
            timestamp = gatewayTime
            
        if  self.jsonData['$schemaRef'] == 'http://schemas.elite-markets.net/eddn/commodity/2':
            self.importCommodity2Data(timestamp)
        elif  self.jsonData['$schemaRef'] == 'http://schemas.elite-markets.net/eddn/shipyard/1':
            self.importShipyard1Data(timestamp)


        self.mydb.con.commit()

if __name__ == '__main__':
    mydb = elite.db(guiMode=True,DBPATH="../../../db/my.db")
    my = loader(mydb)
    data = '{"header": {"softwareVersion": "1.7.2.0", "gatewayTimestamp": "2015-08-29T13:15:03.561146", "softwareName": "E:D Market Connector [Windows]", "uploaderID": "mEDI_S"}, "$schemaRef": "http://schemas.elite-markets.net/eddn/commodity/2", "message": {"commodities": [{"name": "Explosives", "buyPrice": 223, "supplyLevel": "Med", "supply": 484304, "demand": 0, "sellPrice": 206}, {"name": "Hydrogen Fuel", "buyPrice": 113, "supplyLevel": "Med", "supply": 813392, "demand": 0, "sellPrice": 107}, {"name": "Mineral Oil", "buyPrice": 0, "supply": 0, "demand": 15101943, "sellPrice": 325, "demandLevel": "High"}, {"name": "Clothing", "buyPrice": 0, "supply": 0, "demand": 624393, "sellPrice": 474, "demandLevel": "High"}, {"name": "Consumer Technology", "buyPrice": 0, "supply": 0, "demand": 86795, "sellPrice": 7489, "demandLevel": "High"}, {"name": "Domestic Appliances", "buyPrice": 0, "supply": 0, "demand": 186225, "sellPrice": 733, "demandLevel": "High"}, {"name": "Animal Meat", "buyPrice": 0, "supply": 0, "demand": 173232, "sellPrice": 1631, "demandLevel": "High"}, {"name": "Coffee", "buyPrice": 0, "supply": 0, "demand": 43309, "sellPrice": 1631, "demandLevel": "High"}, {"name": "Fish", "buyPrice": 0, "supply": 0, "demand": 483976, "sellPrice": 583, "demandLevel": "High"}, {"name": "Food Cartridges", "buyPrice": 0, "supply": 0, "demand": 8072, "sellPrice": 141, "demandLevel": "Low"}, {"name": "Fruit And Vegetables", "buyPrice": 0, "supply": 0, "demand": 156266, "sellPrice": 474, "demandLevel": "High"}, {"name": "Grain", "buyPrice": 0, "supply": 0, "demand": 1042956, "sellPrice": 342, "demandLevel": "High"}, {"name": "Synthetic Meat", "buyPrice": 0, "supply": 0, "demand": 100903, "sellPrice": 396, "demandLevel": "High"}, {"name": "Tea", "buyPrice": 0, "supply": 0, "demand": 157159, "sellPrice": 1831, "demandLevel": "High"}, {"name": "Polymers", "buyPrice": 64, "supplyLevel": "High", "supply": 2416125, "demand": 0, "sellPrice": 53}, {"name": "Semiconductors", "buyPrice": 693, "supplyLevel": "High", "supply": 487086, "demand": 0, "sellPrice": 669}, {"name": "Superconductors", "buyPrice": 6154, "supplyLevel": "High", "supply": 1057350, "demand": 0, "sellPrice": 6028}, {"name": "Microbial Furnaces", "buyPrice": 0, "supply": 0, "demand": 14350347, "sellPrice": 333, "demandLevel": "High"}, {"name": "Power Generators", "buyPrice": 0, "supply": 0, "demand": 680755, "sellPrice": 648, "demandLevel": "Med"}, {"name": "Water Purifiers", "buyPrice": 0, "supply": 0, "demand": 56909, "sellPrice": 313, "demandLevel": "Low"}, {"name": "Basic Medicines", "buyPrice": 0, "supply": 0, "demand": 7813, "sellPrice": 315, "demandLevel": "Low"}, {"name": "Performance Enhancers", "buyPrice": 0, "supply": 0, "demand": 120548, "sellPrice": 7489, "demandLevel": "High"}, {"name": "Progenitor Cells", "buyPrice": 0, "supply": 0, "demand": 48220, "sellPrice": 7489, "demandLevel": "High"}, {"name": "Aluminium", "buyPrice": 251, "supplyLevel": "Med", "supply": 864831, "demand": 0, "sellPrice": 233}, {"name": "Beryllium", "buyPrice": 7998, "supplyLevel": "Med", "supply": 62382, "demand": 0, "sellPrice": 7834}, {"name": "Cobalt", "buyPrice": 524, "supplyLevel": "High", "supply": 5600630, "demand": 0, "sellPrice": 497}, {"name": "Copper", "buyPrice": 329, "supplyLevel": "High", "supply": 7811503, "demand": 0, "sellPrice": 312}, {"name": "Gallium", "buyPrice": 4666, "supplyLevel": "High", "supply": 1034762, "demand": 0, "sellPrice": 4569}, {"name": "Gold", "buyPrice": 8780, "supplyLevel": "High", "supply": 933541, "demand": 0, "sellPrice": 8693}, {"name": "Indium", "buyPrice": 5387, "supplyLevel": "High", "supply": 1302261, "demand": 0, "sellPrice": 5276}, {"name": "Lithium", "buyPrice": 1444, "supplyLevel": "Med", "supply": 216208, "demand": 0, "sellPrice": 1395}, {"name": "Silver", "buyPrice": 4625, "supplyLevel": "Med", "supply": 91172, "demand": 0, "sellPrice": 4529}, {"name": "Tantalum", "buyPrice": 3503, "supplyLevel": "High", "supply": 519003, "demand": 0, "sellPrice": 3429}, {"name": "Titanium", "buyPrice": 800, "supplyLevel": "High", "supply": 4682272, "demand": 0, "sellPrice": 772}, {"name": "Uranium", "buyPrice": 2284, "supplyLevel": "High", "supply": 1694679, "demand": 0, "sellPrice": 2236}, {"name": "Bauxite", "buyPrice": 0, "supply": 0, "demand": 2813726, "sellPrice": 178, "demandLevel": "Med"}, {"name": "Bertrandite", "buyPrice": 0, "supply": 0, "demand": 2279203, "sellPrice": 2927, "demandLevel": "High"}, {"name": "Coltan", "buyPrice": 0, "supply": 0, "demand": 4244249, "sellPrice": 1723, "demandLevel": "High"}, {"name": "Gallite", "buyPrice": 0, "supply": 0, "demand": 3233749, "sellPrice": 2301, "demandLevel": "High"}, {"name": "Indite", "buyPrice": 0, "supply": 0, "demand": 2725294, "sellPrice": 2552, "demandLevel": "Med"}, {"name": "Lepidolite", "buyPrice": 0, "supply": 0, "demand": 5972797, "sellPrice": 774, "demandLevel": "Med"}, {"name": "Painite", "buyPrice": 0, "supply": 0, "demand": 8931, "sellPrice": 35946, "demandLevel": "High"}, {"name": "Rutile", "buyPrice": 0, "supply": 0, "demand": 5652848, "sellPrice": 485, "demandLevel": "High"}, {"name": "Uraninite", "buyPrice": 0, "supply": 0, "demand": 6055272, "sellPrice": 1161, "demandLevel": "High"}, {"name": "Beer", "buyPrice": 0, "supply": 0, "demand": 674172, "sellPrice": 304, "demandLevel": "High"}, {"name": "Liquor", "buyPrice": 0, "supply": 0, "demand": 39958, "sellPrice": 851, "demandLevel": "High"}, {"name": "Tobacco", "buyPrice": 0, "supply": 0, "demand": 48070, "sellPrice": 5462, "demandLevel": "High"}, {"name": "Wine", "buyPrice": 0, "supply": 0, "demand": 807220, "sellPrice": 396, "demandLevel": "High"}, {"name": "SAP 8 Core Container", "buyPrice": 0, "supply": 0, "demand": 357177, "sellPrice": 59910, "demandLevel": "High"}, {"name": "Imperial Slaves", "buyPrice": 0, "supply": 0, "demand": 113622, "sellPrice": 16801, "demandLevel": "Med"}, {"name": "Advanced Catalysers", "buyPrice": 0, "supply": 0, "demand": 1885293, "sellPrice": 3327, "demandLevel": "High"}, {"name": "H.E. Suits", "buyPrice": 0, "supply": 0, "demand": 1209464, "sellPrice": 424, "demandLevel": "High"}, {"name": "Resonating Separators", "buyPrice": 0, "supply": 0, "demand": 1391154, "sellPrice": 6598, "demandLevel": "High"}, {"name": "Synthetic Fabrics", "buyPrice": 94, "supplyLevel": "High", "supply": 2338930, "demand": 0, "sellPrice": 83}, {"name": "Biowaste", "buyPrice": 14, "supplyLevel": "High", "supply": 63023, "demand": 0, "sellPrice": 10}, {"name": "Chemical Waste", "buyPrice": 0, "supply": 0, "demand": 644705, "sellPrice": 107, "demandLevel": "High"}, {"name": "Scrap", "buyPrice": 0, "supply": 0, "demand": 176228, "sellPrice": 70, "demandLevel": "Low"}, {"name": "Non-Lethal Weapons", "buyPrice": 0, "supply": 0, "demand": 670, "sellPrice": 1764, "demandLevel": "Low"}, {"name": "Reactive Armour", "buyPrice": 0, "supply": 0, "demand": 3840, "sellPrice": 2166, "demandLevel": "Med"}], "timestamp": "2015-08-29T13:15:04Z", "systemName": "Cemiess", "stationName": "Glass City"}}'
    data = '{"header": {"softwareVersion": "1.7.2.0", "gatewayTimestamp": "2015-08-29T04:54:04+03:00", "softwareName": "E:D Market Connector [Windows]", "uploaderID": "mEDI_S"}, "$schemaRef": "http://schemas.elite-markets.net/eddn/commodity/2", "message": {"commodities": [{"name": "Explosives", "buyPrice": 223, "supplyLevel": "Med", "supply": 484304, "demand": 0, "sellPrice": 206}, {"name": "Hydrogen Fuel", "buyPrice": 113, "supplyLevel": "Med", "supply": 813392, "demand": 0, "sellPrice": 107}, {"name": "Mineral Oil", "buyPrice": 0, "supply": 0, "demand": 15101943, "sellPrice": 325, "demandLevel": "High"}, {"name": "Clothing", "buyPrice": 0, "supply": 0, "demand": 624393, "sellPrice": 474, "demandLevel": "High"}, {"name": "Consumer Technology", "buyPrice": 0, "supply": 0, "demand": 86795, "sellPrice": 7489, "demandLevel": "High"}, {"name": "Domestic Appliances", "buyPrice": 0, "supply": 0, "demand": 186225, "sellPrice": 733, "demandLevel": "High"}, {"name": "Animal Meat", "buyPrice": 0, "supply": 0, "demand": 173232, "sellPrice": 1631, "demandLevel": "High"}, {"name": "Coffee", "buyPrice": 0, "supply": 0, "demand": 43309, "sellPrice": 1631, "demandLevel": "High"}, {"name": "Fish", "buyPrice": 0, "supply": 0, "demand": 483976, "sellPrice": 583, "demandLevel": "High"}, {"name": "Food Cartridges", "buyPrice": 0, "supply": 0, "demand": 8072, "sellPrice": 141, "demandLevel": "Low"}, {"name": "Fruit And Vegetables", "buyPrice": 0, "supply": 0, "demand": 156266, "sellPrice": 474, "demandLevel": "High"}, {"name": "Grain", "buyPrice": 0, "supply": 0, "demand": 1042956, "sellPrice": 342, "demandLevel": "High"}, {"name": "Synthetic Meat", "buyPrice": 0, "supply": 0, "demand": 100903, "sellPrice": 396, "demandLevel": "High"}, {"name": "Tea", "buyPrice": 0, "supply": 0, "demand": 157159, "sellPrice": 1831, "demandLevel": "High"}, {"name": "Polymers", "buyPrice": 64, "supplyLevel": "High", "supply": 2416125, "demand": 0, "sellPrice": 53}, {"name": "Semiconductors", "buyPrice": 693, "supplyLevel": "High", "supply": 487086, "demand": 0, "sellPrice": 669}, {"name": "Superconductors", "buyPrice": 6154, "supplyLevel": "High", "supply": 1057350, "demand": 0, "sellPrice": 6028}, {"name": "Microbial Furnaces", "buyPrice": 0, "supply": 0, "demand": 14350347, "sellPrice": 333, "demandLevel": "High"}, {"name": "Power Generators", "buyPrice": 0, "supply": 0, "demand": 680755, "sellPrice": 648, "demandLevel": "Med"}, {"name": "Water Purifiers", "buyPrice": 0, "supply": 0, "demand": 56909, "sellPrice": 313, "demandLevel": "Low"}, {"name": "Basic Medicines", "buyPrice": 0, "supply": 0, "demand": 7813, "sellPrice": 315, "demandLevel": "Low"}, {"name": "Performance Enhancers", "buyPrice": 0, "supply": 0, "demand": 120548, "sellPrice": 7489, "demandLevel": "High"}, {"name": "Progenitor Cells", "buyPrice": 0, "supply": 0, "demand": 48220, "sellPrice": 7489, "demandLevel": "High"}, {"name": "Aluminium", "buyPrice": 251, "supplyLevel": "Med", "supply": 864831, "demand": 0, "sellPrice": 233}, {"name": "Beryllium", "buyPrice": 7998, "supplyLevel": "Med", "supply": 62382, "demand": 0, "sellPrice": 7834}, {"name": "Cobalt", "buyPrice": 524, "supplyLevel": "High", "supply": 5600630, "demand": 0, "sellPrice": 497}, {"name": "Copper", "buyPrice": 329, "supplyLevel": "High", "supply": 7811503, "demand": 0, "sellPrice": 312}, {"name": "Gallium", "buyPrice": 4666, "supplyLevel": "High", "supply": 1034762, "demand": 0, "sellPrice": 4569}, {"name": "Gold", "buyPrice": 8780, "supplyLevel": "High", "supply": 933541, "demand": 0, "sellPrice": 8693}, {"name": "Indium", "buyPrice": 5387, "supplyLevel": "High", "supply": 1302261, "demand": 0, "sellPrice": 5276}, {"name": "Lithium", "buyPrice": 1444, "supplyLevel": "Med", "supply": 216208, "demand": 0, "sellPrice": 1395}, {"name": "Silver", "buyPrice": 4625, "supplyLevel": "Med", "supply": 91172, "demand": 0, "sellPrice": 4529}, {"name": "Tantalum", "buyPrice": 3503, "supplyLevel": "High", "supply": 519003, "demand": 0, "sellPrice": 3429}, {"name": "Titanium", "buyPrice": 800, "supplyLevel": "High", "supply": 4682272, "demand": 0, "sellPrice": 772}, {"name": "Uranium", "buyPrice": 2284, "supplyLevel": "High", "supply": 1694679, "demand": 0, "sellPrice": 2236}, {"name": "Bauxite", "buyPrice": 0, "supply": 0, "demand": 2813726, "sellPrice": 178, "demandLevel": "Med"}, {"name": "Bertrandite", "buyPrice": 0, "supply": 0, "demand": 2279203, "sellPrice": 2927, "demandLevel": "High"}, {"name": "Coltan", "buyPrice": 0, "supply": 0, "demand": 4244249, "sellPrice": 1723, "demandLevel": "High"}, {"name": "Gallite", "buyPrice": 0, "supply": 0, "demand": 3233749, "sellPrice": 2301, "demandLevel": "High"}, {"name": "Indite", "buyPrice": 0, "supply": 0, "demand": 2725294, "sellPrice": 2552, "demandLevel": "Med"}, {"name": "Lepidolite", "buyPrice": 0, "supply": 0, "demand": 5972797, "sellPrice": 774, "demandLevel": "Med"}, {"name": "Painite", "buyPrice": 0, "supply": 0, "demand": 8931, "sellPrice": 35946, "demandLevel": "High"}, {"name": "Rutile", "buyPrice": 0, "supply": 0, "demand": 5652848, "sellPrice": 485, "demandLevel": "High"}, {"name": "Uraninite", "buyPrice": 0, "supply": 0, "demand": 6055272, "sellPrice": 1161, "demandLevel": "High"}, {"name": "Beer", "buyPrice": 0, "supply": 0, "demand": 674172, "sellPrice": 304, "demandLevel": "High"}, {"name": "Liquor", "buyPrice": 0, "supply": 0, "demand": 39958, "sellPrice": 851, "demandLevel": "High"}, {"name": "Tobacco", "buyPrice": 0, "supply": 0, "demand": 48070, "sellPrice": 5462, "demandLevel": "High"}, {"name": "Wine", "buyPrice": 0, "supply": 0, "demand": 807220, "sellPrice": 396, "demandLevel": "High"}, {"name": "SAP 8 Core Container", "buyPrice": 0, "supply": 0, "demand": 357177, "sellPrice": 59910, "demandLevel": "High"}, {"name": "Imperial Slaves", "buyPrice": 0, "supply": 0, "demand": 113622, "sellPrice": 16801, "demandLevel": "Med"}, {"name": "Advanced Catalysers", "buyPrice": 0, "supply": 0, "demand": 1885293, "sellPrice": 3327, "demandLevel": "High"}, {"name": "H.E. Suits", "buyPrice": 0, "supply": 0, "demand": 1209464, "sellPrice": 424, "demandLevel": "High"}, {"name": "Resonating Separators", "buyPrice": 0, "supply": 0, "demand": 1391154, "sellPrice": 6598, "demandLevel": "High"}, {"name": "Synthetic Fabrics", "buyPrice": 94, "supplyLevel": "High", "supply": 2338930, "demand": 0, "sellPrice": 83}, {"name": "Biowaste", "buyPrice": 14, "supplyLevel": "High", "supply": 63023, "demand": 0, "sellPrice": 10}, {"name": "Chemical Waste", "buyPrice": 0, "supply": 0, "demand": 644705, "sellPrice": 107, "demandLevel": "High"}, {"name": "Scrap", "buyPrice": 0, "supply": 0, "demand": 176228, "sellPrice": 70, "demandLevel": "Low"}, {"name": "Non-Lethal Weapons", "buyPrice": 0, "supply": 0, "demand": 670, "sellPrice": 1764, "demandLevel": "Low"}, {"name": "Reactive Armour", "buyPrice": 0, "supply": 0, "demand": 3840, "sellPrice": 2166, "demandLevel": "Med"}], "timestamp": "2015-08-29T04:54:04+03:00", "systemName": "Cemiess", "stationName": "Glass City"}}'
    data = '{"header": {"softwareVersion": "1.7.2.0", "gatewayTimestamp": "2015-08-29T16:50:50.266090", "softwareName": "E:D Market Connector [Windows]", "uploaderID": "cb7c13ba2a3146fc47be41672f033151"}, "$schemaRef": "http://schemas.elite-markets.net/eddn/shipyard/1", "message": {"timestamp": "2015-08-29T16:50:46Z", "systemName": "LP 816-60", "stationName": "Garratt Landing", "ships": ["Sidewinder", "Hauler", "Asp", "Eagle", "Vulture", "Adder", "Type-7 Transporter", "Type-6 Transporter", "Federal Dropship"]}}'


#    my.importData(data)
#    sys.exit()
    my.start()

    while my.isRunning():
        time.sleep(5)
        my.update()
    
    my.stop()
    