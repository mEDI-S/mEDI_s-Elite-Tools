'''
Created on 29.07.2015

@author: mEDI

import or update data from http://eddb.io/archive/v3/stations.json
'''
import os

from datetime import datetime, date, time, timedelta
import json

import gzip
import io

try:
    import urllib2
except ImportError:
    import urllib.request as urllib2

class loader(object):
    '''
    classdocs
    '''
    mydb = None


    def __init__(self, mydb):
        '''
        Constructor
        '''
        self.mydb = mydb

    def importData(self, filename=None):
        print("import %s" % filename)

        fienameItems = "db/commodities.json"
        fienameSystems = "db/systems.json"
        utcOffeset =  datetime.now() - datetime.utcnow() 

        cur = self.mydb.cursor()
        
        fp = open(filename)
        josnData = json.load(fp)
        fp.close()

        if not josnData:
            return

        #build systemIDCache = translator cache
        fp = open(fienameSystems)
        stationJosnData = json.load(fp)
        fp.close()
        if not stationJosnData: return

        cur.execute( "select id, System from systems" )
        result = cur.fetchall()
        systemIDCache_DB= {}
        for system in result:
            systemIDCache_DB[system["System"].lower()] = system["id"]
        result= None

        systemJosmIDtoDBIDCache= {} # build josmID to dbID
        for system in stationJosnData:
            systemJosmIDtoDBIDCache[system["id"]] = systemIDCache_DB[ system["name"].lower() ]


        #build itemIDCach translator cache 
        fp = open(fienameItems)
        itemsJosnData = json.load(fp)
        fp.close()
        if not itemsJosnData: return

        cur.execute( "select id, name from items" )
        result = cur.fetchall()
        itemIDCache_DB= {}
        for system in result:
            itemIDCache_DB[ system["name"].lower() ] = system["id"]
        result= None

        itemJosmIDtoDBIDCache= {} # build josmID to dbID
        for item in itemsJosnData:
            itemJosmIDtoDBIDCache[item["id"]] = itemIDCache_DB[ item["name"].lower() ]


        # build stationCache
        cur.execute("select id, Station, SystemID, modified from stations")
        result = cur.fetchall()
        stationCache = {}
        for system in result:
            key = "%s_%s" % (system["SystemID"], system["Station"].lower())
            stationCache[key ] = [system["id"], system["modified"]]
        result = None



        # build itemPriceCache
        cur.execute( "select id, StationID, ItemID, modified from price" )
        result = cur.fetchall()
        itemPriceCache= {}

        for item in result:
            cacheKey = "%d_%d" % ( item["StationID"], item["ItemID"])
            itemPriceCache[cacheKey] = [item["id"], item["modified"]]
        result= None


        insertCount = 0
        insertItemCount = 0
        updateItemCount = 0
        itemCount = 0
        updateCount = 0
        totalCount = 0

        updateStation = []
        insertItems = []
        updateItems = []
        for station in josnData:
            totalCount += 1
            modified = datetime.fromtimestamp(station["updated_at"]) - utcOffeset
            #print(station["name"])

            systemID = systemJosmIDtoDBIDCache[station["system_id"]]
            stationCacheKey = "%s_%s" % (systemID, station["name"].lower() )
            '''
            update or insert Stations 
            '''
            if stationCacheKey not in stationCache:
                insertCount += 1

                cur.execute("insert or IGNORE into stations (SystemID, Station, StarDist, blackmarket, max_pad_size, market, shipyard, outfitting, rearm, refuel, repair, modified) values (?,?,?,?,?,?,?,?,?,?,?,?) ",
                    (systemID, station["name"], station["distance_to_star"], station["has_blackmarket"], station["max_landing_pad_size"], station["has_commodities"], station["has_shipyard"], station["has_outfitting"], station["has_rearm"], station["has_refuel"], station["has_repair"], modified))

                
                stationID = self.mydb.getStationID(systemID,station["name"])

            elif stationCache[stationCacheKey][1] < modified:
                updateCount += 1
                stationID = stationCache[stationCacheKey][0]
                updateStation.append( [station["name"], station["distance_to_star"], station["has_blackmarket"], station["max_landing_pad_size"], station["has_commodities"], station["has_shipyard"], station["has_outfitting"], station["has_rearm"], station["has_refuel"], station["has_repair"], modified, stationID] )
            else:
                stationID = stationCache[stationCacheKey][0]

            '''
            update or insert items 
            '''
            for item in station["listings"]:
                itemCount += 1

                modified = datetime.fromtimestamp(item["collected_at"]) - utcOffeset
                itemID = itemJosmIDtoDBIDCache[item["commodity_id"]]
                
                itemPriceCacheKey = "%d_%d" % (stationID, itemID)

                if itemPriceCacheKey not in itemPriceCache:
                    insertItemCount += 1

                    insertItems.append( [ systemID, stationID, itemID, item["sell_price"] , item["buy_price"], item["demand"], item["supply"], modified ] )

                elif itemPriceCache[itemPriceCacheKey][1] < modified:
                    updateItemCount += 1
                    
                    updateItems.append( [ item["sell_price"] , item["buy_price"], item["demand"], item["supply"], modified,  itemPriceCache[itemPriceCacheKey][0] ] ) 
                    


        if updateStation:
            cur.executemany("UPDATE stations SET Station=?, StarDist=?, blackmarket=?, max_pad_size=?, market=?, shipyard=?, outfitting=?, rearm=?, refuel=?, repair=?, modified=? where id = ?", updateStation)

        if insertItems:
            cur.executemany( "insert or IGNORE into price (SystemID, StationID, ItemID, StationBuy, StationSell, Dammand, Stock, modified, source) values (?,?,?,?,?,?,?,?,4) ", insertItems)
        self.mydb.con.commit()


        if updateItems:
            cur.executemany( "UPDATE price SET StationBuy=?, StationSell=?, Dammand=?, Stock=?, modified=?, source=4 where id = ?", updateItems)

            
            
        if updateCount or insertCount or insertItemCount or updateItemCount:
            print("update stations", updateCount, "insert stations", insertCount, "from", totalCount, "systems","insert items",insertItemCount,"update items",updateItemCount,"from items",itemCount)

        self.mydb.con.commit()
        cur.close()


    def filenameFromUrl(self, url):

        filename = url.split("/").pop()

        return filename
    
    def update(self):
        eddbUrl_systems = "http://eddb.io/archive/v3/stations.json"
        storageDir = "db"

        filename = self.filenameFromUrl(eddbUrl_systems)
        filename = os.path.join(storageDir, filename)

        if os.path.isfile(filename):

            cDate = datetime.fromtimestamp(os.path.getmtime(filename))

            if cDate < datetime.now() - timedelta(hours=24):
                self.updateFromUrl(filename, eddbUrl_systems)

        else:  # download file not exists
            self.updateFromUrl(filename, eddbUrl_systems)

        #self.importData(filename)
#        self.updateFromUrl(filename, eddbUrl_systems)

    def updateFromUrl(self, filename, url):
        if not url: return

        print("download %s" % url)

        request = urllib2.Request(url)
        request.add_header('Accept-encoding', 'gzip')
        response = urllib2.urlopen(request)
        if response.info().get('Content-Encoding') == 'gzip':
            # print("gzip ok")
            buf = io.BytesIO(response.read())
            f = gzip.GzipFile(fileobj=buf)
        else:
            # print("none")
            f = response

        wfp = open(filename, "wb")
        wfp.write(f.read())
        wfp.close()
            

        if response.info().get('content-type').split("; ")[0] == "application/json":
            pass
            self.importData(filename)
        else:
            print("download error?")
            print(response.info().items())
