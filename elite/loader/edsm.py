# -*- coding: UTF8
'''
Created on 19.09.2015

http://www.edsm.net/api

@author: mEDI
'''

import json

import gzip
import io
import sys
import traceback

try:
    from _version import __buildid__ , __version__, __builddate__, __toolname__, __useragent__
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

__edsmAPIurl__ = 'http://www.edsm.net/api-v1'
__test__ = ''

class edsm(object):


    def __init__(self):
        pass
    
 
    def getSystemCoords(self, systemname):
        apiPath = "system"
        apiurl = "%s/%s" % (__edsmAPIurl__, apiPath)

        getRequest = {
                      "sysname" : systemname,
                      "coords": 1, 
                      }

        postRequest = None
        josnData = self.sendAPIRequest(apiurl, getRequest, postRequest)
#        print(josnData)

        if not josnData:
            return

        if isinstance(josnData, int):
            return

        if "error" in josnData:
            return

        if 'coords' in josnData and josnData['name'] == systemname:
            return josnData['coords']
        
    def submitDistances(self, targetSystemname, commander, refsystems ):
        apiPath = "submit-distances"
        apiurl = "%s/%s" % (__edsmAPIurl__, apiPath)
        postrequest = {
                       "data": {
                               "ver": 2,
#                               'test': __test__,
                               "commander": commander,
                               "p0":{ "name": targetSystemname },
                                "refs": refsystems,
                               }
                       }

#        print(postrequest)
        josnData = self.sendAPIRequest(apiurl, None, postrequest )
        print(josnData)

        if josnData:
            return josnData
            

    
    def sendAPIRequest(self, apiurl, getRequest=None, postRequest=None):

        url = apiurl
        if postRequest:
            postRequest = str( json.dumps(postRequest) ).encode('utf-8')
            
        if getRequest:
            getRequest = urlencode(getRequest)
            url = apiurl + "?" + getRequest

        request = urllib2.Request(url, postRequest)
        request.add_header('User-Agent', __useragent__)
        if postRequest:
            request.add_header('Content-Type', 'application/json; charset=utf-8')

        request.add_header('Accept', 'application/json; charset=utf-8')

        if postRequest:
            request.add_header('Content-Length', len(postRequest))

        request.add_header('Accept-encoding', 'gzip')

        print(apiurl, getRequest, postRequest)
#        return
        try:
            response = urllib2.urlopen(request)
        except:
            traceback.print_exc()
            e = sys.exc_info()
            return {"error":e}
        
        if response.info().get('Content-Encoding') == 'gzip':
            # print("gzip ok")
            buf = io.BytesIO(response.read())
            f = gzip.GzipFile(fileobj=buf)
        else:
            # print("none")
            f = response
        
        result = f.read()
#        print(result)
        if result:
            josnData = json.loads(result.decode('utf-8'))
            return josnData       
        
