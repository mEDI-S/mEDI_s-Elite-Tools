# -*- coding: UTF8
'''
Created on 23.07.2015

@author: mEDI

import or update db with system data from http://www.davek.com.au/td/station.asp

'''
import os
import csv
from datetime import datetime, date, time, timedelta

from StringIO import StringIO
import gzip
import urllib2

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

        print("update stations from %s" % filename)
        
        with open(filename) as csvfile:

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
                station = row[fields.index("unq:name")]
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

    def filenameFromUrl(self, url):

        filename = url.split("/").pop()

        return filename
    
    def update(self):
        systems_url = "http://www.davek.com.au/td/station.asp"
        storageDir = "db"

        filename = "station.csv"
        filename = os.path.join(storageDir, filename)

        if os.path.isfile(filename):

            cDate = datetime.fromtimestamp(os.path.getmtime(filename))

            if cDate < datetime.now() - timedelta(hours=24):
                self.updateFromUrl(filename, systems_url)
            else:
                self.importData(filename)

        else:  # download file not exists
            self.updateFromUrl(filename, systems_url)

#        self.importData(filename)
#        self.updateFromUrl(filename, eddbUrl_systems)

    def updateFromUrl(self, filename, url):
        if not url: return

        print("download %s" % url)

        request = urllib2.Request(url)
        request.add_header('Accept-encoding', 'gzip')
        response = urllib2.urlopen(request)
        if response.info().get('Content-Encoding') == 'gzip':
            # print("gzip ok")
            buf = StringIO(response.read())
            f = gzip.GzipFile(fileobj=buf)
        else:
            # print("none")
            f = response

        wfp = open(filename, "wb")
        wfp.write(f.read())
        wfp.close()
            

        if response.info().get('content-type').split("; ")[0] == "application/octet-stream":
            pass
            self.importData(filename)
        else:
            print("download error?")
            print(response.info().items())
