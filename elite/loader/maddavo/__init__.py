# -*- coding: UTF8

from elite.loader.maddavo import system
from elite.loader.maddavo import station
from elite.loader.maddavo import prices
from elite.loader.maddavo import items

from datetime import datetime, timedelta

def updateAll(mydb):
    lastUpdateTime = mydb.getConfig( 'lastMaddavoDownload' )
    if lastUpdateTime:
        lastUpdateTime = datetime.strptime(lastUpdateTime , "%Y-%m-%d %H:%M:%S")
        if lastUpdateTime > datetime.now() - timedelta(minutes=60):
            return

    print("update from maddavo")
        
    maddavo_station = station.loader(mydb)
    maddavo_station.update()

    maddavo_prices = prices.loader(mydb)
    maddavo_prices.update()
