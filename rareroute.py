# -*- coding: UTF8

import sqlite3
import sys
import math
import timeit
from elite.system import system as elitesystem
from elite.rares import rares as eliterares
from elite.route import route as eliteroute
from elite.commodity import commodity as elitecommodity
from elite.loader.maddavo import maddavo as maddavo

maddavofilename ="db/all_Gen2015-07-21_030021_645620.prices"

mymaddavo = maddavo(maddavofilename)

#https://libraries.io/pypi/uncurl
# import numpy as np #http://www.lfd.uci.edu/~gohlke/pythonlibs/#numpy


# https://guillaume.segu.in/blog/code/487/optimizing-memory-usage-in-python-a-case-study/
# Microsoft Visual C++
#===============================================================================
# http://smira.ru/wp-content/uploads/2011/08/heapy.html
# from guppy import hpy #http://chase-seibert.github.io/blog/2013/08/03/diagnosing-memory-leaks-python.html
# hp = hpy()
# hp.setrelheap()
# h = hp.heap()
#===============================================================================
# print(h)
# sys.exit()
#===============================================================================
sellDist = 160
dbPath = "db/ED4.db"
raresDBPath = "db/rares.db"


start = timeit.default_timer()

con = sqlite3.connect(dbPath)
con.row_factory = sqlite3.Row    

conRares = sqlite3.connect(raresDBPath)
conRares.row_factory = sqlite3.Row    





mysystem = elitesystem(con)
myrares = eliterares(conRares, con)
myroute = eliteroute(con)
mycommodity = elitecommodity(con,mymaddavo)


def sellItems(system, route, muted=False):
    myTitle = True
#    print(" -->",indexstart)
    for oldsystem in route:
        if oldsystem._sellDone:
            continue
        dist = mysystem.calcDistance(system.systemName, oldsystem.systemName)
        if dist >= sellDist:
            if oldsystem._raresInSystem:
                oldsystem._sellDone = True
                if muted == False: 
                    if myTitle:
                        print("\t__Sell__")
                        myTitle = False
                    for item in oldsystem._raresInSystem:
                        print("\t\tItem: %s" % (item["Item"]))








# hp_start =  hp.heap()
##################
# options
##################
myStartSystem = "ltt 9810"
maxSunDistance = 1000
maxHops = 6
maxJumpDistance = 12.71
maxDeep = 10
minDeep = 9
useSlowMod=True # rerouting best route with all avalibel routes to optimize results
useSlowModOnStart = False # extrem slow deep 10 =8161314 routes =12gb ram usage optimal results

if useSlowModOnStart==True:
    useSlowMod=False


systemList = myrares.getRaresListFitered(maxSunDistance)  # # 600 iis broken endles loop?
print("calc with %d rare systems" % len(systemList))
myRaresRoute = []

startSystem = eliteroute(con, None, maxDeep,  maxJumpDistance, maxHops)
startSystem._availableSystemList = systemList
startSystem.systemName = myStartSystem  # Startsystem
startSystem.initSystem = startSystem
startSystem.calcAllRoutesFromSystem(useSlowModOnStart)


def getBestRouteFromResult(startSystem , useSlowMod=True, maxDeep=None):
    if not maxDeep :maxDeep = startSystem.calcRoutingDeep()
    elif maxDeep > startSystem.calcRoutingDeep():
        maxDeep = startSystem.calcRoutingDeep()
    allRoutesTop = []
    bestSellCount = None
    bestOption = None
    print("max deep" , maxDeep)
    print("hops", startSystem.getMinHops(maxDeep))
    print("star dist", startSystem.getMinStarDist(maxDeep))
    print("dist", startSystem.getMinDistFromBest(maxDeep))

    print("routes calculated", startSystem.calcRouteSum())
    
    allRoutes = startSystem.getAllRoutes(maxDeep)
    print("routes with maxdeep", len(allRoutes))
    
    while len(allRoutesTop) == 0 :
        if bestSellCount:  # its on loop 2 true "give the best != 0 sell cout route back"
            bestOption = True
        for endsystem in allRoutes:
            # print(endsystem.calcRoutingDeep())
            route = endsystem.getSystemsFromRoute()
            
            for system in route:  # reset sell status
                system._sellDone = None
                system._raresInSystem = None

            for system in route:
                if system._raresInSystem == None: system._raresInSystem = myrares.getRaresInSystem(system.systemName)
                sellItems(system, route, True)
            sellItems(route[0], route, True)  # sell on start== end system
        
            notSellCount = 0
            for oldsystem in route:
                if oldsystem._sellDone == None and oldsystem._raresInSystem:
                    notSellCount += 1
            # print(notSellCount)
            if notSellCount == 0 or (bestOption == True and notSellCount == bestSellCount):
                # top route can sell all items
                allRoutesTop.append(route)
                bestSellCount = notSellCount
            elif bestSellCount == None or bestSellCount > notSellCount:
                bestSellCount = notSellCount
                
    
    print("not sell count", bestSellCount)
    print("top routes", len(allRoutesTop))

    bestDist = None
    shortestStarDist = None
    backToStartDist = None
    bestBackToStartDist = None
    bestRating = None
    for route in allRoutesTop:
        totalDist = 0
        totalSunDist = 0
        syslist = ""
        for system in route:
            if system._hopsFromBefore : totalDist += system._dist
            if system.starDist : totalSunDist += system.starDist
            syslist += system.systemName
            syslist += ", "
    #    print(totalHops, totalSunDist, system.systemName ,syslist)
        backToStartDist = mysystem.calcDistance(system.systemName, route[0].systemName) 
        totalDist += backToStartDist  # add back to start distance
        #######################
        ## rating calculation
        #######################
        rating = backToStartDist * 2 + totalDist/len(route) + totalSunDist *1.5 / len(route)
#        print(backToStartDist, totalDist, totalSunDist , rating)

        if not shortestStarDist or shortestStarDist > totalSunDist:
            shortestStarDist = totalSunDist
        if not bestBackToStartDist or bestBackToStartDist > backToStartDist:
            bestBackToStartDist = backToStartDist
        if not bestDist or bestDist > totalDist:
            bestDist = totalDist

        if not bestRating or bestRating > rating:
            usedRoute = "used route: starDist %dls len %dly backtostart %dly" % (totalSunDist,totalDist,backToStartDist)
            bestRating = rating
            bestRoute = route

    print("best rating ", bestRating)
    if bestRoute:
        dist = bestRoute[len(bestRoute)-1].getStardistanceFromRoute()
        print("best star dist", shortestStarDist , "used route", dist, dist/ len(bestRoute) )
    else:
        print("best star dist", shortestStarDist , "noting used" )
    print("best dist", bestDist)
    print("best bestBackToStartDist", bestBackToStartDist)
    print(usedRoute)
  
    stop = timeit.default_timer()
    print(round(stop - start, 3))
    # calc all avalibel routes to the best route (optimize the path)
    # useSlowMod = False
    if useSlowMod == True:
        systemList = []
        for system in bestRoute:
            if myStartSystem != system.systemName:
                systemList.append([ system.systemName, system.starDist ])

        print("slow calc with %d rare systems" % len(systemList))

        startSystem = eliteroute(con, None, maxDeep,  maxJumpDistance, maxHops)
        startSystem._availableSystemList = systemList
        startSystem.systemName = myStartSystem  # Startsystem
        startSystem.initSystem = startSystem
        startSystem.calcAllRoutesFromSystem(True)  # slow mode calc
        # maxDeep = startSystem.calcRoutingDeep()
        # route = startSystem.getBestRoute(maxDeep)
        (bestRoute,bestSellCount,bestRating) = getBestRouteFromResult(startSystem, False, maxDeep)  # #recrusive run
    # sys.exit()
    # route = bestRoute
    return (bestRoute,bestSellCount,bestRating)

wonRating = None
wonRoute = None
for calcDeep in range(minDeep,maxDeep+1):
    (route,bestSellCount,bestRating) = getBestRouteFromResult(startSystem, useSlowMod, maxDeep=calcDeep)
    rating = bestRating * ((1+bestSellCount)* 1.2) + route[len(route)-1].deep * 10
    print("----------->", calcDeep,rating, bestSellCount, bestRating)
    if not wonRating or wonRating > rating:
        wonRating = rating
        wonRoute = route

print("won ----------->", wonRating)
route = wonRoute
################
# print my Resultat list
################

for system in route:  # reset sell status
    system._sellDone = None
    system._raresInSystem = None

totalDist = 0
for sysCount, system in enumerate(route):
    if system._raresInSystem == None: system._raresInSystem = myrares.getRaresInSystem(system.systemName)
    if system._dist :
        diststr = "%dly" % system._dist
        totalDist += system._dist
    else: diststr = "Start"
    print("%d. %s -> %s" % (sysCount + 1, diststr, system.systemName))

    if sysCount+1 < len(route):   #next sytsem for commodity deals
        nextSystem = route[sysCount+1]
    else:
        nextSystem = route[0]
        
    commodTrades = []
    if system._raresInSystem:
        print("\t__Buy__")

        for item in system._raresInSystem:
            print("\t\tRareitem: %s From Station: %s dist:%dls" % (item["Item"],item["Station"], mysystem.getStarDistFrom(system.systemName, item["Station"])))
            nextRareStations = myrares.getRaresInSystem(nextSystem.systemName)
            if not nextRareStations:    #endloop fallback
                commodTrades.append( [item["Station"], ""] )  
            else:
                for raresStation in nextRareStations:
                    if [item["Station"], raresStation["Station"]] in commodTrades:
                        pass
                    else:
                        commodTrades.append( [item["Station"], raresStation["Station"]] )  

                
    else:
        print("\tNo rares to buy")
        nextRareStations = myrares.getRaresInSystem(nextSystem.systemName)
        if nextRareStations:    #endloop fallback
            for raresStation in nextRareStations:
                commodTrades.append( ["", raresStation["Station"]] )  
        if commodTrades:
            print("\t__Buy__")

    for stationForCommod in commodTrades:
        #print(system.systemName,item["Station"],nextSystem.systemName,stationForCommod["Station"])
            #print(system.systemName,stationForCommod[0],nextSystem.systemName,stationTrade)
#        commodityDeals = mycommodity.getAvailableDealsFromTo(system.systemName,stationForCommod[0],nextSystem.systemName,stationForCommod[1])
        if not stationForCommod[0]: # no from station avalibel (start system have no rares) fallback and calc all stations in system
            commodityDeals = []
            for station in mysystem.getStationsFromSystem( system.systemName ):
                newcommodityDeals = mycommodity.getAvailableDealsFromTo_maddavoloader(system.systemName,station,nextSystem.systemName,stationForCommod[1])
                if newcommodityDeals: commodityDeals += newcommodityDeals
            commodityDeals = mycommodity.sortPricelist(commodityDeals)
        elif not stationForCommod[1]: # no to station avalibel (start system have no rares) fallback and calc all stations in system
            commodityDeals = []
            for station in mysystem.getStationsFromSystem( nextSystem.systemName ):
                newcommodityDeals = mycommodity.getAvailableDealsFromTo_maddavoloader(system.systemName,stationForCommod[0],nextSystem.systemName,station)
                if newcommodityDeals: commodityDeals += newcommodityDeals
            commodityDeals = mycommodity.sortPricelist(commodityDeals)
        else:
            commodityDeals = mycommodity.getAvailableDealsFromTo_maddavoloader(system.systemName,stationForCommod[0],nextSystem.systemName,stationForCommod[1])
            
        if commodityDeals == False:
            print("\t\t\tNo commodity data avalibel")
        elif not commodityDeals:
            print("\t\t\tNo com deals")
            
        else:
            for count, commodItem in enumerate(commodityDeals):
                profit = commodItem[1]["buy"]-commodItem[0]["sell"]
                print("\t\t\tCom: %s from: %s %dcr to: %s %dcr profit:%d" % (commodItem[0]["item"],commodItem[0]["station"],commodItem[0]["sell"], commodItem[1]["station"],commodItem[1]["buy"], profit ) )
                if count >= 2: break    # only show the first 3

# # sell items calc
    sellItems(system, route, False)



# back to start
dist = mysystem.calcDistance(system.systemName, route[0].systemName)
totalDist += dist
print("%d. back to %s -> %dly" % (sysCount + 2, route[0].systemName, round(dist)))
sellItems(route[0], route, False)

# # rest items
myTitle = True
for oldsystem in route:
    if oldsystem._sellDone:
        continue
    if oldsystem._raresInSystem:
        # oldsystem._sellDone = True
        if myTitle:
            print("\t__Sell Rest__")
            myTitle = False
        dist = mysystem.calcDistance(oldsystem.systemName, route[0].systemName)

        for item in oldsystem._raresInSystem:
            sellList = []
            for loopsystem in route:
                dist2 = mysystem.calcDistance(oldsystem.systemName, loopsystem.systemName)
                if dist2 >= sellDist:
                    sellList.append("%s -> %dly" % (loopsystem.systemName, dist2))
            print("\t\tItem: %s  buydist:%d or sell in: %s" % (item["Item"], dist, ", ".join(sellList)))


print("total loop len %dly" % totalDist)  

# myroute.calcRoutenRecrusion()


stop = timeit.default_timer()
print(round(stop - start, 3))
print(sys.version)
