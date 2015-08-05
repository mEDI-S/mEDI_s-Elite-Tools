# -*- coding: UTF8

import sys
import timeit

import elite

start = timeit.default_timer()
mydb = elite.db()



##################
# options
##################
myStartSystem = "ltt 9810"
maxSunDistance = 1500
sellDist = 160
maxHops = 6
maxJumpDistance = 12.71
maxDeep = 18
minDeep = 16
useSlowMod = True           # rerouting best route with all avalibel routes to optimize results
useSlowModOnStart = False   # extrem slow deep 10 =8161314 routes =12gb ram usage optimal results

# todo: elite.route.calcAllRoutesFromSystem is not optimal
if maxDeep > 19 and sys.maxint  <= 2147483647 and  (useSlowMod == True or useSlowModOnStart == True):
    print("warning: on 32bit systems no slowmod >deep 19 avalibel" )
    useSlowMod = False
    useSlowModOnStart = False

if minDeep >= maxDeep:
    minDeep = maxDeep
     
if useSlowModOnStart == True:
    useSlowMod = False







def sellItems(system, route, muted=False):
    myTitle = True
#    print(" -->",indexstart)
    for oldsystem in route:
        if oldsystem._sellDone:
            continue
        dist = mydb.getDistanceFromTo(system.systemID, oldsystem.systemID)
        if dist >= sellDist:
            if oldsystem._raresInSystem:
                oldsystem._sellDone = True
                if muted == False: 
                    if myTitle:
                        print("\t__Sell__")
                        myTitle = False
                    for item in oldsystem._raresInSystem:
                        print("\t\tItem: %s" % (item["Name"]))









myrares = elite.rares(mydb)
myroute = elite.route(mydb)

systemList = myrares.getRaresListFitered(maxSunDistance)
print("calc with %d rare systems" % len(systemList))
myRaresRoute = []

startSystem = elite.route(mydb, None, maxDeep, maxJumpDistance, maxHops)
startSystem._availableSystemList = systemList
startSystem.systemID = mydb.getSystemIDbyName(myStartSystem)  # Startsystem
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
            route = endsystem.getSystemsFromRoute()
            
            for system in route:  # reset sell status
                system._sellDone = None
                system._raresInSystem = None

            for system in route:
                if system._raresInSystem == None: system._raresInSystem = myrares.getRaresInSystem(system.systemID)
                sellItems(system, route, True)
            sellItems(route[0], route, True)  # sell on start== end system
        
            notSellCount = 0
            for oldsystem in route:
                if oldsystem._sellDone == None and oldsystem._raresInSystem:
                    notSellCount += 1
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
            syslist += "%s" % system.systemID
            syslist += ", "
    #    print(totalHops, totalSunDist, system.systemName ,syslist)
        backToStartDist = mydb.getDistanceFromTo(system.systemID, route[0].systemID) 
        totalDist += backToStartDist  # add back to start distance
        #######################
        # # rating calculation
        #######################
        rating = backToStartDist * 2 + totalDist / len(route) + totalSunDist * 1.5 / len(route)
#        print(backToStartDist, totalDist, totalSunDist , rating)

        if not shortestStarDist or shortestStarDist > totalSunDist:
            shortestStarDist = totalSunDist
        if not bestBackToStartDist or bestBackToStartDist > backToStartDist:
            bestBackToStartDist = backToStartDist
        if not bestDist or bestDist > totalDist:
            bestDist = totalDist

        if not bestRating or bestRating > rating:
            usedRoute = "used route: starDist %dls len %dly backtostart %dly" % (totalSunDist, totalDist, backToStartDist)
            bestRating = rating
            bestRoute = route

    print("best rating ", bestRating)
    if bestRoute:
        dist = bestRoute[len(bestRoute) - 1].getStardistanceFromRoute()
        print("best star dist", shortestStarDist , "used route", dist, dist / len(bestRoute))
    else:
        print("best star dist", shortestStarDist , "noting used")
    print("best dist", bestDist)
    print("best bestBackToStartDist", bestBackToStartDist)
    print(usedRoute)
  
    stop = timeit.default_timer()
    print(round(stop - start, 3))
    # useSlowMod = False
    #######################
    ## rerouting in slow mode
    ## calc all avalibel routes to the best route (optimize the path)
    #######################
    if useSlowMod == True:
        systemList = []
        for system in bestRoute:
            if myStartSystem != system.systemID:
                systemList.append([ system.systemID, system.starDist ])

        print("slow calc with %d rare systems" % len(systemList))

        startSystem = elite.route(mydb, None, maxDeep, maxJumpDistance, maxHops)
        startSystem._availableSystemList = systemList
        startSystem.systemID = mydb.getSystemIDbyName(myStartSystem)  # Startsystem
        startSystem.initSystem = startSystem
        startSystem.calcAllRoutesFromSystem(True)  # slow mode calc
        # maxDeep = startSystem.calcRoutingDeep()
        # route = startSystem.getBestRoute(maxDeep)
        (bestRoute, bestSellCount, bestRating) = getBestRouteFromResult(startSystem, False, maxDeep)  # #recrusive run

    return (bestRoute, bestSellCount, bestRating)

wonRating = None
wonRoute = None
for calcDeep in range(minDeep, maxDeep + 1):
    (route, bestSellCount, bestRating) = getBestRouteFromResult(startSystem, useSlowMod, maxDeep=calcDeep)
    rating = bestRating * ((1 + bestSellCount) * 1.2) + route[len(route) - 1].deep * 10
    print("----------->", calcDeep, rating, bestSellCount, bestRating)
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
    if system._raresInSystem == None: system._raresInSystem = myrares.getRaresInSystem(system.systemID)
    if system._dist :
        diststr = "%dly" % system._dist
        totalDist += system._dist
    else: diststr = "Start"
    print("%d. %s -> %s" % (sysCount + 1, diststr, mydb.getSystemname(system.systemID)))

    if sysCount + 1 < len(route):  # next sytsem for commodity deals
        nextSystem = route[sysCount + 1]
    else:
        nextSystem = route[0]
        
    commodTrades = []
    if system._raresInSystem:
        print("\t__Buy__")

        for item in system._raresInSystem:
            print("\t\tRareitem: %s From Station: %s dist:%dls" % (item["Name"], mydb.getStationname(item["StationID"]) , mydb.getStarDistFromStation(item["StationID"])))
            nextRareStations = myrares.getRaresInSystem(nextSystem.systemID)
            if not nextRareStations:  # endloop fallback
                commodTrades.append([item["StationID"], ""])  
            else:
                for raresStation in nextRareStations:
                    if [item["StationID"], raresStation["StationID"]] in commodTrades:
                        pass
                    else:
                        commodTrades.append([item["StationID"], raresStation["StationID"]])  

                
    else:
        print("\tNo rares to buy")
        nextRareStations = myrares.getRaresInSystem(nextSystem.systemID)
        if nextRareStations:  # endloop fallback
            for raresStation in nextRareStations:
                commodTrades.append(["", raresStation["StationID"]])  
        if commodTrades:
            print("\t__Buy__")

    for stationForCommod in commodTrades:
        if not stationForCommod[0]:  # no from station avalibel (start system have no rares) fallback and calc all stations in system
            commodityDeals = []
            for station in mydb.getStationsFromSystem(system.systemID):
                newcommodityDeals = mydb.getDealsFromTo(station[0], stationForCommod[1])
                if newcommodityDeals: commodityDeals += newcommodityDeals

        elif not stationForCommod[1]:  # no to station avalibel (start system have no rares) fallback and calc all stations in system
            commodityDeals = []
            for station in mydb.getStationsFromSystem(nextSystem.systemID):
                newcommodityDeals = mydb.getDealsFromTo(stationForCommod[0], station[0])
                if newcommodityDeals: commodityDeals += newcommodityDeals
        else:
            commodityDeals = mydb.getDealsFromTo(stationForCommod[0], stationForCommod[1])

        commodityDeals = sorted(commodityDeals, key=lambda items: items["profit"], reverse=True)
            
        if commodityDeals == False:
            print("\t\t\tNo commodity data avalibel")
        elif not commodityDeals:
            print("\t\t\tNo com deals")
            
        else:
            for count, commodItem in enumerate(commodityDeals):
                print("\t\t\tCom: %s from: %s %dcr to: %s %dcr profit:%d" % (commodItem["itemName"], commodItem["fromStation"], commodItem["stationSell"], commodItem["toStation"], commodItem["stationBuy"], commodItem["profit"]))
                if count >= 2: break  # only show the first 3

# # sell items calc
    sellItems(system, route, False)



# back to start
dist = mydb.getDistanceFromTo(system.systemID, route[0].systemID)
totalDist += dist
print("%d. back to %s -> %dly" % (sysCount + 2, mydb.getSystemname(route[0].systemID) , round(dist)))
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
        dist = mydb.getDistanceFromTo(oldsystem.systemID, route[0].systemID)

        for item in oldsystem._raresInSystem:
            sellList = []
            for loopsystem in route:
                dist2 = mydb.getDistanceFromTo(oldsystem.systemID, loopsystem.systemID)
                if dist2 >= sellDist:
                    sellList.append("%s -> %dly" % ( mydb.getSystemname(loopsystem.systemID) , dist2))
            print("\t\tItem: %s  buydist:%d or sell in: %s" % (item["Name"], dist, ", ".join(sellList)))


print("total loop len %dly" % totalDist)  



stop = timeit.default_timer()
print(round(stop - start, 3))
print(sys.version)
