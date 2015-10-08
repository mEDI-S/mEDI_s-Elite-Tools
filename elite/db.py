# -*- coding: UTF8
'''
Created on 23.07.2015

@author: mEDI

'''

import sqlite3
import os
import sys
from datetime import datetime, timedelta

import elite.loader.maddavo
import elite.loader.bpc
import elite.loader.EDMarakedConnector
import elite.loader.eddb
import elite.loader.raresimport
import elite.loader.eddn

__loaderCount__ = 6
__forceupdateFile__ = "updatetrigger.txt"

import sqlite3_functions

__DBPATH__ = os.path.join("db", "my.db")
DBVERSION = 2


class db(object):

    path = None
    con = None
    __stationIDCache = {}
    __systemIDCache = {}
    __itemIDCache = {}
    __configCache = {}
    __streamUpdater = []
    loaderCount = __loaderCount__
    sendProcessMsg = None
    
    def __init__(self, guiMode=None, DBPATH=__DBPATH__):

        self.guiMode = guiMode
        self._active = True
        if self.con is not None:
            return

        new_db = None
        if not os.path.isfile(DBPATH):
            print("new db")
            new_db = True

        self.con = sqlite3.connect(DBPATH, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES, check_same_thread=False)
        self.con.row_factory = sqlite3.Row

        sqlite3_functions.registerSQLiteFunktions(self.con)

        if new_db:
            self.initDB()
            self.importData()
            self.getSystemPaths()
        else:
            pass
            # self.initDB()

        # self.fillCache()
        self.con.execute("PRAGMA journal_mode = MEMORY")
        self.con.execute("PRAGMA recursive_triggers=True")
            
        if self.getConfig('dbVersion') != DBVERSION:
            ''' run on database update'''
            self.initDB()
            self.getSystemPaths()
            self.setConfig('dbVersion', DBVERSION)
        elif self.getConfig('initRun') == "1" or os.path.isfile(__forceupdateFile__):
            ''' run on first start (install with build db or on update)'''
            print("init run")
            self.initDB()
            self.getSystemPaths()
            self.setConfig('initRun', 0)
            ''' remove trigger file '''
            if os.path.isfile(__forceupdateFile__):
                os.remove(__forceupdateFile__)
            
        if not self.guiMode:
            self.initDB()
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

        cur.execute("select id, SystemID, Station from stations")
        result = cur.fetchall()
        for station in result:
            key = "%d_%s" % (station["SystemID"], station["Station"])
            self.__stationIDCache[key] = station["id"]

        cur.execute("select id, System from systems")
        result = cur.fetchall()
        for system in result:
            self.__systemIDCache[system["System"] ] = system["id"]

        cur.close()
        
    def importData(self):
        print("import data")

        elite.loader.raresimport.loader(self).importData('db/rares.csv')

    def startStreamUpdater(self):
        ''' Start this only from a gui or other running instances and not in single run scripts'''

        if self.getConfig("plugin_eddn") is not 0:
            self.__streamUpdater.append(elite.loader.eddn.newClient(self))

    def stopStreamUpdater(self):
        if self.__streamUpdater:
            for client in self.__streamUpdater:
                client.stop()
                self.__streamUpdater.remove(client)

    def updateData(self):
        '''
        update price date from all sources
        '''
        myPos = 0
        if self._active is not True:
            return

        if self.getConfig("plugin_eddb") is not 0:
            myPos += 1
            if self.sendProcessMsg:
                self.sendProcessMsg("Update: EDDB", myPos, self.loaderCount)
            elite.loader.eddb.updateAll(self)
            if self._active is not True:
                return

        if self.getConfig("plugin_edmc") is not 0:
            myPos += 1
            if self.sendProcessMsg:
                self.sendProcessMsg("Update: EDMC", myPos, self.loaderCount)
            elite.loader.EDMarakedConnector.loader(self).update()
            if self._active is not True:
                return

        if self.getConfig("plugin_mms") is not 0:
            myPos += 1
            if self.sendProcessMsg:
                self.sendProcessMsg("Update: Maddavo", myPos, self.loaderCount)
            elite.loader.maddavo.updateAll(self)
            if self._active is not True:
                return

        if self.getConfig("plugin_bpc") is not 0:
            myPos += 1
            if self.sendProcessMsg:
                self.sendProcessMsg("Update: BPC", myPos, self.loaderCount)
            elite.loader.bpc.prices.loader(self).importData()
            if self._active is not True:
                return


        if self.getConfig("plugin_eddn") is not 0:
            myPos += 1
            if self.sendProcessMsg:
                self.sendProcessMsg("Update: EDDN", myPos, self.loaderCount)
            if self.__streamUpdater:
                for client in self.__streamUpdater:
                    client.update()

        if self.getConfig("plugin_eddndynamoDB") is not 0:
            myPos += 1
            if self.sendProcessMsg:
                self.sendProcessMsg("Update: EDDN dynamoDB", myPos, self.loaderCount)
            elite.loader.eddn.dynamoDB.loader(self).update()
            if self._active is not True:
                return


        lastOptimize = self.getConfig('lastOptimizeDatabase')
        optimize = None
        if lastOptimize:
            lastOptimize = datetime.strptime(lastOptimize, "%Y-%m-%d %H:%M:%S")
            if lastOptimize + timedelta(days=7) < datetime.now():
                optimize = True
        else:
            optimize = True

        if optimize:
            myPos += 1
            if self.sendProcessMsg:
                self.sendProcessMsg("Optimize DB", myPos, self.loaderCount)
            self.optimizeDatabase()

        if myPos is not self.loaderCount:
            self.loaderCount = myPos

    def initDB(self):
        print("create/update db")
        '''
        create tables
        '''
        self.con.execute("CREATE TABLE IF NOT EXISTS config(var TEXT,val)")
        self.con.execute("create UNIQUE index  IF NOT EXISTS config_unique_var on config (var)")


        # systems
        self.con.execute("CREATE TABLE IF NOT EXISTS systems (id INTEGER PRIMARY KEY AUTOINCREMENT, System TEXT COLLATE NOCASE UNIQUE , posX FLOAT, posY FLOAT, posZ FLOAT, permit BOOLEAN DEFAULT 0, power_control INT, government INT, allegiance INT, modified timestamp)")

        # stations
        self.con.execute("CREATE TABLE IF NOT EXISTS stations (id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE, SystemID INT NOT NULL, Station TEXT COLLATE NOCASE, StarDist INT, government INT, allegiance INT, blackmarket BOOLEAN, max_pad_size CHARACTER, market BOOLEAN, shipyard BOOLEAN,outfitting BOOLEAN,rearm BOOLEAN,refuel BOOLEAN,repair BOOLEAN, modified timestamp)")
        self.con.execute("create UNIQUE index  IF NOT EXISTS station_unique_system_Station on stations (SystemID, Station)")


        self.con.execute("CREATE TABLE IF NOT EXISTS allegiances (id INTEGER PRIMARY KEY AUTOINCREMENT, Name TEXT UNIQUE)")
        self.con.execute("CREATE TABLE IF NOT EXISTS governments (id INTEGER PRIMARY KEY AUTOINCREMENT, Name TEXT UNIQUE)")


        # items
        self.con.execute("CREATE TABLE IF NOT EXISTS items (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT COLLATE NOCASE UNIQUE, category TEXT COLLATE NOCASE, ui_sort TINYINT )")

        
        # price
        self.con.execute("CREATE TABLE IF NOT EXISTS price (id INTEGER PRIMARY KEY AUTOINCREMENT, SystemID INT NOT NULL, StationID INT NOT NULL, ItemID INT NOT NULL, StationSell INT NOT NULL DEFAULT 0, StationBuy INT NOT NULL DEFAULT 0, Dammand INT NOT NULL DEFAULT 0, Stock INT NOT NULL DEFAULT 0, modified timestamp, source INT NOT NULL)")
        self.con.execute("create UNIQUE index  IF NOT EXISTS price_unique_System_Station_Item on price (SystemID,StationID,ItemID)")
        self.con.execute("CREATE UNIQUE INDEX IF NOT EXISTS `price_index_StationID_ItemID` ON `price` (`StationID` ,`ItemID` )")
        self.con.execute("create index  IF NOT EXISTS price_modified on price (modified)")

        # fakePrice
        self.con.execute("CREATE TABLE IF NOT EXISTS fakePrice (priceID INTEGER PRIMARY KEY  )")
        self.con.execute("CREATE TABLE IF NOT EXISTS ignorePriceTemp (priceID INTEGER PRIMARY KEY  )")

        # blackmarketPrice
        self.con.execute("CREATE TABLE IF NOT EXISTS blackmarketPrice (priceID INTEGER PRIMARY KEY  )")

        # default config
        self.con.execute("insert or ignore into config(var,val) values (?,?)", ("dbVersion", DBVERSION))
        self.con.execute("insert or ignore into config(var,val) values (?,?)", ("EDMarkedConnector_cvsDir", r'c:\Users\mEDI\Documents\ED'))
        self.con.execute("insert or ignore into config(var,val) values (?,?)", ("EliteLogDir", r'C:\Program Files (x86)\Steam\SteamApps\common\Elite Dangerous\Products\FORC-FDEV-D-1010\Logs'))
        self.con.execute("insert or ignore into config(var,val) values (?,?)", ("BPC_db_path", r'c:\Program Files (x86)\Slopeys ED BPC\ED4.db'))

        # rares
        self.con.execute("CREATE TABLE IF NOT EXISTS rares (id INTEGER PRIMARY KEY AUTOINCREMENT, SystemID INT NOT NULL, StationID INT NOT NULL, Name TEXT, Price INT, MaxAvail INT, illegal BOOLEAN DEFAULT NULL, offline BOOLEAN DEFAULT NULL, modifydate timestamp, comment TEXT )")

        # dealCache dynamic cache
        self.con.execute("CREATE TABLE IF NOT EXISTS dealsInDistances(dist FLOAT, priceAID INT, priceBID INT)")
        self.con.execute("create UNIQUE index  IF NOT EXISTS dealsInDistances_unique_priceA_priceB on dealsInDistances (priceAID, priceBID)")

        self.con.execute("CREATE TABLE IF NOT EXISTS dealsInDistancesSystems(systemID INT, dist FLOAT)")
        self.con.execute("create UNIQUE index  IF NOT EXISTS dealsInDistancesSystems_unique_systemID on dealsInDistancesSystems (systemID)")
        self.con.execute("CREATE TABLE IF NOT EXISTS dealsInDistancesSystems_queue (systemID INTEGER PRIMARY KEY)")

        # ships and shipyard
        self.con.execute("CREATE TABLE IF NOT EXISTS ships (id INTEGER PRIMARY KEY AUTOINCREMENT, Name TEXT UNIQUE)")
        self.con.execute("CREATE TABLE IF NOT EXISTS shipyard (SystemID INT,StationID INT ,ShipID INT, Price INT, modifydate timestamp)")
        self.con.execute("create UNIQUE index  IF NOT EXISTS shipyard_unique_systemID_StationID_ShipID on shipyard (systemID, StationID, ShipID)")

        self.con.execute("CREATE TABLE IF NOT EXISTS outfitting_category (id INTEGER PRIMARY KEY AUTOINCREMENT, category TEXT UNIQUE)")
        self.con.execute("CREATE TABLE IF NOT EXISTS outfitting_modulename (id INTEGER PRIMARY KEY AUTOINCREMENT, modulename TEXT UNIQUE)")
        self.con.execute("CREATE TABLE IF NOT EXISTS outfitting_mount (id INTEGER PRIMARY KEY AUTOINCREMENT, mount TEXT UNIQUE)")
        self.con.execute("CREATE TABLE IF NOT EXISTS outfitting_guidance (id INTEGER PRIMARY KEY AUTOINCREMENT, guidance TEXT UNIQUE)")

        self.con.execute("CREATE TABLE IF NOT EXISTS outfitting (StationID INT, NameID INT, Class INT, MountID INT, CategoryID INT, Rating TEXT, GuidanceID INT, modifydate timestamp)")
        self.con.execute("create UNIQUE index  IF NOT EXISTS outfitting_unique_StationID_NameID_Class_Mount_Rating on outfitting (StationID, NameID, Class, MountID, Rating)")

        # powers
        self.con.execute("CREATE TABLE IF NOT EXISTS powers (id INTEGER PRIMARY KEY AUTOINCREMENT, Name TEXT UNIQUE)")

        # fly log
        self.con.execute("CREATE TABLE IF NOT EXISTS flylog (id INTEGER PRIMARY KEY AUTOINCREMENT, SystemID INT, optionalSystemName TEXT, Comment TEXT, DateTime timestamp)")


        # bookmarks
        self.con.execute("CREATE TABLE IF NOT EXISTS bookmarks (id INTEGER PRIMARY KEY AUTOINCREMENT, Type INT, Name TEXT)")
        self.con.execute("CREATE TABLE IF NOT EXISTS bookmarkChilds (BookmarkID INT, Pos INT,  SystemID INT, StationID INT, ItemID INT)")  # Type 0 = Deals/Multi Hop Route
        self.con.execute("create UNIQUE index IF NOT EXISTS bookmarkChilds_unique_BookmarkID on bookmarkChilds (BookmarkID, Pos)")

        # trigger to controll the dynamic cache
        self.con.execute("""CREATE TRIGGER IF NOT EXISTS trigger_update_price AFTER UPDATE  OF StationBuy, StationSell ON  price
                            WHEN NEW.StationBuy != OLD.StationBuy OR NEW.StationSell != OLD.StationSell
                            BEGIN
                                DELETE FROM dealsInDistances WHERE priceAID=OLD.id;
                                DELETE FROM dealsInDistancesSystems WHERE systemID=OLD.SystemID;
                            END; """)

        self.con.execute("""CREATE TRIGGER IF NOT EXISTS trigger_delete_price AFTER DELETE  ON  price
                            BEGIN
                                DELETE FROM dealsInDistances WHERE priceAID=OLD.id;
                                DELETE FROM dealsInDistances WHERE priceBID=OLD.id;
                                DELETE FROM dealsInDistancesSystems WHERE systemID=OLD.SystemID;
                            END; """)

        self.con.execute("""CREATE TRIGGER IF NOT EXISTS trigger_insert_price AFTER INSERT  ON  price
                            BEGIN
                                DELETE FROM dealsInDistancesSystems WHERE systemID=NEW.SystemID;
                            END; """)


        self.con.execute("""CREATE TRIGGER IF NOT EXISTS trigger_delete_dealsInDistancesSystems AFTER DELETE  ON  dealsInDistancesSystems
                            BEGIN
                                insert or ignore into dealsInDistancesSystems_queue (systemID) values(OLD.systemID);
                            END; """)


        ''' update db version'''
        dbVersion = self.getConfig('dbVersion')
        if dbVersion:
            dbVersion = int(dbVersion)
        else:
            dbVersion = DBVERSION
        ''' 01 to 02 '''
        if dbVersion < 2:
            print("update database from %s to 2" % dbVersion)
            self.con.execute("ALTER TABLE systems ADD COLUMN government INT;")
            self.con.execute("ALTER TABLE systems ADD COLUMN allegiance INT;")
    
            self.con.execute("ALTER TABLE stations ADD COLUMN government INT;")
            self.con.execute("ALTER TABLE stations ADD COLUMN allegiance INT;")
    
            self.con.execute("vacuum systems;")
            self.con.execute("vacuum stations;")

        self.con.commit()

    def optimizeDatabase(self):
        '''
        optimize all tables and indexes
        '''
        cur = self.cursor()

        cur.execute("select * from sqlite_master where type = 'table' or type = 'index' order by type")
        result = cur.fetchall()

        for i, table in enumerate(result):
            print("vacuum %s" % table["name"])
            if self.sendProcessMsg:
                self.sendProcessMsg("Optimize DB", i + 1, len(result) )

            self.con.execute("vacuum '%s'" % table["name"])

        cur.execute("select * from sqlite_master where type = 'table' order by rootpage")
        result = cur.fetchall()

        for table in result:
            print("analyze %s" % table["name"])
            if self.sendProcessMsg:
                self.sendProcessMsg("Analyze DB", i + 1, len(result) )

            cur.execute("analyze '%s'" % table["name"])

        self.con.commit()
        cur.close()
        self.setConfig('lastOptimizeDatabase', datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
    def cursor(self):
        cur = self.con.cursor()
        # cur.execute("PRAGMA synchronous = OFF")
        # cur.execute("PRAGMA journal_mode = MEMORY")
        # cur.execute("PRAGMA journal_mode = OFF")
        return cur


    def setConfig(self, var, val):

        self.__configCache[var] = val

        cur = self.cursor()

        cur.execute("insert or replace into config(var,val) values (?,?)", (var, val))
        self.con.commit()
        cur.close()

    def setFakePrice(self, id):
        if isinstance(id, int):
            self.con.execute("insert or ignore into fakePrice (priceID) values(?);", (id,))
            self.con.commit()

    def setIgnorePriceTemp(self, id):
        if isinstance(id, int):
            self.con.execute("insert or ignore into ignorePriceTemp (priceID) values(?);", (id,))
            self.con.commit()

    def cleanIgnorePriceTemp(self):
        self.con.execute("DELETE FROM ignorePriceTemp")
        self.con.commit()

        
    def getConfig(self, var):

        if self.__configCache.get(var):
            return self.__configCache.get(var)
        
        cur = self.cursor()
        cur.execute("select val from config where var = ? limit 1", (var,))
        result = cur.fetchone()
        cur.close()

        if result:
            self.__configCache[var] = result[0]
            return result[0]
        else:
            return False

    def getSystemIDbyName(self, system):

        system = system.lower()

        result = self.__systemIDCache.get(system)
        if result:
            return result
        
        cur = self.cursor()
        cur.execute("select id from systems where LOWER(System) = ? limit 1", (system,))

        result = cur.fetchone()
        cur.close()
        if result:
            self.__systemIDCache[system] = result[0]
            return result[0]

    def getShiptID(self, name):
        name = name.lower()

        cur = self.cursor()
        cur.execute("select id from ships where LOWER(Name)=? limit 1", (name,))
        result = cur.fetchone()
        cur.close()
        if result:
            return result[0]
        
    def getSystemname(self, SystemID):
        cur = self.cursor()
        cur.execute("select System from systems where id = ? limit 1", (SystemID,))

        result = cur.fetchone()
        cur.close()
        if result:
            return result[0]

    def getStationID(self, systemID, station):
        if not systemID or not station:
            return
        station = station.lower()
        key = "%d_%s" % (systemID, station) 

        result = self.__stationIDCache.get(key)
        if result:
            return result

        cur = self.cursor()
        cur.execute("select id from stations where systemID = ? and LOWER(Station) = ? limit 1", (systemID, station,))
        result = cur.fetchone()

        cur.close()
        if result:
            self.__stationIDCache[key] = result[0]
            return result[0]

    def getStationname(self, stationID):

        cur = self.cursor()
        cur.execute("select Station from stations where id = ? limit 1", (stationID,))
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

        if not stationID:
            return
        
        cur = self.cursor()
        cur.execute("select StarDist from stations where id = ? limit 1", (stationID,))
        result = cur.fetchone()
        cur.close()
        return result[0]

    def getItemID(self, itemname):

        result = self.__itemIDCache.get(itemname.lower())
        if result:
            return result
        
        cur = self.cursor()
        cur.execute("select id from items where LOWER(name) = ?  limit 1", (itemname.lower(),))
        result = cur.fetchone()

        cur.close()
        if result:
            self.__itemIDCache[itemname.lower()] = result[0]
            return result[0]

    def getAllItemNames(self):

        cur = self.cursor()

        cur.execute("select id ,name from items order by name")

        result = cur.fetchall()

        cur.close()
        if result:
            return result

    def getSystemData(self, systemID):
        cur = self.cursor()
        cur.execute("select * from systems where id = ? limit 1", (systemID,))
        result = cur.fetchone()
        cur.close()
        return result

    def getStationsFromSystem(self, system):

        if isinstance(system, int):
            systemID = system
        else:
            systemID = self.getSystemIDbyName(system)

        cur = self.con.cursor()
        cur.execute('SELECT id, Station FROM stations  where SystemID=? order by Station', (systemID,))
        rows = cur.fetchall()
        cur.close()
        stations = []
        for row in rows:
            stations.append([ row["id"], row["Station"] ])
        return stations
        
    def getStationData(self, stationID):
        cur = self.cursor()
        cur.execute("select * from stations where id = ? limit 1", (stationID,))
        result = cur.fetchone()
        cur.close()
        return result


    def getItemPriceDataByID(self, systemID, stationID, itemID):
        cur = self.cursor()
        cur.execute("select * from price where SystemID = ? and StationID = ? AND ItemID = ? limit 1", (systemID, stationID, itemID,))
        result = cur.fetchone()
        cur.close()
        return result

    def getItemPriceModifiedDate(self, systemID, stationID, itemID):
        cur = self.cursor()
        cur.execute("select modified from price where SystemID = ? and StationID = ? AND ItemID = ? limit 1", (systemID, stationID, itemID,))
        result = cur.fetchone()
        cur.close()
        if result:
            return result[0]
        return None

    def getSystemsInDistance(self, system, distance):
        # system is systemid or name

        if isinstance(system, int):
            systemID = system
        else:
            systemID = self.getSystemIDbyName(system)

        cur = self.cursor()

        # get pos data from systemA
        cur.execute("select * from systems  where id = ?  limit 1", (systemID,))
        systemA = cur.fetchone()

        cur.execute("select id, calcDistance(?, ?, ?, posX, posY, posZ ) AS dist, System  from systems where  dist <= ? order by dist", (systemA["posX"], systemA["posY"], systemA["posZ"], distance,))
        result = cur.fetchall()

        cur.close()
        return result

    def getDistanceFromTo(self, systemA, systemB):
        # system is systemid or name

        if not isinstance(systemA, int):
            systemA = self.getSystemIDbyName(systemA)

        if not isinstance(systemB, int):
            systemB = self.getSystemIDbyName(systemB)

        cur = self.cursor()


        cur.execute("""select calcDistance(a.posX, a.posY, a.posZ, b.posX, b.posY, b.posZ ) As dist FROM systems AS a
                    left JOIN systems AS b on b.id = ?
                    where a.id = ? """, (systemA, systemB,))
        
        result = cur.fetchone()
        cur.close()
        if result:
            return result[0]
        return result


    def getPricesInDistance(self, system, distance, maxStarDist, maxAgeDate, ItemID=None, onlyLpads=None, buyOrSell=None, allegiance=None, government=None):
        # system is systemid or name

        if isinstance(system, int):
            systemID = system
        else:
            systemID = self.getSystemIDbyName(system)
        cur = self.cursor()

        if distance == 0:
            distanceFromQuery = "FROM ( select * from systems where systems.id = '%s' ) as systems" % systemID
        else:
            # get pos data from systemA
            cur.execute("select * from systems  where id = ?  limit 1", (systemID,))
            systemA = cur.fetchone()
            distanceFromQuery = "FROM ( select calcDistance(%s, %s, %s, systems.posX, systems.posY, systems.posZ ) as dist, * from systems where dist <= %s ) as systems" % (systemA["posX"], systemA["posY"], systemA["posZ"], distance)
            
        itemFilter = ""
        if ItemID:
            itemFilter = "AND price.ItemID=%d" % ItemID

        padsizeFilter = ""
        if onlyLpads:
            padsizeFilter = " AND stations.max_pad_size = 'L' "

        buyOrSellFilter = ""
        if buyOrSell:
            if buyOrSell == 1:
                buyOrSellFilter = "AND price.StationSell > 0"
            elif buyOrSell == 2:
                buyOrSellFilter = "AND price.StationBuy > 0"

        allegianceFilter = ""
        if allegiance:
            allegianceFilter = "AND (systems.allegiance=%s OR stations.allegiance=%s)" % (allegiance, allegiance)

        governmentFilter = ""
        if government:
            governmentFilter = "AND ( systems.government=%s OR stations.government=%s)" % (government, government)
           
        cur.execute("""select *, price.modified AS age
                    %s
                    inner join price ON systems.id=price.SystemID

                    left JOIN items on items.id = price.ItemID
                    left JOIN stations on stations.id = price.StationID

                    left JOIN fakePrice AS fakePriceA ON price.id=fakePriceA.priceID
                    left JOIN ignorePriceTemp ON price.id=ignorePriceTemp.priceID

                    where
                        fakePriceA.priceID IS NULL
                        AND ignorePriceTemp.priceID IS NULL
                        %s
                        %s %s
                        %s %s
                        AND price.modified >= ?
                        AND stations.StarDist <= ?
                        """ % (distanceFromQuery, itemFilter, padsizeFilter, buyOrSellFilter, allegianceFilter, governmentFilter), (maxAgeDate, maxStarDist, ))
        
        result = cur.fetchall()

        cur.close()
        return result

    def getDealsFromTo(self, fromStation, toStation, maxAgeDate=datetime.utcnow() - timedelta(days=14), minStock=0):

        if isinstance(fromStation, int):
            fromStationID = fromStation
        else:
            return

        if isinstance(toStation, int):
            toStationID = toStation
        else:
            return

        cur = self.cursor()

        cur.execute('''select priceA.ItemID AS ItemID, priceB.StationBuy-priceA.StationSell AS profit,
                             priceB.StationBuy AS StationBuy,  priceA.StationSell AS StationSell,
                            priceA.id AS priceAid, priceB.id AS priceBid, priceA.Stock AS Stock,
                             items.name AS itemName,
                             stationA.Station AS fromStation,
                             stationB.Station AS toStation,
                             priceA.modified AS fromAge, priceB.modified AS toAge
                             
                    FROM price AS priceA

                    inner JOIN price AS priceB ON priceB.StationID=? AND priceA.ItemID=priceB.ItemID AND priceB.StationBuy > priceA.StationSell
                    left JOIN items on priceA.ItemID=items.id
                    left JOIN stations AS stationA on priceA.StationID=stationA.id
                    left JOIN stations AS stationB on priceB.StationID=stationB.id

                    left JOIN fakePrice AS fakePriceA ON priceA.id=fakePriceA.priceID
                    left JOIN fakePrice AS fakePriceB ON priceB.id=fakePriceB.priceID

                    left JOIN ignorePriceTemp AS ignorePriceTempA ON priceA.id=ignorePriceTempA.priceID
                    left JOIN ignorePriceTemp AS ignorePriceTempB ON priceB.id=ignorePriceTempB.priceID

                    WHERE

                        priceA.StationID=?
                        AND priceA.StationSell > 0
                        AND priceA.Stock > ?
                        AND priceA.modified >= ?
                        AND priceB.modified >= ?
                        AND fakePriceA.priceID IS NULL and fakePriceB.priceID IS NULL
                        AND ignorePriceTempA.priceID IS NULL and ignorePriceTempB.priceID IS NULL
                    order by profit DESC
                    ''', (toStationID, fromStationID, minStock, maxAgeDate, maxAgeDate))
        
        result = cur.fetchall()
        cur.close()

            
        return result


    def getDealsFromToSystem(self, fromStationID, toSystemID, maxStarDist=999999999, maxAgeDate=datetime.utcnow() - timedelta(days=14), minStock=0):


        cur = self.cursor()

        cur.execute('''select priceA.ItemID AS ItemID, priceB.StationBuy-priceA.StationSell AS profit,
                             priceB.StationBuy AS StationBuy,  priceA.StationSell AS StationSell,
                            priceA.id AS priceAid, priceB.id AS priceBid, priceA.Stock AS Stock,
                             items.name AS itemName,
                             stationA.Station AS fromStation,
                             stationB.Station AS toStation,
                             priceA.modified AS fromAge, priceB.modified AS toAge
                             
                    FROM price AS priceA

                    inner JOIN price AS priceB ON priceB.SystemID=? AND priceA.ItemID=priceB.ItemID AND priceB.StationBuy > priceA.StationSell
                    left JOIN items on priceA.ItemID=items.id
                    left JOIN stations AS stationA on priceA.StationID=stationA.id
                    left JOIN stations AS stationB on priceB.StationID=stationB.id

                    left JOIN fakePrice AS fakePriceA ON priceA.id=fakePriceA.priceID
                    left JOIN fakePrice AS fakePriceB ON priceB.id=fakePriceB.priceID

                    left JOIN ignorePriceTemp AS ignorePriceTempA ON priceA.id=ignorePriceTempA.priceID
                    left JOIN ignorePriceTemp AS ignorePriceTempB ON priceB.id=ignorePriceTempB.priceID

                    WHERE

                        priceA.StationID=?
                        AND priceA.StationSell > 0
                        AND stationB.StarDist <= ?
                        AND priceA.Stock > ?
                        AND priceA.modified >= ?
                        AND priceB.modified >= ?
                        AND fakePriceA.priceID IS NULL and fakePriceB.priceID IS NULL
                        AND ignorePriceTempA.priceID IS NULL and ignorePriceTempB.priceID IS NULL
                    order by profit DESC
                    ''', (toSystemID, fromStationID, maxStarDist, minStock, maxAgeDate, maxAgeDate))
        
        result = cur.fetchall()
        cur.close()
           
        return result


    def addSystemToDealsInDistancesCacheQueue(self, systemIDlist):
        cur = self.cursor()

        for system in systemIDlist:
            systemID = system["id"]
            cur.execute("INSERT or IGNORE INTO dealsInDistancesSystems_queue ( systemID ) values (?)", (systemID, ))

        self.con.commit()
        cur.close()


    def calcDealsInDistancesCache(self, systemIDlist, maxAgeDate, minTradeProfit=1000, dist=51):
        print("calcDealsInDistancesCache", len(systemIDlist))

        cur = self.cursor()

        for myPos, system in enumerate(systemIDlist):
            if self._active is not True:
                return

            if self.sendProcessMsg:
                self.sendProcessMsg("rebuild cache", myPos + 1, len(systemIDlist))

            systemID = system["id"]

            cur.execute("INSERT or IGNORE INTO dealsInDistancesSystems ( systemID, dist ) values (?, ? )", (systemID, dist))

            cur.execute("select * from systems  where id = ?  limit 1", (systemID,))
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

                            left JOIN ignorePriceTemp AS ignorePriceTempA ON priceA.id=ignorePriceTempA.priceID
                            left JOIN ignorePriceTemp AS ignorePriceTempB ON priceB.id=ignorePriceTempB.priceID

                        where
                            priceA.SystemID = ?
                            AND priceA.modified >= ?
                            AND priceA.StationSell > 0

                            AND priceB.StationBuy > priceA.StationSell
                            AND priceB.StationBuy - priceA.StationSell >= ?

                            AND fakePriceA.priceID IS NULL and fakePriceB.priceID IS NULL
                            AND ignorePriceTempA.priceID IS NULL and ignorePriceTempB.priceID IS NULL

                            """, (systemA["posX"], systemA["posY"], systemA["posZ"], maxAgeDate, dist, systemID, maxAgeDate, minTradeProfit))

            # delete system from queue
            cur.execute("DELETE FROM dealsInDistancesSystems_queue WHERE systemID=?", [systemID])

            self.con.commit()

    def calcDealsInDistancesCacheQueue(self):
        cur = self.cursor()

        cur.execute("select systemID AS id  from dealsInDistancesSystems_queue")
        systemList = cur.fetchall()
        if systemList:
            maxAgeDate = datetime.utcnow() - timedelta(days=14)  # TODO: save max age and use the max?
            self.calcDealsInDistancesCache(systemList, maxAgeDate)


    def checkDealsInDistancesCache(self):
        cur = self.cursor()

        cur.execute("""select * from dealsInDistances
                    left join price AS priceA ON priceA.id=dealsInDistances.priceAID
                    left join price AS priceB ON priceB.id=dealsInDistances.priceBID
                     where
                       priceB.StationBuy < priceA.StationSell
                       OR priceB.StationBuy IS NULL
                       OR priceA.StationSell IS NULL
                     """)

        result = cur.fetchone()


    def rebuildFullDistancesCache(self):
        cur = self.cursor()

        cur.execute(""" DELETE FROM dealsInDistances""")
        cur.execute(""" DELETE FROM dealsInDistancesSystems""")
        self.con.commit()

    def deleteDealsInDistancesSystems_queue(self):
        cur = self.cursor()

        cur.execute(""" DELETE FROM dealsInDistancesSystems_queue""")
        self.con.commit()

    def getBestDealsinDistance(self, system, distance, maxSearchRange, maxAgeDate, maxStarDist, minProfit, minStock, resultLimit=50, onlyLpads=None):
        if isinstance(system, int):
            systemID = system
        else:
            systemID = self.getSystemIDbyName(system)

        cur = self.cursor()

        # get pos data from systemA
        cur.execute("select * from systems  where id = ?  limit 1", (systemID,))
        systemA = cur.fetchone()

        padsizePart = ""
        if onlyLpads:
            padsizePart = " AND stationA.max_pad_size = 'L' "
            
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
                        %s
                    group by systemA.id
                    
                        """ % (padsizePart),
                         (systemA["posX"], systemA["posY"], systemA["posZ"], maxSearchRange, maxAgeDate, minStock, maxStarDist))

        # check the dealsIndistance cache
        cur.execute("""select id, calcDistance(?, ?, ?, posX, posY, posZ ) AS distn, dealsInDistancesSystems.dist
                             from TEAMP_selectSystemA AS systems
                             
                             LEFT join dealsInDistancesSystems  ON systems.id=dealsInDistancesSystems.SystemID
                             where  distn<=? AND dealsInDistancesSystems.dist is NULL group by id
                             
                             """, (systemA["posX"], systemA["posY"], systemA["posZ"], distance,))
        systemList = cur.fetchall()
        if systemList:
            if self.getConfig("option_calcDistance") != 1:
                self.calcDealsInDistancesCache(systemList, maxAgeDate)
            else:
                self.addSystemToDealsInDistancesCacheQueue(systemList)

        padsizePart = ""
        if onlyLpads:
            padsizePart = " AND stationB.max_pad_size = 'L' "


        cur.execute(""" select priceB.StationBuy-priceA.StationSell AS profit, priceA.id, priceB.id,
                        priceA.ItemID AS ItemID , priceB.StationBuy AS StationBuy, priceA.StationSell AS StationSell,
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

                        left JOIN ignorePriceTemp AS ignorePriceTempA ON priceA.id=ignorePriceTempA.priceID
                        left JOIN ignorePriceTemp AS ignorePriceTempB ON priceB.id=ignorePriceTempB.priceID

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
                        AND ignorePriceTempA.priceID IS NULL and ignorePriceTempB.priceID IS NULL
                        %s

                    order by profit DESC

                        limit ?

                        """ % (padsizePart), (distance, maxAgeDate, minStock, maxStarDist, maxAgeDate, maxStarDist, minProfit, resultLimit))

        result = cur.fetchall()

        cur.close()
        return result


    def getBestDealsFromStationInDistance(self, stationID, distance, maxAgeDate, maxStarDist, minProfit, minStock, reslultLimit=20, onlyLpads=None):

        cur = self.cursor()

        # get pos data from systemA
        cur.execute("select * from stations left join systems on systems.id=stations.SystemID  where stations.id = ?  limit 1", (stationID,))
        stationA = cur.fetchone()


        # check the dealsIndistance cache
        cur.execute("""select id, calcDistance(?, ?, ?, posX, posY, posZ ) AS distn, dealsInDistancesSystems.dist
                             from TEAMP_selectSystemA AS systems
                             
                             LEFT join dealsInDistancesSystems  ON systems.id=dealsInDistancesSystems.SystemID
                             where  distn<=? AND dealsInDistancesSystems.dist is NULL group by id
                             
                             """, (stationA["posX"], stationA["posY"], stationA["posZ"], distance,))
        systemList = cur.fetchall()
        if systemList:
            if self.getConfig("option_calcDistance") != 1:
                self.calcDealsInDistancesCache(systemList, maxAgeDate)
            else:
                self.addSystemToDealsInDistancesCacheQueue(systemList)

        padsizePart = ""
        if onlyLpads:
            padsizePart = " AND stationB.max_pad_size = 'L' "


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

                        left JOIN ignorePriceTemp AS ignorePriceTempA ON priceA.id=ignorePriceTempA.priceID
                        left JOIN ignorePriceTemp AS ignorePriceTempB ON priceB.id=ignorePriceTempB.priceID

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
                        AND ignorePriceTempA.priceID IS NULL and ignorePriceTempB.priceID IS NULL

                        %s
                        
                        order by profit DESC
                        limit ?
                        """ % (padsizePart),
                        (stationID, minStock, distance, maxAgeDate, maxAgeDate, maxStarDist, minProfit, reslultLimit))
        
        result = cur.fetchall()

        cur.close()
        return result

    def getPricesFrom(self, system, maxStarDist, maxAgeDate):
        # system is name, systemID or systemID list (maximal 999 systems)

        if isinstance(system, int):
            systemIDs = [system]
            systemBseq = "?"
        elif isinstance(system, list):
            # print(len(system))
            systemIDs = system
            systemBseq = ','.join(['?'] * len(systemIDs))
        else:
            systemIDs = [self.getSystemIDbyName(system)]
            systemBseq = "?"
        # print(systemBseq)

        # print(systemAID, systemBID)
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
                    """ % (systemBseq), systemIDs)

        result = cur.fetchall()

        cur.close()
        return result

    def getAllSystems(self):
        cur = self.cursor()
        
        cur.execute("""select System, id FROM Systems order by System """)

        result = cur.fetchall()

        cur.close()
        return result

    def getSystemsWithStationName(self, station):

        stationLikeStr = "%%%s%%" % station
    
        cur = self.cursor()

        cur.execute("""select System FROM Systems
                left join stations on Systems.id=stations.SystemID

                     where stations.Station LIKE ?
                     group by  Systems.id
                     order by System
                     """, (stationLikeStr,))

        result = cur.fetchall()

        cur.close()
        return result

    def getAllShipnames(self):
        cur = self.cursor()
        
        cur.execute("""select id, Name FROM ships order by Name """)

        result = cur.fetchall()

        cur.close()
        return result

    def getShipyardWithShip(self, shipID, systemID=None):

        cur = self.cursor()

        if systemID:
            cur.execute("select * from systems  where id = ?  limit 1", (systemID,))
            systemA = cur.fetchone()
        else:
            systemA = {"posX": 0.0, "posY": 0.0, "posZ": 0.0}


        cur.execute("""select *, calcDistance(?, ?, ?, posX, posY, posZ ) AS dist
                    ,shipyard.modifydate as age
                     FROM shipyard
                    left JOIN systems on systems.id = shipyard.SystemID
                    left JOIN stations on stations.id = shipyard.StationID
               /*     left JOIN ships on ships.id = shipyard.ShipID */
                where
                ShipID=?
                """, (systemA["posX"], systemA["posY"], systemA["posZ"], shipID, ))
        result = cur.fetchall()

        cur.close()
        return result
        
    def getSystemPaths(self):
        print("getSystemPaths")
        logPath = None
        if sys.platform == 'win32':
            from PySide import QtCore
            InstallLocation = None
            ''' Elite Dangerous (steam install) path '''
            # HKEY_LOCAL_MACHINE\SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall\Steam App 359320\InstallLocation
            settings = QtCore.QSettings(r"HKEY_LOCAL_MACHINE\SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall\Steam App 359320", QtCore.QSettings.NativeFormat)
            if settings:
                InstallLocation = settings.value("InstallLocation")

            ''' Elite Dangerous (steam on Win 10) path? '''
            if not InstallLocation:
                settings = QtCore.QSettings(r"HKEY_LOCAL_MACHINE\SOFTWARE\Wow6432Node\Valve\Steam\Apps\359320", QtCore.QSettings.NativeFormat)
                if settings:
                    InstallLocation = settings.value("InstallLocation")


            ''' Elite Dangerous (default install) path '''
            # https://support.frontier.co.uk/kb/faq.php?id=108
            if not InstallLocation:
                path = r'C:\Program Files (x86)\Frontier'
                if os.path.isdir(path):
                    InstallLocation = path


            if InstallLocation:
                productsList = ['FORC-FDEV-D-1010', 'FORC-FDEV-D-1008', 'FORC-FDEV-D-1003', 'FORC-FDEV-D-1002', 'FORC-FDEV-D-1001', 'FORC-FDEV-D-1000']

                for path in productsList:
                    mypath = os.path.join(InstallLocation, 'Products', path, 'Logs')
                    if os.path.isdir(mypath):
                        logPath = mypath
                        break
    
                if os.path.isdir(logPath):
                    self.setConfig('EliteLogDir', logPath)
                    # print("set %s" % logPath)


            ''' EDMarketConnector settings import '''
            # HKEY_CURRENT_USER\Software\Marginal\EDMarketConnector\outdir
            settings = QtCore.QSettings("Marginal", "EDMarketConnector")
            outdir = settings.value("outdir")
            if outdir and os.path.isdir(outdir):
                self.setConfig('EDMarkedConnector_cvsDir', outdir)
                # print("set %s" % outdir)

            ''' Slopeys ED BPC path import '''
            # HKEY_LOCAL_MACHINE\SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall\Slopeys ED BPC\UninstallString
            settings = QtCore.QSettings(r"HKEY_LOCAL_MACHINE\SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall\Slopeys ED BPC", QtCore.QSettings.NativeFormat)
            uninstallerPath = settings.value(r"UninstallString")
            if uninstallerPath:
                path = uninstallerPath.split("\\")
                path.pop()
                path.append("ED4.db")
                path = "\\".join(path)
                if os.path.isfile(path):
                    self.setConfig('BPC_db_path', path)
                    # print("set %s" % path)
                    
    def close(self):
        self.con.close()

    def getPowerID(self, power):
        power = power.lower()

        cur = self.cursor()
        cur.execute("select id from powers where LOWER(Name)=? limit 1", (power,))
        result = cur.fetchone()
        cur.close()
        if result:
            return result[0]

    def getAllPowers(self):
        cur = self.cursor()
        
        cur.execute("""select id, Name FROM powers order by Name """)

        result = cur.fetchall()

        cur.close()
        return result

    def getSystemsWithPower(self, powerID, systemID=None):
        cur = self.cursor()

        if systemID:
            cur.execute("select * from systems  where id = ?  limit 1", (systemID,))
            systemA = cur.fetchone()
        else:
            systemA = {"posX": 0.0, "posY": 0.0, "posZ": 0.0}

        cur.execute("""select *, calcDistance(?, ?, ?, posX, posY, posZ ) AS dist
                     FROM systems
                where
                power_control=?
                """, (systemA["posX"], systemA["posY"], systemA["posZ"], powerID,))
        result = cur.fetchall()

        cur.close()
        return result

    def getAllegianceID(self, allegiance, addUnknown=None):
        if not allegiance or allegiance == "None":
            return

        cur = self.cursor()
        cur.execute("select id from allegiances where LOWER(Name)=? limit 1", (allegiance.lower(),))

        result = cur.fetchone()

        if not result and addUnknown:
            cur.execute("insert or IGNORE into allegiances (Name) values (?) ", (allegiance,))
            cur.execute("select id from allegiances where Name=? limit 1", (allegiance,))

            result = cur.fetchone()

        cur.close()
        if result:
            return result[0]

    def getAllegiances(self):

        cur = self.cursor()
        cur.execute("select id, Name from allegiances ")

        result = cur.fetchall()

        cur.close()
        if result:
            return result


    def getGovernmentID(self, government, addUnknown=None):
        if not government or government == "None":
            return
        
        cur = self.cursor()
        cur.execute("select id from governments where LOWER(Name)=? limit 1", (government.lower(),))

        result = cur.fetchone()

        if not result and addUnknown:
            cur.execute("insert or IGNORE into governments (Name) values (?) ", (government,))
            cur.execute("select id from governments where Name=? limit 1", (government,))

            result = cur.fetchone()

        cur.close()
        if result:
            return result[0]


    def getGovernments(self):

        cur = self.cursor()
        cur.execute("select id, Name from governments ")

        result = cur.fetchall()

        cur.close()
        if result:
            return result

    def saveBookmark(self, name, routeList, typ):
        cur = self.cursor()
        cur.execute("insert into bookmarks (Name, Type) values (?, ?) ", (name, typ))
        if cur.lastrowid:
            BookmarkID = cur.lastrowid
            for i, hop in enumerate(routeList):
                cur.execute("insert into bookmarkChilds (BookmarkID, Pos, SystemID, StationID, ItemID) values (?, ?, ?, ?, ?) ",
                            (BookmarkID, i, hop['SystemID'], hop['StationID'], hop['ItemID'] ) )

        self.con.commit()
        cur.close()

    def deleteBookmark(self, bid):
        if not id:
            return

        cur = self.cursor()

        cur.execute("DELETE from bookmarkChilds where BookmarkID=? ", (bid, ) )
        cur.execute("DELETE from bookmarks where id=? ", (bid, ) )

        self.con.commit()
        cur.close()

    def getBookmarks(self):
        cur = self.cursor()
        cur.execute("""SELECT * FROM bookmarks order by id """)
        result = cur.fetchall()

        data = []
        for bookmark in result:
            cur.execute("""SELECT * FROM bookmarkChilds
                    left JOIN systems on systems.id = bookmarkChilds.SystemID
                    left JOIN stations on stations.id = bookmarkChilds.StationID
                    left JOIN items on items.id = bookmarkChilds.ItemID

                    where BookmarkID=?
                    order by BookmarkID, Pos
                     """, (bookmark['id'], ) )

            childresult = cur.fetchall()

            data.append({ 'id': bookmark['id'],
                          'Name': bookmark['Name'],
                          'Type': bookmark['Type'],
                          'childs': childresult,
                          })
        return data


    def getOutfittingCategoryID(self, category, addUnknown=None):
        if not category or category == "None":
            return

        cur = self.cursor()
        cur.execute("select id from outfitting_category where LOWER(category)=? limit 1", (category.lower(),))

        result = cur.fetchone()

        if not result and addUnknown:
            cur.execute("insert or IGNORE into outfitting_category (category) values (?) ", (category, ))
            cur.execute("select id from outfitting_category where category=? limit 1", (category, ))

            result = cur.fetchone()

        cur.close()
        if result:
            return result[0]


    def getOutfittingNameID(self, name, addUnknown=None):
        if not name:
            return

        cur = self.cursor()
        cur.execute("select id from outfitting_modulename where LOWER(modulename)=? limit 1", (name.lower(),))

        result = cur.fetchone()

        if not result and addUnknown:
            cur.execute("insert or IGNORE into outfitting_modulename (modulename) values (?) ", (name, ))
            cur.execute("select id from outfitting_modulename where modulename=? limit 1", (name, ))

            result = cur.fetchone()

        cur.close()
        if result:
            return result[0]


    def getOutfittingMountID(self, mount, addUnknown=None):
        if not mount:
            return

        cur = self.cursor()
        cur.execute("select id from outfitting_mount where LOWER(mount)=? limit 1", (mount.lower(),))

        result = cur.fetchone()

        if not result and addUnknown:
            cur.execute("insert or IGNORE into outfitting_mount (mount) values (?) ", (mount, ))
            cur.execute("select id from outfitting_mount where mount=? limit 1", (mount, ))

            result = cur.fetchone()

        cur.close()
        if result:
            return result[0]


    def getOutfittingGuidanceID(self, guidance, addUnknown=None):
        if not guidance:
            return

        cur = self.cursor()
        cur.execute("select id from outfitting_guidance where LOWER(guidance)=? limit 1", (guidance.lower(),))

        result = cur.fetchone()

        if not result and addUnknown:
            cur.execute("insert or IGNORE into outfitting_guidance (guidance) values (?) ", (guidance, ))
            cur.execute("select id from outfitting_guidance where guidance=? limit 1", (guidance, ))

            result = cur.fetchone()

        cur.close()
        if result:
            return result[0]
