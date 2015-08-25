# -*- coding: UTF8
'''
Created on 23.07.2015

@author: mEDI

'''

import sqlite3
import os
from datetime import datetime, timedelta

import elite.loader.maddavo
import elite.loader.bpc
import elite.loader.EDMarakedConnector
import elite.loader.eddb 
import elite.loader.raresimport

import sqlite3_functions

DBPATH = os.path.join("db","my.db")
DBVERSION = 1

class db(object):

    path = None
    con = None
    __stationIDCache = {}
    __systemIDCache = {}
    __itemIDCache = {}

    def __init__(self, guiMode=None):

        self.guiMode = guiMode
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
            self.initDB()
            self.importData()
        else:
            self.initDB()

        #self.fillCache()
            
        dbVersion = self.getConfig( 'dbVersion' )
        if dbVersion == False:
            print(dbVersion)
            print("version false db")
            self.initDB()

        if not self.guiMode:
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

        elite.loader.raresimport.loader(self).importData('db/rares.csv')
        
    def updateData(self):
        '''
        update price date from all sources
        '''        

        elite.loader.eddb.updateAll(self)

        elite.loader.EDMarakedConnector.loader(self).update()

        elite.loader.maddavo.updateAll(self)

        elite.loader.bpc.prices.loader(self).importData()

        lastOptimize = self.getConfig( 'lastOptimizeDatabase' )
        optimize = None
        if lastOptimize:
            lastOptimize = datetime.strptime(lastOptimize , "%Y-%m-%d %H:%M:%S")
            if lastOptimize + timedelta(days=7) < datetime.now():
                optimize = True
        else:
            optimize = True

        if optimize:
            self.optimizeDatabase()
            self.setConfig( 'lastOptimizeDatabase', datetime.now().strftime("%Y-%m-%d %H:%M:%S") )
            
    def initDB(self):
        print("create/update db")
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

        #fakePrice
        self.con.execute( "CREATE TABLE IF NOT EXISTS fakePrice (priceID INTEGER PRIMARY KEY  )" )

        #default config
        self.con.execute( "insert or ignore into config(var,val) values (?,?)", ( "dbVersion", DBVERSION ) )
        self.con.execute( "insert or ignore into config(var,val) values (?,?)", ( "EDMarkedConnector_cvsDir", r'c:\Users\mEDI\Documents\ED' ) )
        self.con.execute( "insert or ignore into config(var,val) values (?,?)", ( "EliteLogDir", r'C:\Program Files (x86)\Steam\SteamApps\common\Elite Dangerous\Products\FORC-FDEV-D-1010\Logs' ) )
        self.con.execute( "insert or ignore into config(var,val) values (?,?)", ( "BPC_db_path", r'c:\Program Files (x86)\Slopeys ED BPC\ED4.db' ) )

        #rares
        self.con.execute( "CREATE TABLE IF NOT EXISTS rares (id INTEGER PRIMARY KEY AUTOINCREMENT, SystemID INT NOT NULL, StationID INT NOT NULL, Name TEXT, Price INT, MaxAvail INT, illegal BOOLEAN DEFAULT NULL, offline BOOLEAN DEFAULT NULL, modifydate timestamp, comment TEXT )" )

        #dealCache dynamic cache
        self.con.execute( "CREATE TABLE IF NOT EXISTS dealsInDistances(dist FLOAT, priceAID INT, priceBID INT)" )
        self.con.execute( "create UNIQUE index  IF NOT EXISTS dealsInDistances_unique_priceA_priceB on dealsInDistances (priceAID, priceBID)" )

        self.con.execute( "CREATE TABLE IF NOT EXISTS dealsInDistancesSystems(systemID INT, dist FLOAT)" )
        self.con.execute( "create UNIQUE index  IF NOT EXISTS dealsInDistancesSystems_unique_systemID on dealsInDistancesSystems (systemID)" )
        self.con.execute( "CREATE TABLE IF NOT EXISTS dealsInDistancesSystems_queue (systemID INTEGER PRIMARY KEY)" )

        # trigger to controll the dynamic cache
        self.con.execute( """CREATE TRIGGER IF NOT EXISTS trigger_update_price AFTER UPDATE  OF StationBuy, StationSell ON  price
                            WHEN NEW.StationBuy != OLD.StationBuy OR NEW.StationSell != OLD.StationSell
                            BEGIN
                                DELETE FROM dealsInDistances WHERE priceAID=OLD.id;
                                DELETE FROM dealsInDistancesSystems WHERE systemID=OLD.SystemID;
                            END; """ )

        self.con.execute( """CREATE TRIGGER IF NOT EXISTS trigger_delete_price AFTER DELETE  ON  price
                            BEGIN
                                DELETE FROM dealsInDistances WHERE priceAID=OLD.id;
                                DELETE FROM dealsInDistances WHERE priceBID=OLD.id;
                                DELETE FROM dealsInDistancesSystems WHERE systemID=OLD.SystemID;
                            END; """ )

        self.con.execute( """CREATE TRIGGER IF NOT EXISTS trigger_insert_price AFTER INSERT  ON  price
                            BEGIN
                                DELETE FROM dealsInDistancesSystems WHERE systemID=NEW.SystemID;
                            END; """ )


        self.con.execute( """CREATE TRIGGER IF NOT EXISTS trigger_delete_dealsInDistancesSystems AFTER DELETE  ON  dealsInDistancesSystems
                            BEGIN
                                insert or ignore into dealsInDistancesSystems_queue (systemID) values(OLD.systemID);
                            END; """ )


        self.con.commit()

    def optimizeDatabase(self):
        '''
        optimize all tables and indexes
        '''
        cur = self.cursor()

        cur.execute( "select * from sqlite_master order by rootpage" )
        result = cur.fetchall()

        for table in result:
            print("vacuum %s" % table["name"])
            self.con.execute( "vacuum '%s'" % table["name"]  )

        cur.execute( "select * from sqlite_master where type = 'table' order by rootpage" )
        result = cur.fetchall()

        for table in result:
            print("analyze %s" % table["name"])
            cur.execute( "analyze '%s'" %  table["name"] )

        self.con.commit()
        cur.close()
        
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

    def setFakePrice(self, id):
        if isinstance( id, int):
            self.con.execute( "insert or ignore into fakePrice (priceID) values(?);", ( id, ) )
            self.con.commit()

        
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

    def getDealsFromTo(self, fromStation,  toStation, maxAgeDate=datetime.utcnow()-timedelta(days=14), minStock=0 ):

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
                            priceA.id AS priceAid, priceB.id AS priceBid,
                             items.name AS itemName,
                             stationA.Station AS fromStation,
                             stationB.Station AS toStation
                             
                    FROM price AS priceA

                    inner JOIN price AS priceB ON priceB.StationID=? AND priceA.ItemID=priceB.ItemID AND priceB.StationBuy > priceA.StationSell
                    left JOIN items on priceA.ItemID=items.id
                    left JOIN stations AS stationA on priceA.StationID=stationA.id
                    left JOIN stations AS stationB on priceB.StationID=stationB.id

                    left JOIN fakePrice AS fakePriceA ON priceA.id=fakePriceA.priceID
                    left JOIN fakePrice AS fakePriceB ON priceB.id=fakePriceB.priceID

                    WHERE 

                        priceA.StationID=? 
                        AND priceA.StationSell > 0
                        AND priceA.Stock > ?
                        AND priceA.modified >= ?
                        AND priceB.modified >= ?
                        AND fakePriceA.priceID IS NULL and fakePriceB.priceID IS NULL
                    order by profit DESC
                    ''', (toStationID, fromStationID, minStock, maxAgeDate, maxAgeDate))
        
        result = cur.fetchall()
        cur.close()

#        for i in result:
#            print(i)
            
        return result

    def calcDealsInDistancesCache(self, systemIDlist, maxAgeDate , minTradeProfit=1000,dist=51):
        print("calcDealsInDistancesCache", len(systemIDlist))

        cur = self.cursor()

        for system in systemIDlist:
            systemID = system["id"]

            cur.execute("INSERT or IGNORE INTO dealsInDistancesSystems ( systemID, dist ) values (?, ? )", (systemID, dist )) 

            cur.execute( "select * from systems  where id = ?  limit 1", ( systemID, ) )
            systemA = cur.fetchone()
    
            cur.execute("""INSERT or IGNORE INTO dealsInDistances (dist,  priceAID,  priceBID ) 

                            select dist, priceA.id AS priceAID, priceB.id AS priceBID 
/*                            
                            FROM price AS priceA

                            inner JOIN   (select priceB.id AS id , priceB.StationBuy, priceB.ItemID,  calcDistance(?, ?, ?, systemB.posX, systemB.posY, systemB.posZ ) AS dist
                                            from systems AS systemB 
                                            inner join price AS priceB ON priceB.SystemID=systemB.id 
                                            where priceB.StationBuy > 0 AND priceB.modified >= ? AND dist <= ?) 
                                AS priceB ON priceA.ItemID=priceB.ItemID 

*/
                            FROM (select priceB.id AS id , priceB.StationBuy, priceB.ItemID,  calcDistance(?, ?, ?, systemB.posX, systemB.posY, systemB.posZ ) AS dist
                                            from systems AS systemB 
                                            inner join price AS priceB ON priceB.SystemID=systemB.id 
                                            where priceB.StationBuy > 0 AND priceB.modified >= ? AND dist <= ?) 
                                AS priceB  

                            inner JOIN price AS priceA ON priceA.ItemID=priceB.ItemID       

                            left JOIN fakePrice AS fakePriceA ON priceA.id=fakePriceA.priceID
                            left JOIN fakePrice AS fakePriceB ON priceB.id=fakePriceB.priceID

                        where
                            priceA.SystemID = ?
                            AND priceA.modified >= ?
                            AND priceA.StationSell > 0 

                            AND priceB.StationBuy > priceA.StationSell 
                            AND priceB.StationBuy - priceA.StationSell >= ?

                            AND fakePriceA.priceID IS NULL and fakePriceB.priceID IS NULL

                            """  , (systemA["posX"], systemA["posY"], systemA["posZ"], maxAgeDate, dist, systemID,  maxAgeDate, minTradeProfit  )  )

            # delete system from queue
            cur.execute("DELETE FROM dealsInDistancesSystems_queue WHERE systemID=?", [systemID])

            self.con.commit()

    def calcDealsInDistancesCacheQueue(self):
        cur = self.cursor()

        cur.execute( "select systemID AS id  from dealsInDistancesSystems_queue")
        systemList = cur.fetchall()
        if systemList:
            maxAgeDate = datetime.utcnow() - timedelta(days=14) #TODO: save max age and use the max?
            self.calcDealsInDistancesCache(systemList, maxAgeDate )


    def checkDealsInDistancesCache(self):
        cur = self.cursor()

        cur.execute( """select * from dealsInDistances
                    left join price AS priceA ON priceA.id=dealsInDistances.priceAID
                    left join price AS priceB ON priceB.id=dealsInDistances.priceBID
                     where
                       priceB.StationBuy < priceA.StationSell 
                       OR priceB.StationBuy IS NULL
                       OR priceA.StationSell IS NULL
                     """)

        result = cur.fetchone()

    def getBestDealsinDistance(self, system, distance,maxSearchRange, maxAgeDate, maxStarDist, minProfit, minStock, resultLimit=50):
        if isinstance(system,int):
            systemID = system
        else:
            systemID = self.getSystemIDbyName(system)

        cur = self.cursor()

        #get pos data from systemA
        cur.execute( "select * from systems  where id = ?  limit 1", ( systemID, ) )
        systemA = cur.fetchone()

        # use a temp table to build a startsystem list
        cur.execute("DROP TABLE IF EXISTS TEAMP_selectSystemA ")
        cur.execute("""CREATE TEMPORARY TABLE TEAMP_selectSystemA AS select systemA.id AS id, systemA.posX AS posX, systemA.posY AS posY, systemA.posZ AS posZ, systemA.System AS System, systemA.startDist AS startDist

                        FROM ( select calcDistance(?, ?, ?, systems.posX, systems.posY, systems.posZ ) as startDist, * from systems where startDist <= ? ) as systemA

                        inner join price AS priceA ON systemA.id=priceA.SystemID

                        left JOIN stations AS stationA on stationA.id = priceA.StationID

                    where
                        priceA.modified >= ?
                        AND priceA.StationSell>0 
                        AND priceA.Stock>=?
                        AND systemA.permit != 1
                        AND stationA.StarDist <= ?

                    group by systemA.id
                    
                        """    , ( systemA["posX"], systemA["posY"], systemA["posZ"], maxSearchRange, maxAgeDate, minStock, maxStarDist)  ) 

        # check the dealsIndistance cache
        cur.execute( """select id, calcDistance(?, ?, ?, posX, posY, posZ ) AS distn, dealsInDistancesSystems.dist
                             from TEAMP_selectSystemA AS systems 
                             
                             LEFT join dealsInDistancesSystems  ON systems.id=dealsInDistancesSystems.SystemID
                             where  distn<=? AND dealsInDistancesSystems.dist is NULL group by id
                             
                             """, ( systemA["posX"], systemA["posY"], systemA["posZ"],  distance, ) )
        systemList = cur.fetchall()
        if systemList:
            self.calcDealsInDistancesCache(systemList, maxAgeDate)


        cur.execute(""" select priceB.StationBuy-priceA.StationSell AS profit, priceA.id, priceB.id,
                        priceA.ItemID , priceB.StationBuy AS StationBuy, priceA.StationSell AS StationSell,
                        systemA.System AS SystemA, priceA.id AS priceAid, priceA.SystemID AS SystemAID, priceA.StationID AS StationAID, stationA.Station AS StationA, stationA.StarDist, stationA.refuel,
                        systemB.System AS SystemB, priceB.id AS priceBid, priceB.SystemID AS SystemBID, priceB.StationID AS StationBID, stationB.Station AS StationB, stationB.StarDist AS StarDist, stationB.refuel AS refuel,
                        dist, systemA.startDist AS startDist, items.name AS itemName 

                        from TEAMP_selectSystemA AS systemA

                        inner join (select * from  dealsInDistances inner join price ON price.id=dealsInDistances.priceAID WHERE dealsInDistances.dist <= ? ) AS priceA ON priceA.SystemID=systemA.id

                        inner join price AS priceB on priceB.id=priceA.priceBID

                        left join systems AS systemB  ON systemB.id=priceB.SystemID

                        left JOIN stations AS stationA on stationA.id = priceA.StationID

                        left JOIN stations AS stationB on stationB.id = priceB.StationID

                        left JOIN items on priceA.ItemID=items.id

                        left JOIN fakePrice AS fakePriceA ON priceA.id=fakePriceA.priceID
                        left JOIN fakePrice AS fakePriceB ON priceB.id=fakePriceB.priceID

                    where
                        priceA.modified >= ?
                        AND priceA.StationSell>0 
                        AND priceA.Stock>=?
                        AND stationA.StarDist <= ?

                        AND priceB.modified >= ?
                        AND priceB.StationBuy>0 
                        AND systemB.permit != 1
                        AND stationB.StarDist <= ?

                        AND  priceB.StationBuy > priceA.StationSell 
                        AND priceB.StationBuy-priceA.StationSell >= ?
                        AND fakePriceA.priceID IS NULL and fakePriceB.priceID IS NULL

                    order by profit DESC

                        limit ?

                        """    , ( distance, maxAgeDate, minStock, maxStarDist, maxAgeDate, maxStarDist, minProfit, resultLimit)  ) #  

        result = cur.fetchall()

        cur.close()
        return result


    def getBestDealsFromStationInDistance(self,stationID, distance, maxAgeDate, maxStarDist, minProfit, minStock, reslultLimit=20):

        cur = self.cursor()

        #get pos data from systemA
        cur.execute( "select * from stations left join systems on systems.id=stations.SystemID  where stations.id = ?  limit 1", ( stationID, ) )
        stationA = cur.fetchone()


        # check the dealsIndistance cache
        cur.execute( """select id, calcDistance(?, ?, ?, posX, posY, posZ ) AS distn, dealsInDistancesSystems.dist
                             from TEAMP_selectSystemA AS systems 
                             
                             LEFT join dealsInDistancesSystems  ON systems.id=dealsInDistancesSystems.SystemID
                             where  distn<=? AND dealsInDistancesSystems.dist is NULL group by id
                             
                             """, ( stationA["posX"], stationA["posY"], stationA["posZ"],  distance, ) )
        systemList = cur.fetchall()
        if systemList:
            self.calcDealsInDistancesCache(systemList, maxAgeDate)

        cur.execute(""" select priceB.StationBuy-priceA.StationSell AS profit, priceA.ItemID, priceA.id AS priceAid, priceB.StationBuy, priceA.StationSell,
                        systemB.System AS SystemB, priceB.SystemID AS SystemBID , priceB.id AS priceBid, priceB.StationID AS StationBID, stationB.Station AS StationB, stationB.StarDist AS StarDist, stationB.refuel AS refuel,
                        systemA.System AS SystemA,
                        dist, items.name AS itemName

                        FROM price AS priceA

                        inner join dealsInDistances ON dealsInDistances.priceAID=priceA.id

                        inner join price AS priceB on priceB.id=dealsInDistances.priceBID

                        left join systems AS systemA  ON systemA.id=priceA.SystemID
                        left join systems AS systemB  ON systemB.id=priceB.SystemID
                        left JOIN stations AS stationB on stationB.id = priceB.StationID
                        left JOIN items on priceA.ItemID=items.id

                        left JOIN fakePrice AS fakePriceA ON priceA.id=fakePriceA.priceID
                        left JOIN fakePrice AS fakePriceB ON priceB.id=fakePriceB.priceID

                    where
                        priceA.StationID=?
                        AND priceA.Stock>=?
                        AND dealsInDistances.dist <= ?
                        AND priceA.modified >= ?
                        AND priceB.modified >= ?
                        AND systemB.permit != 1
                        
                        AND priceA.StationSell>0 
                        AND stationB.StarDist <= ?
                        AND priceB.StationBuy > priceA.StationSell
                        AND profit >= ? 
                        AND fakePriceA.priceID IS NULL and fakePriceB.priceID IS NULL
                        order by profit DESC
                        limit ?
                        """    , ( stationID, minStock,  distance, maxAgeDate, maxAgeDate, maxStarDist,minProfit, reslultLimit  )  )
        
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
