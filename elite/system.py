# -*- coding: UTF8
'''
Created on 13.07.2015

@author: mEDI
'''
import math
from sqlite3 import Cursor


class system(object):
    '''
    classdocs
    '''
    con = None
    
    __systemdatacache = {}

    def __init__(self, con):
        '''
        Constructor
        '''
        self.con = con

    def calcDistanceFromData(self, dataA, dataB):
        # #sqrt( (xA-xB)2 + (yA-yB)2 + (zA-zB)2 )
        if dataA is None or dataB is None:
            return

        return math.sqrt((dataA["SystemX"] - dataB["SystemX"]) ** 2 + (dataA["SystemY"] - dataB["SystemY"]) ** 2 + (dataA["SystemZ"] - dataB["SystemZ"]) ** 2)

    def getSystemData(self, name):
        
        data = self.__systemdatacache.get(name)
        if data is None:
            cur = self.con.cursor()
            cur.execute('SELECT * FROM System where SystemName == "%s";' % name) 
            data = cur.fetchone()
            cur.close()
            self.__systemdatacache[name] = data
        return data
    
    def calcDistance(self, fromsys, tosys):
#        print("dist calc from %s to %s" % (fromsys, tosys))

        dataA = self.getSystemData(fromsys)
        dataB = self.getSystemData(tosys)
        # 
        # print ("%s %s\n" % (dataA["SystemX"],dataB["SystemX"]))
        # 
        dist = self.calcDistanceFromData(dataA, dataB)
#        print(round(dist))
        return dist
    
    def getAllSystemnames(self):
        
        cur = self.con.cursor()
        cur.execute('SELECT SystemName FROM System group by Systemname ;')
        rows = cur.fetchall()
        cur.close()
        return rows

    def getStarDistFrom(self, system, station=None):
        cur = self.con.cursor()
        if station == None:
            cur.execute('SELECT SysStationDist FROM SysStation WHERE SysStationSystem == "%s" order by SysStationDist limit 1;' % system)
        else:
            cur.execute('SELECT SysStationDist FROM SysStation WHERE SysStationSystem == "%s" AND SysStationStation == "%s" limit 1;' % (system, station))

        res = cur.fetchone()
        if  res :
            cur.close()
            return res[0]
        cur.close()
        return None

    def getSystemsInDistance(self, startSystem, maxDist, systemList=None):
        '''
        return all systems in my distance
        '''
        if systemList == None:
            systemList = self.getAllSystemnames()

        systems = []
        sysInRange = 0
        for name in systemList:

            dist = self.calcDistance(startSystem , name[0])
            if dist:
                if dist < maxDist:
                    system = {"System" : name[0], "dist" : dist  }
                    systems.append(system)
                    
                    sysInRange = sysInRange + 1
                    # print("%s - %s " % (name["System"], round(dist)))
                 
#        systems = sorted(systems, key=lambda system: system["dist"], reverse=True)

        return systems
    
    def getStationsFromSystem(self,system):

        cur = self.con.cursor()
        cur.execute('SELECT SysStationStation FROM SysStation  where sysStationSystem == "%s" group by SysStationStation ;' % system)
        rows = cur.fetchall()
        cur.close()
        stations = []
        for row in rows:
            stations.append(row[0])
        return stations
