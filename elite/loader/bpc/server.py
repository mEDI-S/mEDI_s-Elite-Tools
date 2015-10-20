'''
Created on 19.10.2015

@author: mEDI
'''

from datetime import datetime, timedelta
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

__APIUrl__ = "http://54.154.97.45/ED2/IF"


class loader(object):

    mydb = None
    
    def __init__(self, mydb):
        self.mydb = mydb


    def importData(self):
        
        lastUpdateTime = self.mydb.getConfig('last_BPCServer_import')
        updateStart = datetime.now()
        if lastUpdateTime:
            lastUpdateTime = datetime.strptime(lastUpdateTime, "%Y-%m-%d %H:%M:%S")
            # only update all 30 min
            if updateStart - timedelta(minutes=30) < lastUpdateTime:
                return
        else:
            lastUpdateTime = updateStart - timedelta(hours=48)

        td = updateStart - lastUpdateTime

        minutes = int(td.total_seconds() / 60) + 1

        
        apiurl = "%s/dumper.aspx" % (__APIUrl__)

        getRequest = {"id": minutes, }

        rawdata = self.sendAPIRequest(apiurl, getRequest)
        if rawdata:
            updateItems = []

            '''
            1565804,LHS 1393,          ,Brady Station,Foods,Coffee,1460,0,1297,0,,,,,19-Oct-2015 14:07,True<BR>
            1565801,LHS 1393,          ,Brady Station,Consumer Items,Domestic Appliances,631,437,418,4477,,,,,19-Oct-2015 14:07,True<BR>
            1565798,LHS 1393,          ,Brady Station,Chemicals,Hydrogen Fuel,147,94,90,32470,,,,,19-Oct-2015 14:07,True<BR>
            
            bpcid, system, ? , station, category, item, ?, buy, sell, stock, , , , , date, ?
            station=18496 coffee=15,Domestic Appliances=7, Hydrogen Fuel=2
            '''
            for item in rawdata.split("<BR>"):
                if item:
                    data = item.split(",")
                    system = data[1]
                    systemID = self.mydb.getSystemIDbyName(system)
                    if not systemID:
                        print("BPCServer: unknown system", item)
                        continue
                    
                    station = data[3]
                    stationID = self.mydb.getStationID(systemID, station)
                    if not stationID:
                        print("BPCServer: unknown station", item)
                        continue

                    itemname = data[5]
                    itemID = self.mydb.getItemID(itemname)
                    if not itemID:
                        print("BPCServer: unknown item", item)
                        continue

                    stationsell = data[7]
                    stationbuy = data[8]
                    stock = data[9]

                    datestr = data[14]
                    date = datetime.strptime(datestr, "%d-%b-%Y %H:%M")

                    updateItems.append( [stationbuy, stationsell, stock, date, stationID, itemID, date ] )



            if updateItems:
                pass
                cur = self.mydb.cursor()

                cur.executemany( "UPDATE price SET  StationBuy=?, StationSell=?, Stock=?, modified=?, source=2 where StationID=? AND ItemID=? AND modified<?", updateItems)
                if cur.rowcount:
                    print("BPCServer: update %d items" % cur.rowcount)
                cur.close()

        self.mydb.setConfig('last_BPCServer_import', updateStart.strftime("%Y-%m-%d %H:%M:%S"))


    def sendAPIRequest(self, apiurl, getRequest=None):

        url = apiurl
            
        if getRequest:
            getRequest = urlencode(getRequest)
            url = apiurl + "?" + getRequest

        print("BPCServer download: %s" % url)

        request = urllib2.Request(url)
        request.add_header('User-Agent', __useragent__)


        request.add_header('Accept-encoding', 'gzip')


        try:
            response = urllib2.urlopen(request)
        except:
            traceback.print_exc()
            return
        
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
            return result.decode('utf-8')
