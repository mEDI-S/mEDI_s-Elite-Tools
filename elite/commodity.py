# -*- coding: UTF8
'''
Created on 20.07.2015

@author: mEDI
'''
from elite.loader.maddavo import maddavo as maddavo

class commodity(object):
    '''
    classdocs
    '''
    con = None
    maddavoloader = maddavo()
    def __init__(self, con, maddavoloader=None):
        '''
        Constructor
        '''
        self.con = con
        self.maddavoloader = maddavoloader

    def getAllSellCommodFromStation(self, system, station):
        cur = self.con.cursor()
        if station:
            cur.execute('SELECT * FROM SC where SCStationSystem == "%s" and SCStationName == "%s" and SCStationSell > 0;' % (system, station))
        else:
            cur.execute('SELECT * FROM SC where SCStationSystem == "%s" and SCStationSell > 0;' % (system))
        rows = cur.fetchall()
        cur.close()
        return rows

    def getAllBuyCommodFromStation(self, system, station):
        cur = self.con.cursor()
        if station:
            cur.execute('SELECT * FROM SC where SCStationSystem == "%s" and SCStationName == "%s" and SCStationPrice > 0;' % (system, station))
        else:
            cur.execute('SELECT * FROM SC where SCStationSystem == "%s" and SCStationPrice > 0;' % (system))
            
        rows = cur.fetchall()
        cur.close()
        return rows

    def getAvailableDealsFromTo(self, fromSystem, fromStation, toSystem, toStation):
        fromItems = self.getAllBuyCommodFromStation(fromSystem, fromStation)
        toItems = self.getAllSellCommodFromStation(toSystem, toStation)
        if not fromItems or not toItems:
            return self.getAvailableDealsFromTo_maddavoloader(fromSystem, fromStation, toSystem, toStation)
#            return False
        # print(fromSystem,fromStation,toSystem,toStation,fromItems, toItems)
        itemlist = []
        for fromItem in fromItems:
            for toItem in toItems:
                if fromItem["SCStationCommod"] == toItem["SCStationCommod"]:
                    if fromItem["SCStationPrice"] < toItem["SCStationSell"]:
                        itemlist.append([fromItem, toItem])
                        # print(fromItem["SCStationCommod"], fromItem["SCStationPrice"], toItem["SCStationSell"], toItem["SCStationSell"]-fromItem["SCStationPrice"])
                    break

            
        def itemsSort(itemA, itemB):
            # print("--->",itemA)
            profitA = itemA[1]["SCStationSell"] - itemA[0]["SCStationPrice"]
            profitB = itemB[1]["SCStationSell"] - itemB[0]["SCStationPrice"]
            if profitA > profitB:
                return -1
            elif profitA < profitB:
                return 1
            else:
                return 0

        newlist = sorted(itemlist, cmp=itemsSort)
        # for item in newlist:
        #    print(item[1]["SCStationSell"]-item[0]["SCStationPrice"])
        return newlist

    def itemsSortPrice(self, itemA, itemB):
        # print("--->",itemA)
#            print(itemA, itemB)
        profitA = itemA[1]["buy"] - itemA[0]["sell"]
        profitB = itemB[1]["buy"] - itemB[0]["sell"]
#            print(profitA, profitB)
        if profitA > profitB:
            return -1
        elif profitA < profitB:
            return 1
        else:
            return 0

    def sortPricelist(self, itemlist):
#        return sorted(itemlist, cmp=self.itemsSortPrice)
        return sorted(itemlist, key=lambda items: items[2], reverse=True)
    
    def getAvailableDealsFromTo_maddavoloader(self, fromSystem, fromStation, toSystem, toStation):
        fromItems = self.maddavoloader.getItemsFromStation(fromSystem, fromStation)
        toItems = self.maddavoloader.getItemsFromStation(toSystem, toStation)
        if not fromItems or not toItems:
            return False
        # print(fromItems)
        itemlist = []
        for fromItem in fromItems:
#            print(fromItem)
            for toItem in toItems:
                if fromItem == toItem:
                    if fromItems[fromItem][1] > 0 and fromItems[fromItem][1] < toItems[toItem][0]:
                        profit = toItems[toItem][0] - fromItems[fromItem][1]
                        fitem = {"item":fromItem,"station":fromStation, "sell":fromItems[fromItem][1], "buy":fromItems[fromItem][0]}
                        titem = {"item":toItem,"station":toStation, "sell":toItems[toItem][1], "buy":toItems[toItem][0]}
                        itemlist.append([fitem, titem, profit])
                        #print(fitem,titem)
                        pass
#        print(itemlist)

#        newlist = sorted(itemlist, cmp=self.itemsSortPrice)
        newlist = sorted(itemlist, key=lambda items: items[2], reverse=True)

#        for item in newlist:
#            print(item[1]["buy"]-item[0]["sell"])
        return newlist
