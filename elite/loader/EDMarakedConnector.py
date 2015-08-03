'''
Created on 24.07.2015

@author: mEDI
'''
import os, sys, time
from stat import S_ISREG, ST_CTIME, ST_MODE
import re
import csv
from datetime import datetime, date,  timedelta

class loader(object):
    '''
    classdocs
    '''
    mydb = None
    __itemCache = None


    def __init__(self, mydb):
        '''
        Constructor
        '''
        self.mydb = mydb


    def createPriceKeyCache(self):
        '''
        build key cache
        '''
        if self.__itemCache: return
        print("create cache")
        self.__itemCache = {}
        #get all items and build a cache (extrem faster as single querys) 
        mycur = self.mydb.cursor()
        mycur.execute( "select id, StationID, ItemID, modified from price" )
        result = mycur.fetchall()

        for item in result:
            cacheKey = "%d_%d" % (item["StationID"], item["ItemID"])
            self.__itemCache[cacheKey] = [item["id"], item["modified"]]
        result= None

    def cleanCache(self):
        self.__itemCache = None

    def importData(self, filename=None):
        if not filename: filename = 'db/LTT 9810.Friedrich Peters Vision.2015-07-21T23.05.20.csv'
        
        with open(filename ,"rb") as csvfile:
            simpelreader = csv.reader(csvfile, dialect='excel',delimiter=';',quoting=csv.QUOTE_NONE)

            cur = self.mydb.cursor()
            mylist = list(simpelreader)
            fields = mylist[0]
            #print(fields)

            self.createPriceKeyCache()

            insertStations = []
            updateStations = []
            updateItems = []
            insertCount = 0
            updateCount = 0
            for row in mylist[1:]:
                #print(len(row), row)
                system = row[fields.index("System")].lower()
                station = row[fields.index("Station")].lower()
                item = row[fields.index("Commodity")].lower()
                StationSell = 0
                if row[fields.index("Buy")].isdigit(): StationSell = int(row[fields.index("Buy")])
                StationBuy = 0
                if row[fields.index("Sell")].isdigit() : StationBuy = int(row[fields.index("Sell")])
                Demand = 0
                if row[fields.index("Demand")].isdigit(): Demand = int(row[fields.index("Demand")])
                Stock = 0
                if row[fields.index("Supply")].isdigit() : Stock = int(row[fields.index("Supply")])
                modifydate = datetime.strptime(row[fields.index("Date")].lower(), "%Y-%m-%dT%H:%M:%SZ")

                systemID = self.mydb.getSystemIDbyName(system)

                # add new systems
                if not systemID:
                    print("add new system: %s" % system)
                    cur.execute("insert or IGNORE into systems (System) values (?) ",
                                                               (row[fields.index("System")],))

                    systemID = self.mydb.getSystemIDbyName(system)

                stationID = self.mydb.getStationID(systemID, row[fields.index("Station")])
                # add new stations
                if not stationID:
                    print("add new station: %s" % system)
                    cur.execute("insert or IGNORE into station (SystemID, Station) values (?) ",
                                                               (systemID, row[fields.index("Station")]))

                    stationID = self.mydb.getStationID(systemID, row[fields.index("Station")])

                itemID = self.mydb.getItemID(row[fields.index("Commodity")])
                # add new item    
                if not itemID:
                    print("add new item : %s" % row[fields.index("Commodity")])
                    cur.execute("insert or IGNORE into items (name) values (?) ",
                                                               (row[fields.index("Commodity")]))
                
                    itemID = self.mydb.getItemID(row[fields.index("Commodity")])

                #print( systemID, stationID, itemID, StationBuy, StationSell  , Demand , Stock, modifydate )
                '''
                main import
                '''
                cacheKey = "%d_%d" % (stationID, itemID)

                if cacheKey not in  self.__itemCache:
                    insertCount += 1
                    print("insert")
                    #add new price
                    cur.execute( "insert or IGNORE into price (SystemID, StationID, ItemID, StationBuy, StationSell, Dammand,Stock, modified, source) values (?,?,?,?,?,?,?,?,3) ",
                        ( systemID, stationID, itemID, StationBuy, StationSell  , Demand , Stock, modifydate) )
                
                elif self.__itemCache[cacheKey][1] < modifydate:
                    # update price
                    updateCount +=1
                    self.__itemCache[cacheKey][1] = modifydate
                    #print("update")
                    updateItems.append( [StationBuy, StationSell  , Demand , Stock, modifydate, self.__itemCache[cacheKey][0] ] )
                    
            if updateItems:
                cur.executemany( "UPDATE price SET  StationBuy=?, StationSell=?,  Dammand=?,Stock=?, modified=? ,source=3 where id = ?", updateItems)

            if insertCount or updateCount:
                print("insert", insertCount,"update", updateCount)

            self.mydb.con.commit()

        cur.close()

    def update(self):
        lastUpdateTime = self.mydb.getConfig( 'lastEDMarkedConnectorUpdate' )
        cvsDir = self.mydb.getConfig( 'EDMarkedConnector_cvsDir' )
        #lastUpdateTime = "2015-07-23 14:29:27"
        currentUpdateTime = None
        newstEntry = None
        if lastUpdateTime:
            lastUpdateTime = datetime.strptime(lastUpdateTime , "%Y-%m-%d %H:%M:%S")
        else:
            lastUpdateTime =  datetime.now() - timedelta(days=14)


        for f in os.listdir(cvsDir):
            f =  os.path.join(cvsDir, f)
            if os.path.isfile(f) and len(f) > 4 and re.match(r".*\d{4}-\d{2}-\d{2}T\d{2}.\d{2}.\d{2}\.csv$" ,f):
                cDate = datetime.fromtimestamp(os.path.getmtime(f))
                if cDate > lastUpdateTime:
                    if not newstEntry or cDate > newstEntry:
                        newstEntry = cDate 
                    print("import: %s" % f)
                    self.importData(f)

        if newstEntry:
            newstEntry = newstEntry + timedelta(seconds=1)
            self.mydb.setConfig( 'lastEDMarkedConnectorUpdate', newstEntry.strftime("%Y-%m-%d %H:%M:%S") )

        self.cleanCache()