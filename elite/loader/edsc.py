# -*- coding: UTF8
'''
Created on 14.09.2015

http://edstarcoordinator.com/api.html

@author: mEDI
'''


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

__edscAPIurl__ = 'http://edstarcoordinator.com/api.asmx'
__test__ = 'false'


class edsc(object):


    def __init__(self):
        pass
    

    def getSystemCoords(self, systemname):
        apiPath = "GetSystems"
        apiurl = "%s/%s" % (__edscAPIurl__, apiPath)
        postrequest = {"data": {
                               "ver": 2,
                               'test': __test__,
                               "outputmode": 2,
                               "filter": {
                                     "knownstatus": 1,
                                     "cr": 1,    # 1 or 5?
                                     "systemname": systemname,
                                     "date": '1990-01-01'
                                    }
                                }
                       }

        josnData = self.sendAPIRequest(apiurl, postrequest)
        if not josnData:
            return
        print(josnData)

        if "error" in josnData:
            return
        for system in josnData['d']['systems']:
            if system['name'] == systemname:
                # print(system)
                if system['coord']:
                    coord = {'x': system['coord'][0],
                             'y': system['coord'][1],
                             'z': system['coord'][2]}
                    return coord

    def submitDistances(self, targetSystemname, commander, refsystems ):
        apiPath = "SubmitDistances"
        apiurl = "%s/%s" % (__edscAPIurl__, apiPath)
        postrequest = {
                       "data": {
                                "ver": 2,
                                'test': __test__,
                                "commander": commander,
                                "p0": { "name": targetSystemname },
                                "refs": refsystems,
                               }
                    }

#        print(postrequest)
        josnData = self.sendAPIRequest(apiurl, postrequest)
        print(josnData)

        if josnData and "d" in josnData:
            return josnData['d']
        else:
            return josnData
            

    
    def sendAPIRequest(self, apiurl, postrequest):

        post = str( json.dumps(postrequest) ).encode('utf8')
#        print(post)
        request = urllib2.Request(apiurl, post)
        request.add_header('User-Agent', __useragent__)
        
        request.add_header('Content-Type', 'application/json; charset=utf-8')
        request.add_header('Accept', 'application/json; charset=utf-8')

        request.add_header('Content-Length', len(post))

        request.add_header('Accept-encoding', 'gzip')
        try:
            response = urllib2.urlopen(request)
        except:
            e = sys.exc_info()
            print("sendAPIRequest except", e)
            return {"error": e}
        
        if response.info().get('Content-Encoding') == 'gzip':
            # print("gzip ok")
            buf = io.BytesIO(response.read())
            f = gzip.GzipFile(fileobj=buf)
        else:
            # print("none")
            f = response
        
        result = f.read()
        josnData = json.loads(result.decode('utf-8'))
        
        return josnData
