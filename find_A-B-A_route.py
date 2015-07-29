# -*- coding: UTF8

from elite.db import db


import timeit
import sys
from datetime import datetime, date, time, timedelta

start = timeit.default_timer()

mydb = db()

'''
search best deal in my system for a A-B-A route
'''

startSystem = "ltt 9810"

searchModus = 2         # 1=bestDealFromMySystem 2=findBestDealInMyCircle
maxDist = 40            # max distace for B system
maxSearchRange = 80    # only used in mode 2
maxStarDist = 1300
maxAge = 14             # max data age in days
minLoopProfit = 3000
minTradeProfit = 1000    # only to minimize results (speedup)
minStock = 150000        # > 10000 = stable route > 50000 = extrem stable route and faster results

maxAgeDate = datetime.utcnow() - timedelta(days=maxAge)


# das ressultat von findDealsFromTo() muss einfacher durchsuchbar sein die mega for schleifen sind scheise

def findDealsFromTo(pricesListA, pricesListB):
    '''
    return a list with all avalibel and profitabel deals from listA to ListB
    '''
    dealItems = {}
    for itemA in pricesListA:
        if itemA["StationSell"] > 0 and itemA["Stock"] > minStock:
            #find buy station deal
            for itemB in pricesListB:
                if itemA["ItemID"] is itemB["ItemID"]:
                    #same item
                    profitAtoB = itemB["StationBuy"] - itemA["StationSell"]
                    if profitAtoB > 0 and profitAtoB > minTradeProfit:
                        #print(profitAtoB,itemA, "and", itemB)
                        if itemA["SystemID"] not in dealItems:
                            dealItems[itemA["SystemID"]] = {}
                        if itemB["StationID"] not in dealItems[itemA["SystemID"]]:
                            dealItems[itemA["SystemID"]][itemB["StationID"]] = {}

                        if itemA["StationID"] not in dealItems[itemA["SystemID"]][itemB["StationID"]]: 
                            dealItems[itemA["SystemID"]][itemB["StationID"]][itemA["StationID"]] = {}

                        if itemA["ItemID"] not in dealItems[itemA["SystemID"]][itemB["StationID"]][itemA["StationID"]]: 
                            dealItems[itemA["SystemID"]][itemB["StationID"]][itemA["StationID"]][itemA["ItemID"]] = []

                        dealItems[itemA["SystemID"]][itemB["StationID"]][itemA["StationID"]][itemA["ItemID"]] = [profitAtoB,itemA,itemB] 
    return dealItems

if searchModus is 1:
    pricesListA = mydb.getPricesFrom(startSystem,maxStarDist ,maxAgeDate)
    pricesListB = mydb.getPricesInDistance( startSystem, maxDist, maxStarDist, maxAgeDate)
    dealsListBtoA = findDealsFromTo(pricesListA,pricesListB )
    dealsListAtoB = findDealsFromTo(pricesListB,pricesListA ) 
#    dealsListBtoA = sorted(dealsListBtoA , key=lambda deal: deal[0],reverse=True )
#    dealsListAtoB = sorted(dealsListAtoB , key=lambda deal: deal[0],reverse=True )
elif searchModus is 2:
    start2 = timeit.default_timer()

    pricesListA = mydb.getPricesInDistance( startSystem, maxSearchRange, maxStarDist, maxAgeDate)

    stop = timeit.default_timer()
    print("getPricesInDistance",round(stop - start2, 3))
    start2 = timeit.default_timer()

    dealsListBtoA = findDealsFromTo(pricesListA,pricesListA )

    stop = timeit.default_timer()
    print("findDealsFromTo",round(stop - start2, 3))

#    dealsListAtoB,dealsListAtoB2 = findDealsFromTo(pricesListA,pricesListA )

    #dealsListBtoA = sorted(dealsListBtoA , key=lambda deal: deal[0],reverse=True )
    dealsListAtoB = dealsListBtoA

bestProfitList = []
def findTradingLoop_old(dealsListAtoB,dealsListBtoA):
    '''
    search a back loop deal with profiet
    '''
    for dealBtoAprofit,dealBtoA,dealBtoA_A in dealsListBtoA:
        #print(dealAtoB["SystemID"], systemID)
        #print(dealBtoAprofit,dealBtoA,dealBtoA_A)
        #find best back deal from system->station and calc total profit
        for dealAtoBprofit,dealAtoB,dealAtoB_A in dealsListAtoB:
            #print(dealBtoA["StationID"], dealAtoB["StationID"])
            if dealAtoB["StationID"] == dealBtoA_A["StationID"] and dealBtoA["StationID"] == dealAtoB_A["StationID"] : # StationBtoA:
                #stationDone[dealBtoA["StationID"]] = True
                #print(dealBtoAprofit+ dealAtoBprofit,dealBtoA,dealAtoB)
                profit = dealBtoAprofit + dealAtoBprofit
                if profit > minLoopProfit:
                    bestProfitList.append( [ profit ,dealBtoA,dealBtoA_A, dealAtoB,dealAtoB_A ] )
                break
    return bestProfitList

def findTradingLoop(dealsListAtoB,dealsListBtoA):
    '''
    search a back loop deal with profiet

    dealItems2[itemA["SystemID"]][itemB["StationID"]][itemA["StationID"]][itemA["ItemID"]] = [profitAtoB,itemA,itemB] 

    '''
    bestProfitList = []

    for systemID in dealsListAtoB:
        for stationID_B in dealsListAtoB[systemID]:
            for stationID_A in dealsListAtoB[systemID][stationID_B]:
                for itemA_ID in dealsListAtoB[systemID][stationID_B][stationID_A]:
            #search back part
                    for systemID_B in dealsListBtoA:
                        if dealsListBtoA[systemID_B].get(stationID_A) and dealsListBtoA[systemID_B][stationID_A].get(stationID_B):
                            for itemB_ID in dealsListBtoA[systemID_B][stationID_A][stationID_B]:
#    dealsListAtoB = sorted(dealsListAtoB , key=lambda deal: deal[0],reverse=True )
                
                                profit = dealsListAtoB[systemID][stationID_B][stationID_A][itemA_ID][0] + dealsListBtoA[systemID_B][stationID_A][stationID_B][itemB_ID][0]
                                if profit > minLoopProfit:
                                    bestProfitList.append( [ profit , dealsListAtoB[systemID][stationID_B][stationID_A][itemA_ID][1] , dealsListAtoB[systemID][stationID_B][stationID_A][itemA_ID][2], dealsListBtoA[systemID_B][stationID_A][stationID_B][itemB_ID][1], dealsListBtoA[systemID_B][stationID_A][stationID_B][itemB_ID][2] ] )

                
    return bestProfitList

start2 = timeit.default_timer()

bestProfitList = findTradingLoop(dealsListAtoB,dealsListBtoA)

print("findTradingLoop",round(timeit.default_timer() - start2, 3))

#sys.exit()
#bestProfitList = findTradingLoop(dealsListAtoB,dealsListBtoA)
print("results", len(bestProfitList))

## remove dubel entrys in mode 2
for deal in bestProfitList:
    for dealB  in bestProfitList[bestProfitList.index(deal):]:
        if deal[1]["SystemID"] is dealB[3]["SystemID"] and deal[1]["StationID"] is dealB[3]["StationID"] and deal[1]["ItemID"] is dealB[3]["ItemID"]:
            bestProfitList.remove(dealB)
            break
#            print("hit") 
        pass
print("results after cleaning", len(bestProfitList))

'''
calculate a rating "only profit is not the best option on long ways"
'''
for deal in bestProfitList:
    startDist = (deal[1]["StarDist"]+deal[3]["StarDist"])
   # rating = deal[0] - startDist/1.1
    rating = deal[0] +  minLoopProfit /  (startDist*0.015)
#    print(rating, deal[0], startDist)
    deal.append(rating)

'''
print results (best deals list)
'''
bestProfitList = sorted(bestProfitList , key=lambda deal: deal[5],reverse=True )
count = 0
for deal in bestProfitList:

    if searchModus is 1:
        dist = round(deal[1]["dist"],2)
    elif searchModus is 2:
        dist = round(mydb.getDistanceFromTo(deal[1]["SystemID"], deal[2]["SystemID"]),2)
    else:
        dist= -1

    if deal[1]["StarDist"] > maxStarDist or deal[2]["StarDist"] > maxStarDist or dist > maxDist:
        continue
    count += 1
    if count > 20:
         break

    print("%d. profit %d dist %s ly rating: %d" % (count, deal[0], dist, deal[5] ) )
    #print(deal[1])
    #print(deal[2])
    #print(deal[3])
    #print(deal[4])

    item = deal[1]
    profit = deal[2]["StationBuy"] - deal[1]["StationSell"]
    print("\t%s -> %d ls %s buy: %s %d cr (sell for: %d profit: %d cr) " % (item["System"],item["StarDist"],item["Station"],item["name"],deal[1]["StationSell"],deal[2]["StationBuy"],profit ) )
    item = deal[3]
    profit = deal[4]["StationBuy"] - deal[3]["StationSell"]
    print("\t%s -> %d ls %s buy: %s %d cr (sell for: %d profit: %d cr) " % (item["System"],item["StarDist"],item["Station"],item["name"],deal[3]["StationSell"],deal[4]["StationBuy"],profit ) )







stop = timeit.default_timer()
print(round(stop - start, 3))
print(sys.version)
