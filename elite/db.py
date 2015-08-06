# -*- coding: UTF8
'''
Created on 23.07.2015

@author: mEDI


speedup: http://codereview.stackexchange.com/questions/26822/myth-busting-sqlite3-performance-w-pysqlite
'''
import sqlite3
import os
import sys

import elite.loader.maddavo as maddavo_loader
import elite.loader.bpc as bpc_loader
import elite.loader.EDMarakedConnector as EDMarakedConnector_loader
import elite.loader.eddb as eddb_loader
import elite.loader.raresimport as raresimport

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
#        self.initNewDB()
#        self.importData()
        self.fillCache()
            
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

        raresimport.loader(self).importData('db/rares.csv')
        
    def updateData(self):
        '''
        update price date from all sources
        '''        
        print("update data")
        
        eddb_commodities = eddb_loader.items.loader(self)
        eddb_commodities.update()

        eddb_systems = eddb_loader.systems.loader(self)
        eddb_systems.update()

        eddb_stations = eddb_loader.stations.loader(self)
        eddb_stations.update()

        edMarked =  EDMarakedConnector_loader.loader(self)
        edMarked.update()

        maddavo_station = maddavo_loader.station.loader(self)
        maddavo_station.update()

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
        self.con.execute( "CREATE TABLE IF NOT EXISTS systems (id INTEGER PRIMARY KEY AUTOINCREMENT, System TEXT COLLATE NOCASE UNIQUE , posX FLOAT, posY FLOAT, posZ FLOAT, permit BOOLEAN DEFAULT 0, modified timestamp)" )
#        self.con.execute( "create UNIQUE index  IF NOT EXISTS systems_unique_System on systems (System)" )

        #stations
        self.con.execute( "CREATE TABLE IF NOT EXISTS stations (id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE, SystemID INT NOT NULL, Station TEXT COLLATE NOCASE, StarDist INT, blackmarket BOOLEAN, max_pad_size CHARACTER, market BOOLEAN, shipyard BOOLEAN,outfitting BOOLEAN,rearm BOOLEAN,refuel BOOLEAN,repair BOOLEAN, modified timestamp)" )
        self.con.execute( "create UNIQUE index  IF NOT EXISTS station_unique_system_Station on stations (SystemID, Station)" )

        #items
        self.con.execute( "CREATE TABLE IF NOT EXISTS items (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT COLLATE NOCASE UNIQUE, category TEXT COLLATE NOCASE, ui_sort TINYINT )" )
        #price
        self.con.execute( "CREATE TABLE IF NOT EXISTS price (id INTEGER PRIMARY KEY AUTOINCREMENT, SystemID INT NOT NULL, StationID INT NOT NULL, ItemID INT NOT NULL, StationSell INT NOT NULL DEFAULT 0, StationBuy INT NOT NULL DEFAULT 0, Dammand INT NOT NULL DEFAULT 0, Stock INT NOT NULL DEFAULT 0, modified timestamp, source INT NOT NULL)" )
        self.con.execute( "create UNIQUE index  IF NOT EXISTS price_unique_System_Station_Item on price (SystemID,StationID,ItemID)" )
        self.con.execute( "CREATE UNIQUE INDEX IF NOT EXISTS `price_index_StationID_ItemID` ON `price` (`StationID` ,`ItemID` )")
        self.con.execute( "create index  IF NOT EXISTS price_modified on price (modified)" )

        #det default config
        self.con.execute( "insert or ignore into config(var,val) values (?,?)", ( "dbVersion", DBVERSION ) )
        self.con.execute( "insert or ignore into config(var,val) values (?,?)", ( "EDMarkedConnector_cvsDir", 'c:\Users\mEDI\Documents\ED' ) )

        #rares
        self.con.execute( "CREATE TABLE IF NOT EXISTS rares (id INTEGER PRIMARY KEY AUTOINCREMENT, SystemID INT NOT NULL, StationID INT NOT NULL, Name TEXT, Price INT, MaxAvail INT, illegal BOOLEAN DEFAULT NULL, offline BOOLEAN DEFAULT NULL, modifydate timestamp, comment TEXT )" )
        
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
        cur.execute( "select val from config where var = ? limit 1", ( var, ) )
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
        cur.execute( "select id from systems where LOWER(System) = ? limit 1", ( system, ) )

        result = cur.fetchone()
        cur.close()
        if result:
            self.__systemIDCache[system] = result[0]
            return result[0]

    def getSystemname(self,SystemID):
        cur = self.cursor()
        cur.execute( "select System from systems where id = ? limit 1", ( SystemID, ) )

        result = cur.fetchone()
        cur.close()
        if result:
            return result[0]

    def getStationID(self, systemID, station):
        if not systemID or not station:
            return
        station = station.lower()
        key = "%d_%s" % (systemID,station) 

        result = self.__stationIDCache.get( key )
        if result:
            return result

        cur = self.cursor()
        cur.execute( "select id from stations where systemID = ? and LOWER(Station) = ? limit 1", (systemID, station, ) )
        result = cur.fetchone()

        cur.close()
        if result:
            self.__stationIDCache[key] = result[0]
            return result[0]

    def getStationname(self,stationID):

        cur = self.cursor()
        cur.execute( "select Station from stations where id = ? limit 1", (stationID, ) )
        result = cur.fetchone()
        cur.close()
        if result:
            return result[0]
        
    def getStarDistFromStation(self, station, system=None):
        '''
        allow stationID or (station name + (system name or systemID))
        '''
        if not isinstance(station, int):
            if isinstance(system, int):
                systemID = system
            else:
                systemID = self.getSystemIDbyName(system)

            systemID = self.getStationID(systemID, station)
        else:
            stationID = station

        if not stationID: return
        
        cur = self.cursor()
        cur.execute( "select StarDist from stations where id = ? limit 1", ( stationID, ) )
        result = cur.fetchone()
        cur.close()
        return result[0]

    def getItemID(self,itemname):

        result = self.__itemIDCache.get(itemname.lower())
        if result:
            return result
        
        cur = self.cursor()
        cur.execute( "select id from items where LOWER(name) = ?  limit 1", (itemname.lower(), ) )
        result = cur.fetchone()

        cur.close()
        if result:
            self.__itemIDCache[itemname.lower()] = result[0]
            return result[0]

    def getSystemData(self,systemID):
        cur = self.cursor()
        cur.execute( "select * from systems where id = ? limit 1", ( systemID, ) )
        result = cur.fetchone()
        cur.close()
        return result

    def getStationsFromSystem(self,system):

        if isinstance(system, int):
            systemID = system
        else:
            systemID = self.getSystemIDbyName(system)

        cur = self.con.cursor()
        cur.execute('SELECT id, Station FROM stations  where SystemID=? ' , (systemID,))
        rows = cur.fetchall()
        cur.close()
        stations = []
        for row in rows:
            stations.append( [ row["id"], row["Station"] ] )
        return stations
        
    def getStationData(self,stationID):
        cur = self.cursor()
        cur.execute( "select * from stations where id = ? limit 1", ( stationID, ) )
        result = cur.fetchone()
        cur.close()
        return result


    def getItemPriceDataByID(self,systemID,stationID,itemID):
        cur = self.cursor()
        cur.execute( "select * from price where SystemID = ? and StationID = ? AND ItemID = ? limit 1", ( systemID,stationID,itemID, ) )
        result = cur.fetchone()
        cur.close()
        return result

    def getItemPriceModifiedDate(self,systemID,stationID,itemID):
        cur = self.cursor()
        cur.execute( "select modified from price where SystemID = ? and StationID = ? AND ItemID = ? limit 1", ( systemID,stationID,itemID, ) )
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
        cur.execute( "select * from systems  where id = ?  limit 1", ( systemID, ) )
        systemA = cur.fetchone()

#        cur.execute( "select id, calcDistance(?, ?, ?, posX, posY, posZ ) AS dist, System  from systems where id != ? AND dist < ? order by dist", ( systemA["posX"],systemA["posY"],systemA["posZ"],systemID,distance, ) )
        cur.execute( "select id, calcDistance(?, ?, ?, posX, posY, posZ ) AS dist, System  from systems where  dist <= ? order by dist", ( systemA["posX"],systemA["posY"],systemA["posZ"],distance, ) )
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
                    where a.id = ? """  , ( systemA, systemB, )  )
        
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
        cur.execute( "select * from systems  where id = ?  limit 1", ( systemID, ) )
        systemA = cur.fetchone()

        #cur.execute( "select id, calcDistance(?, ?, ?, posX, posY, posZ ) AS dist, System  from systems where id != ? AND dist < ? order by dist", ( systemA["posX"],systemA["posY"],systemA["posZ"],systemID,distance, ) )


        cur.execute("""select * FROM price
                        inner JOIN   (select id, calcDistance(?, ?, ?, posX, posY, posZ ) AS dist, System  from systems where  dist <= ? ) as dist ON dist.id=price.systemID
                    left JOIN items on items.id = price.ItemID
                    left JOIN systems on systems.id = price.SystemID
                    left JOIN stations on stations.id = price.StationID
 
                    where
                        systems.permit != 1
                        AND price.modified >= ?
                        AND stations.StarDist <= ?
                        """  , (systemA["posX"],systemA["posY"],systemA["posZ"], distance, maxAgeDate, maxStarDist  )  )
        
        result = cur.fetchall()

        cur.close()
        return result

    def getDealsFromTo(self, fromStation,  toStation):

        if isinstance(fromStation,int):
            fromStationID = fromStation
        else:
            fromStationID = self.getStationID( fromStation )

        if isinstance(toStation,int):
            toStationID = toStation
        else:
            toStationID = self.getStationID( toStation )

        cur = self.cursor()

        cur.execute('''select priceA.ItemID AS ItemID, priceB.StationBuy-priceA.StationSell AS profit,
                             priceB.StationBuy AS StationBuy,  priceA.StationSell AS StationSell,
                             items.name AS itemName,
                             stationA.Station AS fromStation,
                             stationB.Station AS toStation
                             
                    FROM price AS priceA

                    inner JOIN price AS priceB ON priceB.StationID=? AND priceA.ItemID=priceB.ItemID AND priceB.StationBuy > priceA.StationSell
                    left JOIN items on priceA.ItemID=items.id
                    left JOIN stations AS stationA on priceA.StationID=stationA.id
                    left JOIN stations AS stationB on priceB.StationID=stationB.id

                    WHERE priceA.StationSell > 0 AND priceA.StationID=? 
                    ''', (toStationID,fromStationID))
        
        result = cur.fetchall()
        cur.close()

#        for i in result:
#            print(i)
            
        return result


    def getDealsFromTo_old(self,systemA, systemB, maxAgeDate):
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
#        cur.execute( """CREATE /*TEMPORARY*/ TABLE testtable2 AS select  
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
