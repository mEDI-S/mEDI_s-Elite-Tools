# -*- coding: UTF8
'''
Created on 28.09.2015

@author: mEDI
'''

from dateutil.parser import parse as dateutil_parse
import json
from datetime import timedelta
import elite


class EDDNimport(object):


    def __init__(self, mydb):
        self.mydb = mydb
        self.outfitting = elite.outfitting(self.mydb)

    def convertStrptimeToDatetimeUTC(self, timestr):
    
        d = dateutil_parse(timestr)
    
        if not d:
            return
    
        if d.utcoffset():
            d = d - d.utcoffset()

        d = d.replace(tzinfo=None)
    
        return d
    

    def importData(self, data):
        if isinstance(data, str):
            jsonData = json.loads(data)
        elif isinstance(data, dict):
            jsonData = data
        else:
            print("importData init bug")

        if not jsonData:
            return

        timestamp = self.convertStrptimeToDatetimeUTC(jsonData["message"]["timestamp"])
        gatewayTime = self.convertStrptimeToDatetimeUTC(jsonData["header"]["gatewayTimestamp"])

        if not timestamp or not gatewayTime:
            print("times wrong?", timestamp, gatewayTime)
            return
        
        ''' drop data with wrong datetime time or older or newer as 10 min'''
        maxTimeDiff = timedelta(minutes=10)
        if timestamp - gatewayTime > maxTimeDiff or gatewayTime - timestamp > maxTimeDiff:
            print("drop wrong time", timestamp, gatewayTime, gatewayTime - timestamp)
            return

        if gatewayTime < timestamp:  # Sender computer is in the future
            timestamp = gatewayTime
            
        if jsonData['$schemaRef'] == 'http://schemas.elite-markets.net/eddn/commodity/2':
            self.importCommodity2Data(timestamp, jsonData)
        elif jsonData['$schemaRef'] == 'http://schemas.elite-markets.net/eddn/shipyard/1':
            self.importShipyard1Data(timestamp, jsonData)
        elif jsonData['$schemaRef'] == 'http://schemas.elite-markets.net/eddn/outfitting/1':
            self.importOutfitting1Data(timestamp, jsonData)
        else:
            print("unkonwn schema %s" % jsonData['$schemaRef'] )

#        self.mydb.con.commit()


    def importCommodity2Data(self, timestamp, jsonData):
        systemID = self.mydb.getSystemIDbyName(jsonData["message"]["systemName"])
        stationID = self.mydb.getStationID(systemID, jsonData["message"]["stationName"])
        if not stationID:
            return

        updateItems = []
        for item in jsonData["message"]["commodities"]:
            itemID = self.mydb.getItemID(item["name"])
            if itemID:
                updateItems.append([ item["sellPrice"], item["buyPrice"], item["demand"], item["supply"], timestamp, stationID, itemID, timestamp  ])
            else:
                print("EDDN wrong itemname?:", item)

        if updateItems:
            cur = self.mydb.cursor()

            cur.executemany(" UPDATE price SET StationBuy=?, StationSell=?, Dammand=?, Stock=?, modified=?, source=5 where StationID=? AND ItemID=? AND modified<?", updateItems)
            if cur.rowcount:
                print("update in %s:%s %s items " % (jsonData["message"]["systemName"], jsonData["message"]["stationName"], cur.rowcount))

            cur.close()


    def importShipyard1Data(self, timestamp, jsonData):
        systemID = self.mydb.getSystemIDbyName(jsonData["message"]["systemName"])
        stationID = self.mydb.getStationID(systemID, jsonData["message"]["stationName"])
        if not stationID:
            return
        cur = self.mydb.cursor()

        ''' Delete first all old Ships from this station'''
        cur.execute("delete from shipyard where StationID=?", (stationID,))

        for ship in jsonData["message"]["ships"]:
            shipID = self.mydb.getShipID(ship, True)

            if shipID:
                cur.execute("insert or ignore into shipyard (SystemID, StationID, ShipID, modifydate ) values (?,?,?,?) ", (systemID, stationID, shipID, timestamp))

        cur.close()


    def importOutfitting1Data(self, timestamp, jsonData):
        systemID = self.mydb.getSystemIDbyName(jsonData["message"]["systemName"])
        stationID = self.mydb.getStationID(systemID, jsonData["message"]["stationName"])
        if not stationID:
            return

#        print("importOutfitting1Data", jsonData)
        cur = self.mydb.cursor()

        for modules in jsonData["message"]["modules"]:
            categoryID = self.outfitting.getOutfittingCategoryID(modules['category'], True)
            nameID = self.outfitting.getOutfittingNameID(modules['name'], True)
            classID = modules['class']

            guidanceID = None
            if 'guidance' in modules:
                guidanceID = self.outfitting.getOutfittingGuidanceID(modules['guidance'], True)

            mountID = None
            if 'mount' in modules:
                mountID = self.outfitting.getOutfittingMountID(modules['mount'], True)

            shipID = None
            if 'ship' in modules:
                shipID = self.mydb.getShipID(modules['ship'], True)
                if not shipID:
                    return
                
            rating = modules['rating']

            if not shipID:
                shipID = 0
            if not guidanceID:
                guidanceID = 0
            if not categoryID:
                categoryID = 0
            if not mountID:
                mountID = 0
            if not classID:
                classID = 0

            if categoryID and nameID:
                cur.execute("delete FROM outfitting where StationID=? AND NameID=? AND Class=? AND MountID=? AND CategoryID=? AND Rating=? AND GuidanceID=? AND shipID=?",
                                                        (stationID, nameID, classID, mountID, categoryID, rating, guidanceID, shipID))
#                print(cur.rowcount)

                cur.execute("insert or ignore into outfitting (StationID, NameID, Class, MountID, CategoryID, Rating, GuidanceID, shipID, modifydate ) values (?, ?, ?, ?, ?, ?, ?, ?, ?) ",
                             (stationID, nameID, classID, mountID, categoryID, rating, guidanceID, shipID, timestamp))
            
        cur.close()
