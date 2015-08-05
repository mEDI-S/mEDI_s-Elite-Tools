# -*- coding: UTF8
'''
Created on 13.07.2015

@author: mEDI
'''

class rares(object):
    '''
    classdocs
    '''
    mydb = None
    __raresInSystemCache = {}

    def __init__(self, mydb):
        '''
        Constructor
        '''
        self.mydb = mydb

    def getRaresListFitered(self,sunDistanc):
        
        cur = self.mydb.cursor()

        cur.execute('''SELECT * FROM rares
                            left join stations on rares.StationID=stations.id
                            left join systems ON rares.SystemID=systems.id
                            where offline != "Y" and illegal != "Y" 
                            AND systems.permit != 1
                            AND stations.StarDist <= ?''', (sunDistanc,)) 

        data = cur.fetchall()
        cur.close()
        results = []
        for rSystem in data:
            results.append( [ rSystem["SystemID"], rSystem["StarDist"] ] )
                
        return results
    
    def getRaresInSystem(self,system):
        data = self.__raresInSystemCache.get(system)

        if data is None:
            cur = self.mydb.cursor()
#            cur.execute('SELECT * FROM Rares JOIN SysStation ON Rares.System==SysStation.SysStationSystem AND Rares.Station==SysStation.SysStationStation where Rares.System == "%s";' % system) 
            cur.execute('SELECT * FROM rares where SystemID = ?', (system,)) 
            data = cur.fetchall()
            cur.close()
            self.__raresInSystemCache[system] = data
        return data
