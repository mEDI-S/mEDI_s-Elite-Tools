# -*- coding: UTF8
'''
Created on 13.07.2015

@author: mEDI
'''


class rares(object):

    mydb = None
    __raresInSystemCache = {}

    def __init__(self, mydb):

        self.mydb = mydb

    def getRaresListFitered(self, sunDistanc):
        
        cur = self.mydb.cursor()

        cur.execute('''SELECT * FROM rares
                            left join stations on rares.StationID=stations.id
                            left join systems ON rares.SystemID=systems.id
                            where offline != "Y" and illegal != "Y"
                            AND systems.permit != 1
                            AND stations.StarDist <= ?''', (sunDistanc, ))

        data = cur.fetchall()
        cur.close()
        results = []
        for rSystem in data:
            results.append( [ rSystem["SystemID"], rSystem["StarDist"] ] )
                
        return results
    
    def getRaresInSystem(self, system):
        data = self.__raresInSystemCache.get(system)

        if data is None:
            cur = self.mydb.cursor()
            cur.execute('SELECT * FROM rares where SystemID = ?', (system,))
            data = cur.fetchall()
            cur.close()
            self.__raresInSystemCache[system] = data
        return data

    def getRaresList(self, sunDistanc=9999999999999):
        
        cur = self.mydb.cursor()

        cur.execute('''SELECT * FROM rares
                            left join stations on rares.StationID=stations.id
                            left join systems ON rares.SystemID=systems.id
                            where offline != "Y"
                            /*AND illegal != "Y"
                            AND systems.permit != 1*/
                            AND stations.StarDist <= ?''', (sunDistanc, ))

        result = cur.fetchall()
        cur.close()
                
        return result

    def updatePrice(self, rID, price):
        if not rID or not price:
            return

        cur = self.mydb.cursor()
        cur.execute("UPDATE rares SET  Price=? where id=?", (price, rID) )
        cur.close()
        return True

    def updateName(self, rID, name):
        if not rID or not name:
            return

        cur = self.mydb.cursor()
        cur.execute("UPDATE rares SET  Name=? where id=?", (name, rID) )
        cur.close()

        return True

    def updateMaxAvail(self, rID, MaxAvail):
        if not rID:
            return

        cur = self.mydb.cursor()
        cur.execute("UPDATE rares SET  MaxAvail=? where id=?", (MaxAvail, rID) )
        cur.close()
        return True

    def updateComment(self, rID, comment):
        if not rID:
            return

        cur = self.mydb.cursor()
        cur.execute("UPDATE rares SET  comment=? where id=?", (comment, rID) )
        cur.close()
        return True
