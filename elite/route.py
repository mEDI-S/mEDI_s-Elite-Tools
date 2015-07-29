# -*- coding: UTF8
'''
Created on 13.07.2015

@author: mEDI
'''

from elite.system import system as elitesystem
#from elite.rares import rares as eliterares

# from elite.route import route as eliteroute

    
class route(object):
    '''
    classdocs
    '''
    #__slots__ = ["bla"]
    #bla =1
    maxHops = 6
    maxJumpDistance = 12.71
    maxDeep = 20
    # die kürzeste route is nicht die beste wegen den optimalen preisen bei > 150ly

    systemName = None
    _before = None
#    _initSystem = None  # startsystem
    initSystem = None  # startsystem
    possibleSystems = []
    _raresInSystem = None
    _availableSystemList = None
    _sellDone = None
    starDist = None
    deep = 1
    _hopsFromBefore = None
    _dist = None  # distance to before system
    con = None
    rares = None
    system = None

    def __init__(self, con, before=None, maxDeep=None,  maxJumpDistance=None, maxHops=None):
        # super(route, self).__init__()
        self.con = con
        self.possibleSystems = []
        self._before = before
        if before:
            self.initSystem = before.initSystem
            self.system = self.initSystem.system 
            self.maxHops = self.initSystem.maxHops 
            self.maxDeep = self.initSystem.maxDeep 
            self.maxJumpDistance = self.initSystem.maxJumpDistance 

#            self.rares =  before.rares
        else:
            self.system = elitesystem(self.con)
            self.maxDeep = maxDeep
            self.maxHops = maxHops
            self.maxJumpDistance = maxJumpDistance
#            self.rares = eliterares(con)

    def addPossibleSystems(self, system, dist, startdist, systemList):
#    def addPossibleSystems(self, system, dist,  rarelist):
        newroute = route(self.con, self)
        newroute._availableSystemList = systemList
        newroute._dist = dist
        newroute.systemName = system
        newroute.starDist = startdist
        newroute.deep = self.deep + 1
        newroute._hopsFromBefore = int(round((dist / self.maxJumpDistance) + 0.5)) 

        # new = {"System":system, "dist":dist, "rareslist":rarelist, "nextroute":route(self.con)}
        self.possibleSystems.append(newroute)

    def setMaxHops(self, hops):
        self.maxHops = hops

    def setmaxJumpDistance(self, dist):
        self.maxJumpDistance = dist

    def calcRoutingDeep(self):
        MaxDeep = self.deep

        for nextsystem in self.possibleSystems:
            nMaxDeep = nextsystem.calcRoutingDeep()
            if nMaxDeep > MaxDeep:
                MaxDeep = nMaxDeep
        return MaxDeep

    def getLongRouting(self, maxdeep, dist, totalStartDist, totalHops, systems=[]):
        systems.append(self.systemName)
        for nextsystem in self.possibleSystems:
            if nextsystem.deep >= maxdeep:
                print("system:%s -> %s deep: %d dist:%d totalStarDist:%d hops:%d" % (systems, self.systemName, nextsystem.deep, nextsystem._dist + dist, nextsystem.starDist + totalStartDist, nextsystem._hopsFromBefore + totalHops))
            nextsystem.getLongRouting(maxdeep, nextsystem._dist + dist, nextsystem.starDist + totalStartDist, nextsystem._hopsFromBefore + totalHops, systems)
        systems.pop()

    def getMinHops(self, maxdeep, totalHops=0):

        minHops = None

        for nextsystem in self.possibleSystems:
            if nextsystem.deep >= maxdeep:
                if minHops is None or minHops > nextsystem._hopsFromBefore + totalHops:
                    minHops = nextsystem._hopsFromBefore + totalHops

            ret = nextsystem.getMinHops(maxdeep, nextsystem._hopsFromBefore + totalHops)

            if ret and (minHops is None or  minHops > ret):
                minHops = ret

        return minHops

    def calcRouteSum(self):
        totalSum = 1
        for nextsystem in self.possibleSystems:
            totalSum += nextsystem.calcRouteSum()
        return totalSum
    
    
    def getMinStarDist(self, maxdeep, starDist=0):

        minStartDist = None

        for nextsystem in self.possibleSystems:
            if nextsystem.deep >= maxdeep:
                if minStartDist is None or minStartDist > nextsystem.starDist + starDist:
                    minStartDist = nextsystem.starDist + starDist

            ret = nextsystem.getMinStarDist(maxdeep, nextsystem.starDist + starDist)

            if ret and (minStartDist is None or  minStartDist > ret):
                minStartDist = ret

        return minStartDist

    def getMinDistFromBest(self, maxdeep, dist=0, totalStartDist=0, totalHops=0, minHops=None, minStardist=None):
        # first loop calculate optimal data
        if minHops is None:
            minHops = self.getMinHops(maxdeep)
        if minStardist is None:
            minStardist = self.getMinStarDist(maxdeep)
        minDist = None
        
        for nextsystem in self.possibleSystems:
            if nextsystem.deep == maxdeep and nextsystem._hopsFromBefore + totalHops == minHops and nextsystem.starDist + totalStartDist == minStardist:
                if minDist is None or minDist > nextsystem._dist + dist:
                    minDist = nextsystem._dist + dist
                
            ret = nextsystem.getMinDistFromBest(maxdeep, nextsystem._dist + dist, nextsystem.starDist + totalStartDist, nextsystem._hopsFromBefore + totalHops, minHops, minStardist)
            if ret and (minDist is None or minDist > ret):
                minDist = ret

        return minDist

    def getBestRoute(self, maxdeep, dist=0, totalStartDist=0, totalHops=0, minHops=None, minStardist=None, minDist=None):
        # first loop calculate optimal data
        if minHops is None:
            minHops = self.getMinHops(maxdeep)
        if minStardist is None:
            minStardist = self.getMinStarDist(maxdeep)
        if minDist is None:
            minDist = self.getMinDistFromBest(maxdeep, 0, 0, 0, minHops, minStardist)

#        systems.append(self)
        for nextsystem in self.possibleSystems:
            if nextsystem and nextsystem.deep == maxdeep and nextsystem._hopsFromBefore + totalHops == minHops and nextsystem.starDist + totalStartDist == minStardist and minDist == nextsystem._dist + dist:

                #print("best system: %s deep: %d dist:%d totalStarDist:%d hops:%d" % ( self.systemName, nextsystem.deep, nextsystem._dist + dist, nextsystem.starDist + totalStartDist, nextsystem._hopsFromBefore + totalHops))
                before = nextsystem
                systems = []
                while before:
                    systems.append(before)
                    before = before._before
                systems.reverse()
                return systems
                break
            res = nextsystem.getBestRoute(maxdeep, nextsystem._dist + dist, nextsystem.starDist + totalStartDist, nextsystem._hopsFromBefore + totalHops,  minHops, minStardist, minDist)
            if res :
                #print(res)
                return res

    def getAllRoutes(self, maxdeep):
        routesList = []
        def listWorker(curSystem):
            if curSystem.deep == maxdeep:
                routesList.append(curSystem)
                return

            for nextsys in curSystem.possibleSystems:
                listWorker(nextsys)

        listWorker(self.initSystem)
        return routesList
    def getSystemsFromRoute(self):
        before = self
        systems = []
        while before:
            systems.append(before)
            before = before._before
        systems.reverse()
        return systems

    def getStardistanceFromRoute(self):
        before = self
        distance = 0
        while before:
            if before.starDist:
                distance += before.starDist
            before = before._before
        return distance

    def calcRoutenRecrusion(self, slowMode):
#        self.queueLock.acquire()
        if self.deep+1 >= self.maxDeep:
            return
        for nextsystem in self.possibleSystems:
            nextsystem.calcAllRoutesFromSystem( slowMode)

    def testExistRoute(self, system, currentRoute):
        # testen ob alle systeme der route schon einmal in einer anderen kombination verwendet wurden

        # recursive rareroute
        count = len(currentRoute)+1
        #if count == 1: return 
        def listWorker(curSystem, count):
            if curSystem.systemName in currentRoute:
                count -= 1
            elif curSystem.systemName == system:
                count -= 1

            #print(count)
            if count == 0:
#                print(system, curSystem.systemName ,currentRoute)
                # allow other routes to me drop only extaxt ends to me
                if curSystem.systemName == system:
                    return True
                return

                
            for nextsys in curSystem.possibleSystems:
                if listWorker(nextsys, count) == True:
                    return True
        # print(self.initSystem)
        return listWorker(self.initSystem, count)
    
    def calcAllRoutesFromSystem(self, slowMode=False):

        if len(self._availableSystemList) == 0: return
        maxDistance = self.maxHops * self.maxJumpDistance

        #print(len(self._availableSystemList), self._availableSystemList)
        systems = self.system.getSystemsInDistance(self.systemName, maxDistance, self._availableSystemList)


        #=======================================================================
        # reverse=True long routes first sell more items
        # reverse=False short routes first sell not all items
        # only in slow mod no difference
        #=====================================================================
        currentRoute = []
        if slowMode != True:
            systems = sorted(systems, key=lambda system: system["dist"], reverse=True)
            # build current routelist
            currentRoute.append(self.systemName)
            before = self._before
            while before:
                currentRoute.append(before.systemName)
                before = before._before

        for system in systems:
#            print(system)
            nextSystemlist = self._availableSystemList[:]
            #nextSystemlist  = []
            for listitem in nextSystemlist:
                if listitem[0] == system["System"]:
                    stardist = listitem[1]
                    nextSystemlist.remove(listitem)
                    break

            if slowMode == True:
                self.addPossibleSystems(system["System"], system["dist"], stardist, nextSystemlist)
            else:
                if self.testExistRoute(system["System"], currentRoute) != True:
                    #if True:
                    self.addPossibleSystems(system["System"], system["dist"], stardist, nextSystemlist)
                
#            self.addPossibleSystems(system["System"], system["dist"],  newrareslist)

        currentRoute = []
        self._availableSystemList = []
        nextSystemlist = []
        systems = []

        self.calcRoutenRecrusion(slowMode)

#        return myRaresRoute
