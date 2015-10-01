'''
Created on 29.07.2015

@author: mEDI

import or update data from http://eddb.io/archive/v3/commodities.json
'''
import os

from datetime import datetime, timedelta
import json

import gzip
import io
import sys

try:
    from _version import __buildid__, __version__, __builddate__, __toolname__, __useragent__
except ImportError:
    __buildid__ = "UNKNOWN"
    __version__ = "UNKNOWN"
    __builddate__ = "NONE"
    __toolname__ = "mEDI s Elite Tools"
    __useragent__ = '%s/%s (%s) %s(%s)' % (__toolname__.replace(" ", ""), __version__, sys.platform, __buildid__, __builddate__.replace(" ", "").replace("-", "").replace(":", ""))


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

        if not josnData:
            return

        cur = self.mydb.cursor()

        for item in josnData:

            itemID = self.mydb.getItemID(item["name"])

            if not itemID:
                print("insert new item %s" % item["name"])

                category = item["category"]["name"]
                if category == "Unknown":
                    category = None

                cur.execute("insert or IGNORE into items (name, category ) values (?,?) ",
                                                            (item["name"], category))


        self.mydb.con.commit()
        cur.close()


    def filenameFromUrl(self, url):

        filename = url.split("/").pop()

        return filename
    
    def update(self):
        eddbUrl_commodities = "http://eddb.io/archive/v3/commodities.json"
        storageDir = "db"

        filename = self.filenameFromUrl(eddbUrl_commodities)
        filename = os.path.join(storageDir, filename)

        if os.path.isfile(filename):

            cDate = datetime.fromtimestamp(os.path.getmtime(filename))

            if cDate < datetime.now() - timedelta(hours=1):
                self.updateFromUrl(filename, eddbUrl_commodities)

        else:  # download file not exists
            self.updateFromUrl(filename, eddbUrl_commodities)

#        self.updateFromUrl(filename, eddbUrl_commodities)

    def updateFromUrl(self, filename, url):
        if not url:
            return

        print("download %s" % url)

        request = urllib2.Request(url)
        request.add_header('User-Agent', __useragent__)
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
            
        if response.info().get('content-type').split("; ")[0] == "application/json":
            pass
            self.importData(filename)
        else:
            print("download error?")
            print(response.info().items())
