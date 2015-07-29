# -*- coding: UTF8
'''
Created on 13.07.2015

@author: mEDI
'''
from elite.system import system as elitesystem

class rares(object):
    '''
    classdocs
    '''
    con = None
    conSystem = None
    __raresInSystemCache = {}

    def __init__(self, raresCon, systemCon):
        '''
        Constructor
        '''
        self.con = raresCon
        self.conSystem = systemCon
        self.system = elitesystem(self.conSystem)

    def getRaresListFitered(self,sunDistanc):
        
        cur = self.con.cursor()
#        cur.execute('SELECT * FROM Rares JOIN SysStation ON Rares.System==SysStation.SysStationSystem AND Rares.Station==SysStation.SysStationStation where SysStation.SysStationDist <=%d AND SysStation.SysStationDist >0 group by System;' % sunDistanc) 
        cur.execute('SELECT * FROM Rares where offline is NULL and illegal is NULL and permit is NULL ;') 
        data = cur.fetchall()
        cur.close()
        results = []
        for rSystem in data:
            dist = self.system.getStarDistFrom(rSystem["System"], rSystem["Station"])
            if  dist  and dist <= sunDistanc:
                results.append( [ rSystem["System"], dist ] )
                
        return results
    
    def getRaresInSystem(self,system):
        data = self.__raresInSystemCache.get(system)

        if data is None:
            cur = self.con.cursor()
#            cur.execute('SELECT * FROM Rares JOIN SysStation ON Rares.System==SysStation.SysStationSystem AND Rares.Station==SysStation.SysStationStation where Rares.System == "%s";' % system) 
            cur.execute('SELECT * FROM Rares where Rares.System == "%s";' % system) 
            data = cur.fetchall()
            cur.close()
            self.__raresInSystemCache[system] = data
        return data
