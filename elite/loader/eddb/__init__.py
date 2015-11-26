# -*- coding: UTF8

from elite.loader.eddb import apiv4

from datetime import datetime, timedelta
import random
import traceback


def updateAll(mydb):
    lastImport = mydb.getConfig( 'lastEDDBimport' )

    if lastImport:
        lastImport = datetime.strptime(lastImport, "%Y-%m-%d %H:%M:%S")

        ''' omly update max all 24h or next dey >5 plus random anti ddos
            "not all clients start update at same time
            hope it work ;)" '''
        updatetime = datetime.utcnow().replace(hour=3, minute=30)
        if lastImport < updatetime and datetime.utcnow() > updatetime and random.randint(1, 10) == 1:
            pass
        else:
            return

    print("update from eddb")

    try:
        myapiv4 = apiv4.loader(mydb)
        myapiv4.importData()
        del myapiv4
    except:
        traceback.print_exc()
        mydb.setConfig('plugin_eddb', 0)
        print("disable eddb loader!")
    
    mydb.setConfig( 'lastEDDBimport', datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S") )
