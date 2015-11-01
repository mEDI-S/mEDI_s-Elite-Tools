# -*- coding: UTF8
'''
Created on 29.10.2015

@author: mEDI

https://eddb.io/api
loader for api V4
'''


import json
from datetime import datetime
import gzip
import io
import sys
import traceback
import elite


try:
    from _version import __buildid__, __version__, __builddate__, __toolname__, __useragent__
except ImportError:
    __buildid__ = "UNKNOWN"
    __version__ = "UNKNOWN"
    __builddate__ = "NONE"
    __toolname__ = "mEDI s Elite Tools"
    __useragent__ = '%s/%s (%s) %s(%s)' % (__toolname__.replace(" ", ""), __version__, sys.platform, __buildid__, __builddate__.replace(" ", "").replace("-", "").replace(":", ""))

try:
    ''' python 2.7'''
    import urllib2
except ImportError:
    ''' python 3.x'''
    import urllib.request as urllib2


_ships_ = {"Adder": 'Adder',
           "Asp Explorer": 'Asp',
           "Hauler": 'Hauler',
           "Diamondback Scout": 'Diamondback Scout',
           "Federal Dropship": 'Federal Dropship',
           "Orca": 'Orca',
           "Federal Gunship": 'Federal Gunship',
           "Diamondback Explorer": 'Diamondback Explorer',
           "Viper Mk III": 'Viper',
           "Imperial Clipper": 'Imperial Clipper',
           "Imperial Courier": 'Imperial Courier',
           "Vulture": 'Vulture',
           "Anaconda": 'Anaconda',
           "Sidewinder Mk. I": 'Sidewinder',
           "Federal Assault Ship": 'Federal Assault Ship',
           "Imperial Eagle": 'Imperial Eagle',
           "Cobra Mk. III": 'Cobra Mk III',
           "Type-9 Heavy": 'Type-9 Heavy',
           "Fer-de-Lance": 'Fer-de-Lance',
           "Type-7 Transporter": 'Type-7 Transporter',
           "Type-6 Transporter": 'Type-6 Transporter',
           "Python": 'Python',
           "Eagle Mk. II": 'Eagle'}

_category_ = {"Utility Mount": 'utility',
              'Internal Compartment': 'internal',
              'Essential Equipment': 'standard',
              'Weapon Hardpoint': 'hardpoint',
              'Bulkhead': None }

_mount_ = {'Fixed': 'Fixed', 'Gimbal': 'Gimballed', 'Turret': 'Turreted'}

_guidance_ = {32: 'Seeker', 16: 'Dumbfire' }

_powerState_ = {'Control': 1, 'Exploited': 2, 'Expansion': 3}


class loader(object):

    translateCommodities = {}
    translateSystemID = {}
    translateStationID = {}
    translatorShipsID = {}
    translatorModulID = {}
    forceImport = None
    
    def __init__(self, mydb):
        self.mydb = mydb

        self.outfitting = elite.outfitting(self.mydb)
        self.utcOffeset = datetime.now() - datetime.utcnow()


    def importData(self, forceImport=None):

        self.forceImport = forceImport

        commodities = self.downloadJson("https://eddb.io/archive/v4/commodities.json")
        if not commodities:
            print("download error: commodities")
            return

        self.importCommodities(commodities)




        modules = self.downloadJson("https://eddb.io/archive/v4/modules.json")
        if not modules:
            print("download error: modules")
            return

        systems = self.downloadJson("https://eddb.io/archive/v4/systems.json")
        if not systems:
            print("download error: systems")
            return

        self.importSystems(systems)


        stations = self.downloadJson("https://eddb.io/archive/v4/stations.json")
        if not stations:
            print("download error: stations")
            return
        self.importStations(stations)
        self.importOutfitting(stations, modules)
        self.importShipyard(stations)

        priceListRaw = self.downloadFile('https://eddb.io/archive/v4/listings.csv')
        if not priceListRaw:
            print("download error: priceList")
            return

        self.importPrice(priceListRaw)



    def importPrice(self, priceListRaw):
        if not priceListRaw:
            return
        
        cur = self.mydb.cursor()

        # build itemPriceCache
        cur.execute("select id, StationID, ItemID, modified from price")
        result = cur.fetchall()
        itemPriceCache = {}

        for item in result:
            cacheKey = "%d_%d" % (item["StationID"], item["ItemID"])
            itemPriceCache[cacheKey] = [item["id"], item["modified"]]
        result = None

        insertItemCount = 0
        insertItems = []
        updateItemCount = 0
        updateItems = []

        for i, rawPrice in enumerate( priceListRaw.decode('utf-8').split("\n")):
            if i <= 0:
                continue
            if not rawPrice.strip():
                continue

            #id,station_id,commodity_id,supply,buy_price,sell_price,demand,collected_at,update_count
            price = rawPrice.split(",")
            stationID = self.translateStationID[int(price[1])]
            itemID = self.translateCommodities[int(price[2])]
            stock = price[3]

            stationSell = price[4]
            stationBuy = price[5]
            demand = price[6]
            modified = datetime.fromtimestamp(int(price[7])) - self.utcOffeset


            itemPriceCacheKey = "%d_%d" % (stationID, itemID)

            if itemPriceCacheKey not in itemPriceCache:
                insertItemCount += 1
                stationData = self.mydb.getStationData(stationID)
                insertItems.append([ stationData['SystemID'], stationID, itemID, stationBuy, stationSell, demand, stock, modified ])

            elif itemPriceCache[itemPriceCacheKey][1] < modified:
                updateItemCount += 1
                
                updateItems.append([ stationBuy, stationSell, demand, stock, modified, itemPriceCache[ itemPriceCacheKey][0] ])
                

        if insertItems:
            cur.executemany("insert or IGNORE into price (SystemID, StationID, ItemID, StationBuy, StationSell, Dammand, Stock, modified, source) values (?, ?, ?, ?, ?, ?, ?, ?, 4) ", insertItems)


        if updateItems:
            cur.executemany("UPDATE price SET StationBuy=?, StationSell=?, Dammand=?, Stock=?, modified=?, source=4 where id = ?", updateItems)

            
            
        if insertItemCount or updateItemCount:
            print("insert items", insertItemCount, "update items", updateItemCount, "total items", i)

        self.mydb.con.commit()
        cur.close()

            


    def importShipyard(self, stationsData):
        if not stationsData:
            return
    
        insertList = []

        cur = self.mydb.cursor()

        if not self.translatorShipsID:
            for ship in _ships_:
                self.translatorShipsID[ship] = self.mydb.getShipID(_ships_[ship], True)

        for station in stationsData:
            modified = datetime.fromtimestamp(station["updated_at"]) - self.utcOffeset
            stationID = self.translateStationID[int(station["id"])]
            if not stationID:
                print("bug stationID", station["id"], "not found")
                continue
            if 'selling_ships' not in station or not station['selling_ships']:
                continue

            updateORInsert = None

            for ship in station['selling_ships']:
                shipID = self.translatorShipsID[ship]

                if shipID:

                    if not updateORInsert:
                        
                        cur.execute("select modifydate FROM shipyard where StationID=? limit 1",
                                                        (stationID,))
                        result = cur.fetchone()
                        if not result:
                            updateORInsert = 1
                        elif result and result['modifydate'] < modified:
                            cur.execute("delete from shipyard where StationID=?", (stationID,))
                            updateORInsert = 1
                        else:
                            updateORInsert = 2

                    if updateORInsert == 1:
                        systemID = self.translateSystemID[station["system_id"]]
                        insertList.append([systemID, stationID, shipID, modified])

        if insertList:
            cur.executemany("insert  into shipyard (SystemID, StationID, ShipID, modifydate ) values (?, ?, ?, ?) ", insertList)
            self.mydb.con.commit()
        cur.close()



    def importOutfitting(self, stationsData, modules):
        if not stationsData:
            return
    
        insertList = []

        cur = self.mydb.cursor()
        modulesPointer = {}


        for ship in _ships_:
            self.translatorShipsID[ship] = self.mydb.getShipID(_ships_[ship], True)

        for modul in modules:
            modulesPointer[int(modul['id'])] = modul

            shipID = 0
            if 'ship' in modul and modul['ship']:
                shipID = self.translatorShipsID[modul['ship']]

            nameID = self.outfitting.getOutfittingNameID(modul['group']['name'], True)

            mountID = 0
            if 'weapon_mode' in modul and modul['weapon_mode']:
                mount = _mount_[modul['weapon_mode']]
                mountID = self.outfitting.getOutfittingMountID(mount, True)


            if modul['group']['category'] not in _category_:
                print(modul['group']['category'])

            category = _category_[ modul['group']['category'] ]
            categoryID = 0
            if category:
                categoryID = self.outfitting.getOutfittingCategoryID( category, True)

            rating = modul['rating']

           
            guidanceID = 0
            if 'missile_type' in modul and modul['missile_type']:
                guidance = _guidance_[ modul['missile_type'] ]
                guidanceID = self.outfitting.getOutfittingGuidanceID(guidance, True)

            classID = modul['class']


            modulID = self.outfitting.getOutfittingModulID(nameID, classID, mountID, categoryID, rating, guidanceID, shipID, True)
            self.translatorModulID[int(modul['id'])] = modulID


        for station in stationsData:
            modified = datetime.fromtimestamp(station["updated_at"]) - self.utcOffeset
            stationID = self.translateStationID[int(station["id"])]
            if not stationID:
                print("bug stationID", station["id"], "not found")
                continue
            if 'selling_modules' not in station or not station['selling_modules']:
                continue

            updateORInsert = None
            for modulID in station['selling_modules']:
                modulID = self.translatorModulID[int(modulID)]

                if modulID:

                    if not updateORInsert:
                        
                        cur.execute("select modifydate FROM outfitting where StationID=? limit 1",
                                                        (stationID,))
                        result = cur.fetchone()
                        if not result:
                            updateORInsert = 1
                        elif result and result['modifydate'] < modified:
                            cur.execute("delete from outfitting where StationID=?", (stationID,))
                            updateORInsert = 1
                        else:
                            updateORInsert = 2

                    if updateORInsert == 1:
                        insertList.append([stationID, modulID, modified])

        if insertList:
            cur.executemany("insert or ignore into outfitting (StationID, modulID, modifydate ) values (?, ?, ?) ", insertList)

            self.mydb.con.commit()
        cur.close()



    def importStations(self, jsonData):
        if not jsonData:
            return
    
        cur = self.mydb.cursor()


        # build stationCache
        cur.execute("select id, Station, SystemID, modified from stations")
        result = cur.fetchall()
        stationCache = {}
        for stations in result:
            key = "%s_%s" % (stations["SystemID"], stations["Station"].lower())
            stationCache[key] = [stations["id"], stations["modified"]]
        result = None


        insertCount = 0
        updateCount = 0
        totalCount = 0

        updateStation = []
        for station in jsonData:
            totalCount += 1
            modified = datetime.fromtimestamp(station["updated_at"]) - self.utcOffeset
            systemID = None
            stationID = None
            if station["system_id"] in self.translateSystemID:
                systemID = self.translateSystemID[station["system_id"]]
            else:
                print("bug in eddb Stations:system_id %s" % station["system_id"])
                continue  # this dataset is buged, drop it
            
            stationCacheKey = "%s_%s" % (systemID, station["name"].lower())

            allegianceID = self.mydb.getAllegianceID(station["allegiance"], True)

            governmentID = self.mydb.getGovernmentID(station["government"], True)

            if stationCacheKey in stationCache:
                stationID = stationCache[stationCacheKey][0]
                self.translateStationID[int(station["id"])] = stationID

            '''
            update or insert Stations
            '''
            if not stationID:
                insertCount += 1

                cur.execute("insert or IGNORE into stations (SystemID, Station, StarDist, government, allegiance, blackmarket, max_pad_size, market, shipyard, outfitting, rearm, refuel, repair, modified) values (?,?,?,?,?,?,?,?,?,?,?,?,?,?) ",
                    (systemID, station["name"], station["distance_to_star"], governmentID, allegianceID, station["has_blackmarket"], station["max_landing_pad_size"], station["has_commodities"], station["has_shipyard"], station["has_outfitting"], station["has_rearm"], station["has_refuel"], station["has_repair"], modified))

                stationID = self.mydb.getStationID(systemID, station["name"])
                self.translateStationID[int(station["id"])] = stationID

            elif stationCache[stationCacheKey][1] < modified or self.forceImport:
                updateCount += 1
                updateStation.append([station["name"], station["distance_to_star"], governmentID, allegianceID, station["has_blackmarket"], station["max_landing_pad_size"], station["has_commodities"], station["has_shipyard"], station["has_outfitting"], station["has_rearm"], station["has_refuel"], station["has_repair"], modified, stationID])


        if updateStation:
            cur.executemany("UPDATE stations SET Station=?, StarDist=?, government=?, allegiance=?, blackmarket=?, max_pad_size=?, market=?, shipyard=?, outfitting=?, rearm=?, refuel=?, repair=?, modified=? where id = ?", updateStation)

            
            
        if updateCount or insertCount:
            print("update stations:", updateCount, "insert stations:", insertCount, "from total:", totalCount)

        self.mydb.con.commit()
        cur.close()



    def importSystems(self, jsonData):
        if not jsonData:
            return
    
        cur = self.mydb.cursor()

        # build systemCache
        cur.execute("select id, System, modified from systems")
        result = cur.fetchall()
        systemCache = {}
        for system in result:
            systemCache[ system["System"].lower() ] = [system["id"], system["modified"]]
        result = None

        insertCount = 0
        updateCount = 0
        totalCount = 0
        updateSystem = []
        for system in jsonData:
            totalCount += 1
            modified = datetime.fromtimestamp(system["updated_at"]) - self.utcOffeset


            powerID = None
            powerState = None
            if system["power"]:
                powerID = self.mydb.getPowerID(system["power"], True)
                powerState = _powerState_.get(system["power_state"])
                if not powerState:
                    print(system["power_state"])
            #power_state

            allegianceID = self.mydb.getAllegianceID(system["allegiance"], True)

            governmentID = self.mydb.getGovernmentID(system["government"], True)


            if system["name"].lower() not in systemCache:
                insertCount += 1
                cur.execute("insert or IGNORE into systems (System, posX, posY, posZ, permit, power_control, power_state, government, allegiance, modified) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ",
                                        (system["name"], float(system["x"]), float(system["y"]), float(system["z"]), system["needs_permit"], powerID, powerState, governmentID, allegianceID, modified))

            elif system["name"].lower() in systemCache and (not systemCache[ system["name"].lower() ][1] or systemCache[ system["name"].lower() ][1] < modified or self.forceImport):
                updateCount += 1
                updateSystem.append([system["name"], float(system["x"]), float(system["y"]), float(system["z"]), system["needs_permit"], powerID, powerState, governmentID, allegianceID, modified, systemCache[ system["name"].lower() ][0] ])

            ''' fill translator cache '''
            if system["name"].lower() in systemCache:
                self.translateSystemID[system["id"]] = systemCache[ system["name"].lower() ][0]
            else:
                self.translateSystemID[system["id"]] = self.mydb.getSystemIDbyName(system["name"])
                
        if updateSystem:
            cur.executemany("update systems SET System=?, posX=?, posY=?, posZ=?, permit=?, power_control=?, power_state=?, government=?, allegiance=?, modified=? where id=?", updateSystem)

        if updateCount or insertCount:
            print("update", updateCount, "insert", insertCount, "from", totalCount, "systems")

        self.mydb.con.commit()
        cur.close()



    def importCommodities(self, jsonData):

        if not jsonData:
            return

        cur = self.mydb.cursor()

        for item in jsonData:

            itemID = self.mydb.getItemID(item["name"])
            averagePrice = item["average_price"]
            self.translateCommodities[ int(item["id"]) ] = itemID

            if not itemID:
                print("insert new item %s" % item["name"])

                category = item["category"]["name"]
                if category == "Unknown":
                    category = None

                cur.execute("insert or IGNORE into items (name, category, average_price ) values (?, ?, ?) ",
                                                            (item["name"], category, averagePrice))


            else:
                ''' update average price '''
                cur.execute("UPDATE items SET average_price=? where id=? ", (averagePrice, itemID))

        self.mydb.con.commit()
        cur.close()




    def downloadJson(self, url):
        print("download %s" % url)

        request = urllib2.Request(url)
        request.add_header('User-Agent', __useragent__)

        request.add_header('Accept-encoding', 'gzip')

        try:
            response = urllib2.urlopen(request)
        except:
            traceback.print_exc()
            return
        
        if response.info().get('Content-Encoding') == 'gzip':
            buf = io.BytesIO(response.read())
            f = gzip.GzipFile(fileobj=buf)
        else:
            f = response
        
        result = f.read()

        if result:
            try:
                josnData = json.loads(result.decode('utf-8'))
            except:
                traceback.print_exc()
                return

            return josnData


    def downloadFile(self, url):
        print("download %s" % url)

        request = urllib2.Request(url)
        request.add_header('User-Agent', __useragent__)

        request.add_header('Accept-encoding', 'gzip')

        try:
            response = urllib2.urlopen(request)
        except:
            traceback.print_exc()
            return
        
        if response.info().get('Content-Encoding') == 'gzip':
            buf = io.BytesIO(response.read())
            f = gzip.GzipFile(fileobj=buf)
        else:
            f = response
        
        result = f.read()

        if result:
            return result
