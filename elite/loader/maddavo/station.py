# -*- coding: UTF8
'''
Created on 23.07.2015

@author: mEDI

import or update db with system data from http://www.davek.com.au/td/station.asp

'''
import csv
from datetime import datetime, date, time

class loader(object):
    '''
    this loader insert or update
    '''

    mydb = None
    
    def __init__(self,mydb):
        '''
        Constructor
        '''
        self.mydb = mydb

    def importData(self,filename=None):
        if not filename: filename = 'db/station.csv'
        
        with open(filename) as csvfile:
#            reader = csv.DictReader(csvfile, quotechar="'",quoting=csv.QUOTE_NONE)
            simpelreader = csv.reader(csvfile, delimiter=',', quotechar="'")

            cur = self.mydb.cursor()
            mylist = list(simpelreader)
            fields = mylist[0]
            #print(fields)

            #get all stations 
            cur.execute( "select id, modified from stations" )
            result = cur.fetchall()
            stationCache= {}
            for station in result:
                stationCache[station["id"]] = station["modified"]
            result= None

            insertStations = []
            updateStations = []

            for row in mylist[1:]:
 
                system = row[fields.index("unq:name@System.system_id")].lower()
                station = row[fields.index("unq:name")].lower()
                starDist = int(row[fields.index("ls_from_star")])
                blackmarket = False
                if row[fields.index("blackmarket")].upper() == "Y": blackmarket = True

                padSize = row[fields.index("max_pad_size")].upper()

                market = False
                if row[fields.index("market")].upper() == "Y": market = True

                shipyard = False
                if row[fields.index("shipyard")].upper() == "Y": shipyard = True
                
                modifydate = datetime.strptime(row[fields.index("modified")].lower(),"%Y-%m-%d %H:%M:%S")

                outfitting = False
                if row[fields.index("outfitting")].upper() == "Y": outfitting = True

                rearm = False
                if row[fields.index("rearm")].upper() == "Y": rearm = True

                refuel = False
                if row[fields.index("refuel")].upper() == "Y": refuel = True

                repair = False
                if row[fields.index("repair")].upper() == "Y": repair = True

                systemID = self.mydb.getSystemIDbyName(system)

                if not systemID:
                    cur.execute( "insert or IGNORE into systems (System) values (?) ",
                                                               ( system) )
                    systemID = self.mydb.getSystemIDbyName(system)
 
                stationID = self.mydb.getStationID(systemID, station)

                if not stationID:
                    #collect for executemany
                    insertStations.append( [systemID, station, starDist, blackmarket, padSize, market, shipyard, outfitting, rearm, refuel, repair, modifydate]  )
                else:
                    if stationCache[stationID] < modifydate:
                        updateStations.append( [starDist, blackmarket, padSize,  market, shipyard,       outfitting,   rearm,   refuel,   repair,  modifydate, stationID] ) 

            if insertStations:
                cur.executemany( "insert or IGNORE into stations (SystemID, Station, StarDist, blackmarket, max_pad_size, market, shipyard, outfitting, rearm, refuel, repair, modified) values (?,?,?,?,?,?,?,?,?,?,?,?) ", insertStations)


            if updateStations:
                cur.executemany( "UPDATE stations SET  StarDist=?, blackmarket=?, max_pad_size=?, market=?, shipyard=?, outfitting=?, rearm=?, refuel=?, repair=?, modified=? where id is ?",updateStations)

            self.mydb.con.commit()
            cur.close()
