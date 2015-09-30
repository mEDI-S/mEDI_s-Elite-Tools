# -*- coding: UTF8
'''
Created on 28.09.2015

@author: mEDI

EDDN on DynamoDB

http://edcodex.info/?m=tools&entry=133

'''

import json
from datetime import datetime, timedelta
import gzip
import io
import sys
import traceback
from elite.loader.eddn.EDDNimport import EDDNimport


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

__APIUrl__ = "https://43h3di62h7.execute-api.eu-west-1.amazonaws.com/beta/commodities"


def epochMicroseconds2datetime(epoch):
    if epoch:
        return datetime.fromtimestamp( int(epoch) / 1000000 )


def datetime2epochMicroseconds(dt):
    if dt:
        return int( dt.replace(tzinfo=None).timestamp() * 1000000 )


class loader(object):
    '''
    EDDN on DynamoDB loader
    '''


    def __init__(self, mydb):
        self.mydb = mydb
        self.EDDNimport = EDDNimport(self.mydb)

    
    def update(self):
        lastUpdateTime = self.mydb.getConfig( 'last_EDDN_DynamoDB_Update' )
        if lastUpdateTime:
            lastUpdateTime = datetime.strptime(lastUpdateTime, "%Y-%m-%d %H:%M:%S")
        else:
            lastUpdateTime = datetime.utcnow().replace(hour=0, minute=0, second=0)

        correntUpdateTime = datetime.utcnow() + timedelta(hours=2)


        if lastUpdateTime < correntUpdateTime - timedelta(minutes=10):
            print("update EDDN on DynamoDB")

            apiurl = "%s/%s" % (__APIUrl__, lastUpdateTime.strftime("%Y-%m-%d") )
            epochFrom = datetime2epochMicroseconds( lastUpdateTime )
            lastGatewayTime = None
            
            activeDonwload = True
            while activeDonwload:
#                activeDonwload = False
                getRequest = {"from": epochFrom, }
    
                correntUpdateTime = datetime.utcnow() + timedelta(hours=2)

                josnData = self.sendAPIRequest(apiurl, getRequest)
    
                if josnData:
                    if 'Count' in josnData and int(josnData['Count']) > 0:
#                        print(josnData['Count'])

                        for item in josnData['Items']:
                            self.EDDNimport.importData(item)
                            lastGTime = self.EDDNimport.convertStrptimeToDatetimeUTC(item["header"]["gatewayTimestamp"])

                            if not lastGatewayTime or lastGatewayTime < lastGTime:
                                lastGatewayTime = lastGTime
                    else:
#                        print("no Count")
                        activeDonwload = False


                    if 'LastEvaluatedTimestamp' in josnData:
                        epochFrom = int(josnData['LastEvaluatedTimestamp']) + 1
                    else:
#                        print("no LastEvaluatedTimestamp")
                        activeDonwload = False

                else:
                    print("no josnData")
                    print(josnData)
                    activeDonwload = False


            if correntUpdateTime:
                self.mydb.setConfig('last_EDDN_DynamoDB_Update', correntUpdateTime.strftime("%Y-%m-%d %H:%M:%S") )
            
#            elif epochFrom:
#                self.mydb.setConfig('last_EDDN_DynamoDB_Update', epochMicroseconds2datetime(epochFrom).strftime("%Y-%m-%d %H:%M:%S") )

            self.mydb.con.commit()
#            if lastGatewayTime:
#                lastGatewayTimeEpoch = datetime2epochMicroseconds(lastGatewayTime)
#                print(lastGatewayTimeEpoch, lastGatewayTime.isoformat())
#            print(epochFrom, epochMicroseconds2datetime(epochFrom).isoformat() )
#            print(datetime2epochMicroseconds(correntUpdateTime), correntUpdateTime.isoformat() )

    def sendAPIRequest(self, apiurl, getRequest=None, postRequest=None):

        url = apiurl
        if postRequest:
            postRequest = str( json.dumps(postRequest) ).encode('utf-8')
            
        if getRequest:
            getRequest = urlencode(getRequest)
            url = apiurl + "?" + getRequest

        print("download %s" % url)

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
            josnData = json.loads(result.decode('utf-8'))
            return josnData
