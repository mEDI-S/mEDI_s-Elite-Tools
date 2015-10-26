# -*- coding: UTF8
'''
Created on 26.10.2015

@author: mEDI
'''

import json
import gzip
import io
import sys
import traceback


try:
    from _version import __buildid__, __version__, __builddate__, __toolname__, __useragent__
except ImportError:
    __buildid__ = "UNKNOWN"
    __version__ = "UNKNOWN"
    __builddate__ = "NONE"
    __toolname__ = "mEDI s Elite Tools"
    __useragent__ = '%s/%s (%s) %s(%s)' % (__toolname__.replace(" ", ""), __version__, sys.platform, __buildid__, __builddate__.replace(" ", "").replace("-", "").replace(":", ""))

try:
    ''' python 2.7'''
    import urllib2
    from urllib import urlencode
except ImportError:
    ''' python 3.x'''
    import urllib.request as urllib2
    from urllib.parse import urlencode

__APIUrl__ = "https://eddb.io"



class eddbweb(object):


    def __init__(self):
        pass
    
    def getEDDBEditStationUrl(self, system, station):
        #https://ross.eddb.io/station/update/16079
        stationID = self.getEDDBStationID(system, station)
        if stationID:
            url = "https://ross.eddb.io/station/update/%s" % (stationID)
            return url


    def getEDDBEditSystemUrl(self, system):
        #https://ross.eddb.io/system/update/10392
        stationID = self.getEDDBSystemID(system)
        if stationID:
            url = "https://ross.eddb.io/system/update/%s" % (stationID)
            return url


    def getEDDBSystemID(self, system):
        josnData = self.getEDDBSystemData(system)
        if josnData:
            if len(josnData) > 1:
                print("eddbweb warning: more as one result system")
            if 'id' in josnData[0]:
                return josnData[0]['id']

                
    def getEDDBStationID(self, system, station):
        josnData = self.getEDDBSystemData(system)
        if josnData:
            for systemdata in josnData:
                if 'stations' in systemdata:
                    for stationdata in systemdata['stations']:
                        if stationdata['name'] == station:
                            return stationdata['id']


    def getEDDBSystemData(self, system):
        getRequest = {"system[multiname]": system, "expand": "stations" }
        apiurl = "%s/system/search" % (__APIUrl__)
        josnData = self.sendAPIRequest(apiurl, getRequest)
        #print(josnData)
        return josnData


    def sendAPIRequest(self, apiurl, getRequest=None, postRequest=None):

        url = apiurl
        if postRequest:
            postRequest = str( json.dumps(postRequest) ).encode('utf-8')
            
        if getRequest:
            getRequest = urlencode(getRequest)
            url = apiurl + "?" + getRequest

        print("webeddb download %s" % url)

        request = urllib2.Request(url, postRequest)
        request.add_header('User-Agent', __useragent__)
        if postRequest:
            request.add_header('Content-Type', 'application/json; charset=utf-8')

        request.add_header('Accept', 'application/json; charset=utf-8')

        if postRequest:
            request.add_header('Content-Length', len(postRequest))

        request.add_header('Accept-encoding', 'gzip')

#        print(apiurl, getRequest, postRequest)

        try:
            response = urllib2.urlopen(request)
        except:
            traceback.print_exc()
            return
        
        if response.info().get('Content-Encoding') == 'gzip':
#            print("gzip ok")
            buf = io.BytesIO(response.read())
            f = gzip.GzipFile(fileobj=buf)
        else:
            # print("none")
            f = response
        
        result = f.read()
#        print(result)
        if result:
            try:
                josnData = json.loads(result.decode('utf-8', 'replace'))
            except:
                traceback.print_exc()
                return

            return josnData
