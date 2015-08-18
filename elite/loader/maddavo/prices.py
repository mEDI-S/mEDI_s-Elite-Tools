'''
Created on 21.07.2015

@author: mEDI
'''
import re
from datetime import datetime, date, time, timedelta
#import urllib
import gzip
import io

try:
    import urllib2
except ImportError:
    import urllib.request as urllib2

# in python3 urllib.request
class loader(object):
    '''
    classdocs
    '''

    __dataCache = {}
    mydb = None

    def __init__(self, mydb=None):
        '''
        Constructor
        '''
        self.mydb = mydb

    def load(self,filename=None):
        if not filename: filename = "db/all_maddavo.prices"

        f = open(filename, 'r')
        #self.__dataCache = {}
        for line in f:
            line = line.strip()
            if len(line) == 0:
                continue
            elif "#" == line[0]:  # drop comment
                continue
            elif "+ " == line[0:2]:  # drop class/group
                continue
            elif "@ " == line[0:2]:  # get system/stations name
        #        name = line[2:]
                ma = re.search("@ (.*)/(.*)", line)
                if ma:
                    systemName = ma.group(1).lower()
                    stationName = ma.group(2).lower()
                else:
                    print("loading error system/stationname")
                #print(line , ma.group(1))
                continue
            else:
                ma = re.search("^(.+?)\s+(\d+)\s+(\d+)\s+(\d+.|\?|-)\s+(\d+.|-|\?)\s+(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s*.*", line)
                if ma:
                    pass
                    #####################
                    # Group:
                    #    1. name
                    #    2. station buy price
                    #    3. station sell price
                    #    4. Dammand
                    #    5. Stock
                    #    6. datetime
                    #####################
                    #print(ma.group(1),ma.group(2),ma.group(3),ma.group(4),ma.group(5),ma.group(6))
                    itemName= ma.group(1).lower()
                    if not self.__dataCache.get(systemName) : self.__dataCache[systemName] = {}
                    if not self.__dataCache[systemName].get(stationName) : self.__dataCache[systemName][stationName] = {}
                    if not self.__dataCache[systemName][stationName].get(itemName) : self.__dataCache[systemName][stationName][itemName] = []
        
                    # erstmal nur das rein was ich brauche die tage
                    ##########
                    # struktur: self.__dataCache{}->systemName{}->stationName{}->itemName{}->[station_buy, station_sell, Dammand, Stock, modifydate]
                    ########
                    Dammand = 0
                    if ma.group(4):
                        res = re.findall(r'\d+', ma.group(4))
                        if res: 
                            Dammand = int( res[0] )
                    Stock = 0
                    if ma.group(5):
                        res = re.findall(r'\d+', ma.group(5))
                        if res:
                            Stock = int( res[0] )
                    modifydate = None
                    if ma.group(6):
                        modifydate = datetime.strptime(ma.group(6),"%Y-%m-%d %H:%M:%S")
                        
                    self.__dataCache[systemName][stationName][itemName] = [ int(ma.group(2)) , int(ma.group(3)), Dammand, Stock, modifydate ]
                else:
                    pass
                    print("loading error: parsing '%s'" % line)
        
        #print(self.__dataCache)
        #print(self.__dataCache["CEMIESS".lower()]["Shoemaker City".lower()]["CONSUMER TECHNOLOGY".lower()] )
    def importData(self):

        if len(self.__dataCache) == 0: self.load()

        cur = self.mydb.cursor()

        #get all items and build a cache (extrem faster as single querys) 
        cur.execute( "select SystemID, StationID, ItemID, modified from price" )
        result = cur.fetchall()
        itemCache= {}

        for item in result:
            cacheKey = "%d_%d_%d" % (item["SystemID"], item["StationID"], item["ItemID"])
            itemCache[cacheKey] = item["modified"]
        result= None

        updateItems = []

        for system in self.__dataCache:

            systemID = self.mydb.getSystemIDbyName(system)
            if systemID == None:
                print("new system?",system)
            for station in self.__dataCache[system]:

                stationID = self.mydb.getStationID(systemID, station)
                if stationID == None:
                    print("new station?",stationID)

                for item in self.__dataCache[system][station]:

                    itemID = self.mydb.getItemID(item)
                    cacheKey = "%d_%d_%d" % (systemID, stationID, itemID)

                    if not itemCache.get(cacheKey):
#                        print(cacheKey,systemID, stationID, itemID,item)
                        cur.execute( "insert or IGNORE into price (SystemID, StationID, ItemID, StationBuy, StationSell, Dammand,Stock, modified, source) values (?,?,?,?,?,?,?,?,1) ",
                            ( systemID, stationID, itemID, self.__dataCache[system][station][item][0],self.__dataCache[system][station][item][1],self.__dataCache[system][station][item][2],self.__dataCache[system][station][item][3], self.__dataCache[system][station][item][4]) )

                    elif itemCache[cacheKey] < self.__dataCache[system][station][item][4]:
                        #print("update", cacheKey)
                        updateItems.append( [self.__dataCache[system][station][item][0],self.__dataCache[system][station][item][1],self.__dataCache[system][station][item][2],self.__dataCache[system][station][item][3], self.__dataCache[system][station][item][4], systemID, stationID, itemID ] )

        
        if updateItems:
            #print(updateItems)
            cur.executemany( "UPDATE price SET  StationBuy=?, StationSell=?, Dammand=?, Stock=?, modified=? ,source=1 where SystemID == ? AND StationID == ? AND ItemID == ?",updateItems)

        self.mydb.con.commit()
        cur.close()
        self.cleanCache()

    def update(self):
        url_fullData = "http://www.davek.com.au/td/prices.asp"
        url_twoDayData = "http://www.davek.com.au/td/prices-2d.asp"
        url_threeHorsData = "http://www.davek.com.au/td/prices-3h.asp"
        
        print("update from maddavo")
        lastUpdateTime = self.mydb.getConfig( 'lastMaddavoDownload' )
        #lastUpdateTime = "2015-07-23 14:29:27"
        currentUpdateTime = None
        if lastUpdateTime:
            lastUpdateTime = datetime.strptime(lastUpdateTime , "%Y-%m-%d %H:%M:%S")

            if lastUpdateTime < datetime.now() - timedelta(days=2):
                print("download full")
#                currentUpdateTime = datetime.now() - timedelta(hours=3)
                currentUpdateTime = datetime.now()
                self.updateFromUrl(url_fullData)
                self.updateFromUrl(url_twoDayData)
                self.updateFromUrl(url_threeHorsData)

            elif lastUpdateTime < datetime.now() - timedelta(hours=3):
                print("download 2d")
#                currentUpdateTime = datetime.now() - timedelta(hours=1)
                currentUpdateTime = datetime.now()
                self.updateFromUrl(url_twoDayData)
                self.updateFromUrl(url_threeHorsData)
            elif lastUpdateTime < datetime.now() - timedelta(minutes=60):
                print("download 3h")
                currentUpdateTime = datetime.now()
                self.updateFromUrl(url_threeHorsData)
            else:
                print("download noting")

        else:
            print("download full fallback")
#            currentUpdateTime = datetime.now() - timedelta(hours=3)
            currentUpdateTime = datetime.now()
            self.updateFromUrl(url_fullData)
            self.updateFromUrl(url_twoDayData)
            self.updateFromUrl(url_threeHorsData)

        if currentUpdateTime:
            self.mydb.setConfig( 'lastMaddavoDownload', currentUpdateTime.strftime("%Y-%m-%d %H:%M:%S") )





    def updateFromUrl(self,url):
        if not url: return
        tempFile = "db/tmp.price"
        filename = tempFile
        print("download %s" % url)

        request = urllib2.Request(url)
        request.add_header('Accept-encoding', 'gzip')
        response = urllib2.urlopen(request)
        if response.info().get('Content-Encoding') == 'gzip':
            #print("gzip ok")
            buf = io.BytesIO(response.read())
            f = gzip.GzipFile(fileobj=buf)
        else:
            #print("none")
            f = response

        wfp = open(filename,"wb")
        wfp.write(f.read())
        wfp.close()

        
#        file,http = urllib.urlretrieve(url, tempFile)
#        if http["Content-Type"] == "application/tradedangerous":
        if response.info().get('content-type').split("; ")[0] == "application/tradedangerous":
            self.load(tempFile)
            self.importData()
        else:
            print("download error?")
            print(response.info().items())

        
        #urllib.urlretrieve()
    def cleanCache(self):
        self.__dataCache = {}
        
    def getBuyPrice(self,system,station,item):
        '''
        return price u can buy the item
        '''
        if len(self.__dataCache) == 0: self.load()

        system = system.lower()
        station = station.lower()
        item = item.lower()
        if self.__dataCache.has_key(system) and self.__dataCache[system].has_key(station) and self.__dataCache[system][station].has_key(item):
            return self.__dataCache[system][station][item][1]
        else:
            return None
    def getSellPrice(self,system,station,item):
        '''
        return price u can sell item to station
        '''
        if len(self.__dataCache) == 0: self.load()

        system = system.lower()
        station = station.lower()
        item = item.lower()
        if self.__dataCache.has_key(system) and self.__dataCache[system].has_key(station) and self.__dataCache[system][station].has_key(item):
            return self.__dataCache[system][station][item][0]
        else:
            return None
    def getItemsFromStation(self, system, station):
        if len(self.__dataCache) == 0: self.load()

        system = system.lower()
        station = station.lower()

        #if self.__dataCache.has_key(system) and self.__dataCache[system].has_key(station):
        return self.__dataCache[system].get(station)
        #else:
        #    return None