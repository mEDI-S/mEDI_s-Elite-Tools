# -*- coding: UTF8

from elite.loader.eddb import apiv4

from datetime import datetime, timedelta
import random


def updateAll(mydb):
    lastImport = mydb.getConfig( 'lastEDDBimport' )

    if lastImport:
        lastImport = datetime.strptime(lastImport, "%Y-%m-%d %H:%M:%S")

        ''' omly update max all 24h or next dey >5 plus random anti ddos
            "not all clients start update at same time
            hope it work ;)" '''
        updatetime = datetime.utcnow().replace(hour=3, minute=30)
        if lastImport < updatetime and datetime.utcnow() > updatetime and (datetime.utcnow().hour > 5 or random.randint(1, 10) == 1  ):
            pass
        else:
            return

    print("update from eddb")

    myapiv4 = apiv4.loader(mydb)
    myapiv4.importData()
    del myapiv4

    mydb.setConfig( 'lastEDDBimport', datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S") )
