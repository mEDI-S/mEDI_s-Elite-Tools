'''
Created on 29.07.2015

@author: mEDI

import or update data from http://eddb.io/archive/v3/systems.json
'''
import os

from datetime import datetime, date, time, timedelta
import json

import gzip
import io

try:
    import urllib2
except ImportError:
    import urllib.request as urllib2

class loader(object):
    '''
    classdocs
    '''
    mydb = None


    def __init__(self, mydb):
        '''
        Constructor
        '''
        self.mydb = mydb

    def importData(self, filename=None):
        print("import %s" % filename)

        fp = open(filename)
        josnData = json.load(fp)
        fp.close()

        if not josnData: return
    
        cur = self.mydb.cursor()

        # build systemCache
        cur.execute("select id, System, modified from systems")
        result = cur.fetchall()
        systemCache = {}
        for system in result:
            systemCache[ system["System"].lower() ] = [system["id"], system["modified"]]
        result = None

        insertCount = 0
        updateCount = 0
        totalCount = 0
        updateSystem = []
        for system in josnData:
            totalCount += 1
            modified = datetime.fromtimestamp(system["updated_at"])

            if system["name"].lower() not in systemCache:
                insertCount += 1
                cur.execute("insert or IGNORE into systems (System, posX, posY, posZ, permit, modified) values (?,?,?,?,?,?) ",
                                        (system["name"] , float(system["x"]) , float(system["y"]), float(system["z"]), system["needs_permit"], modified))

            elif system["name"].lower() in systemCache and systemCache[ system["name"].lower() ][1] < modified:
                updateCount += 1
                updateSystem.append([system["name"], float(system["x"]) , float(system["y"]), float(system["z"]), system["needs_permit"], modified, systemCache[ system["name"].lower() ][0] ]) 


        if updateSystem:
            cur.executemany("update systems SET System=?, posX=?, posY=?, posZ=?, permit=?, modified=? where id is ?" , updateSystem)

        if updateCount or insertCount:
            print("update", updateCount, "insert", insertCount, "from", totalCount, "systems")

        self.mydb.con.commit()
        cur.close()


    def filenameFromUrl(self, url):

        filename = url.split("/").pop()

        return filename
    
    def update(self):
        eddbUrl_systems = "http://eddb.io/archive/v3/systems.json"
        storageDir = "db"

        filename = self.filenameFromUrl(eddbUrl_systems)
        filename = os.path.join(storageDir, filename)

        if os.path.isfile(filename):

            cDate = datetime.fromtimestamp(os.path.getmtime(filename))

            if cDate < datetime.now() - timedelta(hours=24):
                self.updateFromUrl(filename, eddbUrl_systems)

        else:  # download file not exists
            self.updateFromUrl(filename, eddbUrl_systems)

        #self.importData(filename)
#        self.updateFromUrl(filename, eddbUrl_systems)

    def updateFromUrl(self, filename, url):
        if not url: return

        print("download %s" % url)

        request = urllib2.Request(url)
        request.add_header('Accept-encoding', 'gzip')
        response = urllib2.urlopen(request)
        if response.info().get('Content-Encoding') == 'gzip':
            # print("gzip ok")
            buf = io.BytesIO(response.read())
            f = gzip.GzipFile(fileobj=buf)
        else:
            # print("none")
            f = response

        wfp = open(filename, "wb")
        wfp.write(f.read())
        wfp.close()
            
#        file,http = urllib.urlretrieve(url, filename)
#        print(response.info().items())
#        print( response.info().get('content-type').split("; ")[0] )

        if response.info().get('content-type').split("; ")[0] == "application/json":
            pass
            self.importData(filename)
        else:
            print("download error?")
            print(response.info().items())
