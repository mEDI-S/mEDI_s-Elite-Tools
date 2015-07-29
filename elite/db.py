# -*- coding: UTF8
'''
Created on 23.07.2015

@author: mEDI


speedup: http://codereview.stackexchange.com/questions/26822/myth-busting-sqlite3-performance-w-pysqlite
'''
import sqlite3
import os

import elite.loader.maddavo as maddavo_loader
import elite.loader.bpc as bpc_loader
import elite.loader.EDMarakedConnector as EDMarakedConnector_loader
import elite.loader.eddb as eddb_loader

import sqlite3_functions

DBPATH = os.path.join("db","my.db")
DBVERSION = 1

class db(object):
    '''
    classdocs
    '''
    path = None
    con = None
    __stationIDCache = {}
    __systemIDCache = {}
    __itemIDCache = {}

    def __init__(self):
        '''
        Constructor
        '''
        if self.con is not None:
            return

        new_db = None
        if not os.path.isfile(DBPATH):
            print("new db")
            new_db = True
        self.con = sqlite3.connect(DBPATH, detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
        self.con.row_factory = sqlite3.Row    

        sqlite3_functions.registerSQLiteFunktions(self.con)

        if new_db:
            self.initNewDB()
            self.importData()
        #else:
            # test import
        #self.initNewDB()
        self.fillCache()
            #self.importData()
            
        dbVersion = self.getConfig( 'dbVersion' )
        if dbVersion == False:
            print(dbVersion)
            print("version false db")
            self.initNewDB()

        self.updateData()
        
    def cleanCache(self):
        '''
        clean all caches
        '''
        self.__stationIDCache = {}
        self.__systemIDCache = {}
        self.__itemIDCache = {}

    def fillCache(self):
        '''
        fill the id cache for faster imports and updates
        '''
        cur = self.cursor()

        cur.execute( "select id, SystemID, Station from stations" )
        result = cur.fetchall()
        for station in result:
            key = "%d_%s" % (station["SystemID"],station["Station"]) 
            self.__stationIDCache[key] = station["id"]

        cur.execute( "select id, System from systems" )
        result = cur.fetchall()
        for system in result:
            self.__systemIDCache[system["System"] ] = system["id"]

        cur.close()
        
    def importData(self):
        print("import data")

        maddavo_sysl = maddavo_loader.system.loader(self)
        maddavo_sysl.importData(None)

        maddavo_stationl = maddavo_loader.station.loader(self)
        maddavo_stationl.importData(None)

        maddavo_item = maddavo_loader.items.loader(self)
        maddavo_item.importData(None)

        maddavo_prices = maddavo_loader.prices.loader(self)
        maddavo_prices.importData()

    def updateData(self):
        '''
        update price date from all sources
        '''        
        print("update data")
        
        eddb_commodities = eddb_loader.items.loader(self)
        eddb_commodities.update()

        eddb_systems = eddb_loader.systems.loader(self)
        eddb_systems.update()
        return
        edMarked =  EDMarakedConnector_loader.loader(self)
        edMarked.update()

        maddavo_prices = maddavo_loader.prices.loader(self)
        maddavo_prices.update()

        myBPCloader = bpc_loader.prices.loader(self)
        myBPCloader.importData()

        
    def initNewDB(self):
        print("create new db")
        '''
        create tables
        '''
        self.con.execute( "CREATE TABLE IF NOT EXISTS config(var TEXT,val)" )
        self.con.execute( "create UNIQUE index  IF NOT EXISTS config_unique_var on config (var)" )


        #systems
        self.con.execute( "CREATE TABLE IF NOT EXISTS systems (id INTEGER PRIMARY KEY AUTOINCREMENT, System TEXT COLLATE NOCASE UNIQUE , posX FLOAT, posY FLOAT, posZ FLOAT, permit BOOLEAN, modified timestamp)" )
#        self.con.execute( "create UNIQUE index  IF NOT EXISTS systems_unique_System on systems (System)" )

        #stations
        self.con.execute( "CREATE TABLE IF NOT EXISTS stations (id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE, SystemID INT NOT NULL, Station TEXT COLLATE NOCASE, StarDist INT, blackmarket BOOLEAN, max_pad_size CHARACTER, market BOOLEAN, shipyard BOOLEAN,outfitting BOOLEAN,rearm BOOLEAN,refuel BOOLEAN,repair BOOLEAN, modified timestamp)" )
        self.con.execute( "create UNIQUE index  IF NOT EXISTS station_unique_system_Station on stations (SystemID, Station)" )

        #items
        self.con.execute( "CREATE TABLE IF NOT EXISTS items (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT COLLATE NOCASE UNIQUE, category TEXT COLLATE NOCASE, ui_sort TINYINT )" )

        #price
        self.con.execute( "CREATE TABLE IF NOT EXISTS price (SystemID INT NOT NULL, StationID INT NOT NULL, ItemID INT NOT NULL, StationSell INT NOT NULL DEFAULT 0, StationBuy INT NOT NULL DEFAULT 0, Dammand INT NOT NULL DEFAULT 0, Stock INT NOT NULL DEFAULT 0, modified timestamp, source INT NOT NULL)" )
        self.con.execute( "create UNIQUE index  IF NOT EXISTS price_unique_System_Station_Item on price (SystemID,StationID,ItemID)" )
        self.con.execute( "create index  IF NOT EXISTS price_modified on price (modified)" )

        #det default config
        self.con.execute( "insert or ignore into config(var,val) values (?,?)", ( "dbVersion", DBVERSION ) )
        self.con.execute( "insert or ignore into config(var,val) values (?,?)", ( "EDMarkedConnector_cvsDir", 'c:\Users\mEDI\Documents\ED' ) )
        
        self.con.commit()

    def cursor( self ):
        cur = self.con.cursor()
        #cur.execute("PRAGMA synchronous = OFF")
        #cur.execute("PRAGMA journal_mode = MEMORY")
        #cur.execute("PRAGMA journal_mode = OFF")
        return cur


    def setConfig( self, var, val ):

        cur = self.cursor()

        cur.execute( "insert or replace into config(var,val) values (?,?)", ( var, val ) )
        self.con.commit()
        cur.close()

    def getConfig( self, var ):
        cur = self.cursor()
        cur.execute( "select val from config where var is ? limit 1", ( var, ) )
        result = cur.fetchone()
        cur.close()
        if result:
            return result[0]
        else:
            return False

    def getSystemIDbyName(self,system):

        system = system.lower()

        result = self.__systemIDCache.get(system)
        if result:
            return result
        
        cur = self.cursor()
        cur.execute( "select id from systems where System is ? limit 1", ( system, ) )

        result = cur.fetchone()
        cur.close()
        if result:
            self.__systemIDCache[system] = result[0]
            return result[0]

    def getStationID(self,systemID,station):
        if not systemID or not station:
            return
        station = station.lower()
        key = "%d_%s" % (systemID,station) 

        result = self.__stationIDCache.get( key )
        if result:
            return result

        cur = self.cursor()
        cur.execute( "select id from stations where systemID is ? and Station is ? limit 1", (systemID, station, ) )
        result = cur.fetchone()

        cur.close()
        if result:
            self.__stationIDCache[key] = result[0]
            return result[0]

    def getItemID(self,itemname):

        result = self.__itemIDCache.get(itemname.lower())
        if result:
            return result
        
        cur = self.cursor()
        cur.execute( "select id from items where name is ?  limit 1", (itemname, ) )
        result = cur.fetchone()

        cur.close()
        if result:
            self.__itemIDCache[itemname.lower()] = result[0]
            return result[0]

    def getSystemData(self,systemID):
        cur = self.cursor()
        cur.execute( "select * from systems where id is ? limit 1", ( systemID, ) )
        result = cur.fetchone()
        cur.close()
        return result
        
    def getStationData(self,stationID):
        cur = self.cursor()
        cur.execute( "select * from stations where id is ? limit 1", ( stationID, ) )
        result = cur.fetchone()
        cur.close()
        return result

    def getItemPriceDataByID(self,systemID,stationID,itemID):
        cur = self.cursor()
        cur.execute( "select * from price where SystemID is ? and StationID is ? AND ItemID is ? limit 1", ( systemID,stationID,itemID, ) )
        result = cur.fetchone()
        cur.close()
        return result

    def getItemPriceModifiedDate(self,systemID,stationID,itemID):
        cur = self.cursor()
        cur.execute( "select modified from price where SystemID is ? and StationID is ? AND ItemID is ? limit 1", ( systemID,stationID,itemID, ) )
        result = cur.fetchone()
        cur.close()
        if result: return result[0]
        return None

    def getSystemsInDistance(self, system, distance):
        # system is systemid or name

        if isinstance(system,int):
            systemID = system
        else:
            systemID = self.getSystemIDbyName(system)

        cur = self.cursor()

        #get pos data from systemA
        cur.execute( "select * from systems  where id is ?  limit 1", ( systemID, ) )
        systemA = cur.fetchone()

#        cur.execute( "select id, calcDistance(?, ?, ?, posX, posY, posZ ) AS dist, System  from systems where id != ? AND dist < ? order by dist", ( systemA["posX"],systemA["posY"],systemA["posZ"],systemID,distance, ) )
        cur.execute( "select id, calcDistance(?, ?, ?, posX, posY, posZ ) AS dist, System  from systems where  dist < ? order by dist", ( systemA["posX"],systemA["posY"],systemA["posZ"],distance, ) )
        result = cur.fetchall()

        cur.close()
        return result

    def getDistanceFromTo(self, systemA, systemB):
        # system is systemid or name

        if not isinstance(systemA,int):
            systemA = self.getSystemIDbyName(systemA)

        if not isinstance(systemB,int):
            systemB = self.getSystemIDbyName(systemB)

        cur = self.cursor()


        cur.execute("""select calcDistance(a.posX, a.posY, a.posZ, b.posX, b.posY, b.posZ ) As dist FROM systems AS a
                    left JOIN systems AS b on b.id = ?
                    where a.id is ? """  , ( systemA, systemB, )  )
        
        result = cur.fetchone()
        cur.close()
        if result:
            return result[0]
        return result


    def getPricesInDistance(self, system, distance,maxStarDist, maxAgeDate):
        # system is systemid or name

        if isinstance(system,int):
            systemID = system
        else:
            systemID = self.getSystemIDbyName(system)
        cur = self.cursor()

        #get pos data from systemA
        cur.execute( "select * from systems  where id is ?  limit 1", ( systemID, ) )
        systemA = cur.fetchone()

        #cur.execute( "select id, calcDistance(?, ?, ?, posX, posY, posZ ) AS dist, System  from systems where id != ? AND dist < ? order by dist", ( systemA["posX"],systemA["posY"],systemA["posZ"],systemID,distance, ) )


        cur.execute("""select * FROM price
                        inner JOIN   (select id, calcDistance(?, ?, ?, posX, posY, posZ ) AS dist, System  from systems where  dist <= ? ) as dist ON dist.id=price.systemID
                    left JOIN items on items.id = price.ItemID
                    left JOIN systems on systems.id = price.SystemID
                    left JOIN stations on stations.id = price.StationID
 
                    where   
                        price.modified >= ?
                        AND stations.StarDist <= ?
                        """  , (systemA["posX"],systemA["posY"],systemA["posZ"], distance, maxAgeDate, maxStarDist  )  )
        
        result = cur.fetchall()

        cur.close()
        return result


    def getDealsFromTo(self,systemA, systemB, maxAgeDate):
        '''
        unused only experimental
        '''
        # systemB is name, systemID or systemID list
        # system is systemID or name
        if isinstance(systemA,int):
            systemAID = systemA
        else:
            systemAID = self.getSystemIDbyName(systemA)

        if isinstance(systemB,int):
            systemBID = systemB
            systemBseq = "?"
        elif isinstance(systemB,list):
            pass
            systemB.append(systemAID)
            systemBID = systemB
            systemBseq=','.join(['?']*len(systemB))
        else:
            systemBID = self.getSystemIDbyName(systemB)
            systemBseq = "?"
        print(systemBseq)

        #print(systemAID, systemBID)
        cur = self.cursor()

        cur.execute("DROP TABLE IF EXISTS testtable ")

        systemBID.append(maxAgeDate)
        cur.execute("CREATE /*TEMPORARY*/ TABLE testtable AS select * FROM price where systemID in (%s)  AND modified > ?" % (systemBseq) , systemBID  )
        return
        cur.execute("DROP TABLE IF EXISTS testtable2")
 #       cur.execute( """CREATE /*TEMPORARY*/ TABLE testtable2 AS select  
        cur.execute( """select  
                        ( b.StationBuy - a.StationSell ) AS profitAtoB,
                        ( a.StationBuy - b.StationSell ) AS profitBtoA, 
                        items.name AS itemName, a.StationID AS AstationID ,a.ItemID as itemID, a.StationSell AS AstationSell, a.StationBuy AS AstationBuy,
                        b.StationID AS BstationID,  b.StationSell AS BstationSell, b.StationBuy AS BstationBuy
                     from testtable AS a
                     inner  JOIN testtable as b ON  b.SystemID is ? AND a.ItemID = b.ItemID AND b.modified > ?
                     left JOIN items on items.id = a.ItemID
                        where  a.SystemID is ? AND  a.modified >= ?   """, ( systemBID,maxAgeDate,systemAID,maxAgeDate,  ) )

#/*SELECT `_rowid_`,* FROM `testtable2` where AstationSell > 0  ORDER BY profitAtoB DESC */
#SELECT `_rowid_`,* FROM `testtable2` where BstationSell > 0  ORDER BY profitBtoA DESC 

        result = cur.fetchall()

        cur.close()
        return result

    def getPricesFrom(self,system, maxStarDist, maxAgeDate):
        # system is name, systemID or systemID list (maximal 999 systems)

        if isinstance(system,int):
            systemIDs = [system]
            systemBseq = "?"
        elif isinstance(system,list):
            #print(len(system))
            systemIDs = system
            systemBseq=','.join(['?']*len(systemIDs))
        else:
            systemIDs = [self.getSystemIDbyName(system)]
            systemBseq = "?"
        #print(systemBseq)

        #print(systemAID, systemBID)
        cur = self.cursor()

        # add maxAgeDate to list end
        systemIDs.append(maxAgeDate)
        systemIDs.append(maxStarDist)

        cur.execute("""select * FROM price
                    left JOIN items on items.id = price.ItemID
                    left JOIN systems on systems.id = price.SystemID
                    left JOIN stations on stations.id = price.StationID
 
                    where  price.systemID in (%s)
                    AND  price.modified >= ?
                    AND stations.StarDist <= ?
                    """ % (systemBseq) , systemIDs  )

        result = cur.fetchall()

        cur.close()
        return result

if __name__ == '__main__':
    #mydb = db()
    pass
