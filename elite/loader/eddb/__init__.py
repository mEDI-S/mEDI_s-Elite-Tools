# -*- coding: UTF8

from elite.loader.eddb import items
from elite.loader.eddb import systems
from elite.loader.eddb import stations

from datetime import datetime, timedelta
import random

def updateAll(mydb):
    lastImport = mydb.getConfig( 'lastEDDBimport' )

    if lastImport:
        lastImport = datetime.strptime(lastImport , "%Y-%m-%d %H:%M:%S")

        ''' omly update all 24h or next dey >5 plus random anti ddos  
            "not all clients start update at same time
            hope it work ;)" '''

        if lastImport.day == datetime.now().day and lastImport.hour < 5 and random.randint(1, 10) == 1 :
            pass
        elif lastImport > datetime.now() - timedelta(hours=24):
            return

    print("update from eddb")

    eddb_commodities = items.loader(mydb)
    eddb_commodities.update()
    del eddb_commodities
    
    eddb_systems = systems.loader(mydb)
    eddb_systems.update()
    del eddb_systems

    eddb_stations = stations.loader(mydb)
    eddb_stations.update()
    del eddb_stations

    mydb.setConfig( 'lastEDDBimport', datetime.now().strftime("%Y-%m-%d %H:%M:%S") )
