'''
Created on 22.07.2015

@author: mEDI
'''

import sqlite3
from datetime import datetime, timedelta
import os

class loader(object):

    mydb = None
    con = None
    dbPath = None
    
    def __init__(self, mydb):
        self.mydb = mydb
        
    def connect_BPC_DB(self, dbPath=None):
        if dbPath:
            self.dbPath = dbPath
        else:
            self.dbPath = self.mydb.getConfig('BPC_db_path')        
            
        if not os.path.isfile(self.dbPath):
            print("Warning: config->BPC_db_path: '%s' do not exist" % self.dbPath)
            return
            

        self.con = sqlite3.connect(self.dbPath)
        self.con.row_factory = sqlite3.Row    


    def importData(self):
        self.connect_BPC_DB()

        if not self.con:
            return
        

        utcOffeset = datetime.now() - datetime.utcnow() 

        lastUpdateTime = self.mydb.getConfig('lastBPCimport')
        if lastUpdateTime:
            lastUpdateTime = datetime.strptime(lastUpdateTime , "%Y-%m-%d %H:%M:%S")
            # only update all 30 min
            if datetime.utcnow() - timedelta(minutes=30) < lastUpdateTime:
                return
            else:
                cur = self.con.cursor()
                cur.execute("SELECT max(SCStationLastUpdate) FROM `SC`  ;")
                lastDBupdate = cur.fetchone()[0]
                cur.close()
                if len(lastDBupdate) == 16:
                    lastDBupdate = datetime.strptime(lastDBupdate , "%Y-%m-%d %H:%M")
                    # print(type(lastDBupdate), lastDBupdate-utcOffeset, lastUpdateTime)
                    if lastDBupdate - utcOffeset <= lastUpdateTime  :
                        return

                

        else:
            lastUpdateTime = datetime.now() - timedelta(days=14)

        print("update from BPC")

        '''
        build key cache
        '''
        # get all items and build a cache (extrem faster as single querys) 
        mycur = self.mydb.cursor()
        mycur.execute("select SystemID, StationID, ItemID, modified from price")
        result = mycur.fetchall()
        itemCache = {}

        for item in result:
            cacheKey = "%d_%d_%d" % (item["SystemID"], item["StationID"], item["ItemID"])
            itemCache[cacheKey] = item["modified"]
        result = None

        
        '''
        start import
        '''
        self.connect_BPC_DB()

        cur = self.con.cursor()
        cur.execute("select * from SC where SCStationLastUpdate > ? ORDER BY `SCStationLastUpdate` DESC", (lastUpdateTime,))
        result = cur.fetchall()
        failCount = 0
        insertCount = 0
        updateItems = []
        newstEntry = None


        for price in result:
            systemID = self.mydb.getSystemIDbyName(price["SCStationSystem"])
            stationID = self.mydb.getStationID(systemID, price["SCStationName"])
            itemID = self.mydb.getItemID(price["SCStationCommod"])
            if not systemID or not stationID or not itemID:
                failCount += 1
                # extrem many fail entrys in bpc
                # print(price)
            else:
                cacheKey = "%d_%d_%d" % (systemID, stationID, itemID)
                # print(price["SCStationLastUpdate"] )
                if len(price["SCStationLastUpdate"]) == 16:
                    modifydate = datetime.strptime(price["SCStationLastUpdate"] , "%Y-%m-%d %H:%M")
                elif len(price["SCStationLastUpdate"]) > 16:
                    modifydate = datetime.strptime(price["SCStationLastUpdate"] , "%Y-%m-%d %H:%M:%S.%f")

                # convert BPC time (localtime) in UTC time
                if modifydate:
                    modifydate = modifydate - utcOffeset

                if not newstEntry:
                    newstEntry = modifydate


                if not itemCache.get(cacheKey):
                    # print(cacheKey,systemID, stationID, itemID,item)
                    insertCount += 1
                    mycur.execute("insert or IGNORE into price (SystemID, StationID, ItemID, StationBuy, StationSell, Dammand,Stock, modified, source) values (?,?,?,?,?,?,?,?,2) ",
                        (systemID, stationID, itemID, price["SCStationSell"] , price["SCStationPrice"] , 0 , price["SCStationStock"], modifydate))

                elif itemCache[cacheKey] < modifydate:
                    updateItems.append([ price["SCStationSell"] , price["SCStationPrice"] , price["SCStationStock"], modifydate, systemID, stationID, itemID ])

        if failCount:
            print("failCount", failCount)

        if updateItems:
            print("update items", len(updateItems), "insert items", insertCount)
            mycur.executemany("UPDATE price SET  StationBuy=?, StationSell=?,  Stock=?, modified=? ,source=2 where SystemID == ? AND StationID == ? AND ItemID == ?", updateItems)
        
        self.mydb.con.commit()
        mycur.close()
        cur.close()
        # set last updatetime to now()
        if newstEntry:   
            self.mydb.setConfig('lastBPCimport', newstEntry.strftime("%Y-%m-%d %H:%M:%S"))

        
