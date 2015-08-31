# -*- coding: UTF8
'''
Created on 19.08.2015

@author: mEDI
'''

from datetime import datetime, date, time, timedelta
import elite

class route(object):
    '''
    calculate a A-B-A or A-B(x) route,
    set speed control and result details over limitCalc()
    '''

    mydb=None
    deals = []

    options = {}
    options["startSystem"] = None
    options["tradingHops"] = 2  # +1 for the back hop
    options["maxJumpDistance"] = 16.3
    options["maxDist"] = options["maxJumpDistance"]*3  # max distace for B system
    options["maxSearchRange"] = options["maxJumpDistance"]*5  # on start search used
    options["maxStarDist"] = 1300
    options["maxAge"] = 14  # max data age in days
    options["minTradeProfit"] = 1000  # only to minimize results (speedup)
    options["minStock"] = 50000  # > 10000 = stable route > 50000 = extrem stable route and faster results
    options["resultLimit"] = None # calculated by self.limitCalc()

    maxAgeDate = None # calculated by setMaxAgeDate()
    elitetime = None

    def __init__(self, mydb):
        '''
        Constructor
        '''
        self.mydb = mydb
        self.calcDefaultOptions()

    def calcDefaultOptions(self):
        self.elitetime = elite.elitetime(self.mydb, self.options["maxJumpDistance"])
        self.limitCalc()
        self.setMaxAgeDate()

    def setOption(self, option, val):
        self.options[option] = val

    def getOption(self, option):
        if option in self.options:
            return self.options[option]

    def getStationA(self,routeId,hopID):
        if hopID == 0:
            return self.deals[routeId]["path"][hopID]["StationA"]

        return self.deals[routeId]["path"][hopID-1]["StationB"]

    def getSystemA(self,routeId,hopID):
        if hopID == 0:
            return self.deals[routeId]["path"][hopID]["SystemA"]

        return self.deals[routeId]["path"][hopID-1]["SystemB"]
            
    def limitCalc(self, accuracy=0):
        ''' ["normal","fast","nice","slow","all"] '''
        maxResults = 100000 # normal

        if accuracy == 1:
            maxResults = 5000
        elif accuracy == 2:
            maxResults = 1000000
        elif accuracy == 3:
            maxResults = 4000000
            
        self.options["resultLimit"] = round( maxResults**(1.0 / self.options["tradingHops"] )) #max results = 1000000 = resultLimit^tradingHops

        if accuracy == 4:
            self.options["resultLimit"] = 999999

    def setMaxAgeDate(self):
        self.maxAgeDate = datetime.utcnow() - timedelta(days = self.options["maxAge"] )

    def calcRoute(self):
        self.deals = []

        self.findStartDeal()
        self.findHops()
        self.findBackToStartDeals()
        self.calcRating()

    def findStartDeal(self):
        startdeals = self.mydb.getBestDealsinDistance( self.options["startSystem"], self.options["maxDist"], self.options["maxSearchRange"], self.maxAgeDate, self.options["maxStarDist"], self.options["minTradeProfit"], self.options["minStock"], self.options["resultLimit"])

        for deal in startdeals:
            self.deals.append({ "profit":0, "time":0 , "path":[deal],"backToStartDeal":None })

    def findHops(self):
        for deep in range( 1, self.options["tradingHops"] ):
            print("deep", deep+1)
            for deal in self.deals[:]:
                if deep == len(deal["path"]):
                    delsX = self.mydb.getBestDealsFromStationInDistance(deal["path"][ len(deal["path"])-1 ]["StationBID"], self.options["maxDist"], self.maxAgeDate, self.options["maxStarDist"], self.options["minTradeProfit"], self.options["minStock"], self.options["resultLimit"])
                    for dealX in delsX:
                        
                        dealnew = deal.copy()
                        dealnew["path"] = list(deal["path"]) #deepcopy do not work
                         
                        dealnew["path"].append(dealX)
                        self.deals.append(dealnew)

    def findBackToStartDeals(self):
        for deal in self.deals:
            backdeals = self.mydb.getDealsFromTo( deal["path"][ len(deal["path"])-1 ]["StationBID"],  deal["path"][0]["StationAID"], self.maxAgeDate, 1000)
            if backdeals:
                deal["backToStartDeal"] = backdeals[0]


    def calcRating(self):
        for deal in self.deals:
            Systembefore = None
            for i, step in enumerate(deal["path"]):
                deal["profit"] += step["profit"]
        
                if i == 0:
                    deal["time"] += self.elitetime.calcTimeFromTo(step["SystemAID"], step["StationBID"], step["SystemBID"])
                    Systembefore = step["SystemBID"]
                else:
                    deal["time"] += self.elitetime.calcTimeFromTo(Systembefore , step["StationBID"], step["SystemBID"])
                    Systembefore = step["SystemBID"]
        
            # add back to start time
            deal["time"] += self.elitetime.calcTimeFromTo(Systembefore , deal["path"][0]["StationAID"], deal["path"][0]["SystemAID"])
            if deal["backToStartDeal"]:
                deal["profit"] += deal["backToStartDeal"]["profit"]
        
            lapsInHour = int(3600 / deal["time"])  # round down
        
            profitHour = int(3600.0 / deal["time"] * deal["profit"]) #hmm mit lapsInHour oder mit hochrechnung rechnen?
        
            deal["profitHour"] = profitHour
            deal["lapsInHour"] = lapsInHour

        self.sortDealsByProfitH()

    def sortDealsByProfitH(self):            
        self.deals = sorted(self.deals , key=lambda deal: deal["profitHour"], reverse=True)


    def printList(self):
        print("routes found", len(self.deals))
        
        for i, deal in enumerate(self.deals):
            if i >= 40: break 
        
            timeT = "%s:%s" % (divmod(deal["time"] * deal["lapsInHour"], 60))
            timeL = "%s:%s" % (divmod(deal["time"], 60))
        
            print("\n%d. profit: %d profit/h:%d Laps/h: %d/%s LapTime: %s (Start dist: %s ly)" % (i + 1, deal["profit"], deal["profitHour"], deal["lapsInHour"], timeT, timeL, deal["path"][0]["startDist"])) 
        
        
            before = { "StationB":deal["path"][0]["StationA"], "SystemB":deal["path"][0]["SystemA"], "StarDist":deal["path"][0]["stationA.StarDist"], "refuel":deal["path"][0]["stationA.refuel"]  }
        
            for d in deal["path"]:
                #print(d.keys())
                print("\t%s : %s (%d ls) (%s buy:%d sell:%d profit:%d) (%s ly)-> %s:%s" % (before["SystemB"], before["StationB"], before["StarDist"] , d["itemName"],d["StationSell"], d["StationBuy"],  d["profit"], d["dist"],d["SystemB"],d["StationB"] ) )
                if before["refuel"] != 1:
                    print("\t\tWarning: %s have no refuel!?" % before["StationB"])
                
                before = d
        
            backdist = self.mydb.getDistanceFromTo(deal["path"][0]["SystemAID"] , deal["path"][ len(deal["path"])-1 ]["SystemBID"])
        
            if deal["backToStartDeal"]:
                #print(deal["backToStartDeal"].keys())
                print("\t%s : %s (%d ls) (%s buy:%d sell:%d profit:%d) (%s ly)-> %s:%s" % (before["SystemB"], deal["backToStartDeal"]["fromStation"] , before["StarDist"], deal["backToStartDeal"]["itemName"], deal["backToStartDeal"]["StationSell"],deal["backToStartDeal"]["StationBuy"],  deal["backToStartDeal"]["profit"], backdist, deal["path"][0]["SystemA"], deal["path"][0]["StationA"] ) )
            else:
                print("\tno back deal (%s ly) ->%s : %s" % (backdist, deal["path"][0]["SystemA"], deal["path"][0]["StationA"]  ))
        
            if before["refuel"] != 1:
                print("\t\tWarning: %s have no refuel!?" % before["StationB"])
        
        
        
        print("\noptions: startSystem:%s, tradingHops:%d, maxDist:%d, maxJumpDistance:%d, maxSearchRange:%d, maxStarDist:%d, maxAge:%d, minTradeProfit:%d, minStock:%d, resultLimit:%d" 
              % (self.options["startSystem"], self.options["tradingHops"], self.options["maxDist"], self.options["maxJumpDistance"], self.options["maxSearchRange"], self.options["maxStarDist"], self.options["maxAge"], self.options["minTradeProfit"], self.options["minStock"], self.options["resultLimit"]) )
        
        