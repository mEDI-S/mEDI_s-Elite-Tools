# -*- coding: UTF8

'''
Created on 19.08.2015

@author: mEDI
'''
from PySide import QtCore, QtGui
import elite
import timeit
import time
import gui.guitools as guitools


__toolname__ = "Multi Hop Route Finder"
__statusTip__ = "Open A %s Window" % __toolname__


class RouteTreeInfoItem(object):
    def __init__(self, data, parent=None):
        self.parentItem = parent
        self.itemData = data
        self.childItems = []

    def appendChild(self, item):
        self.childItems.append(item)

    def child(self, row):
        return self.childItems[row]

    def childCount(self):
        return len(self.childItems)

    def columnCount(self):
        return 1

    def data(self, column):
        if isinstance( self.itemData, str) or isinstance( self.itemData, unicode):
            if column == 0:
                return self.itemData

    def getPiceID(self):
        if isinstance( self.itemData, list):
            return self.itemData[1]["priceAid"]
        
    def parent(self):
        return self.parentItem

    def row(self):
        if self.parentItem:
            return self.parentItem.childItems.index(self)

        return 0



class RouteTreeHopItem(object):
    def __init__(self, data, parent=None, dbresult=None):
        self.parentItem = parent
        self.itemData = data
        self.childItems = []
        self.dbresult = dbresult
        self._BGColor = None
        
    def appendChild(self, item):
        self.childItems.append(item)

    def child(self, row):
        return self.childItems[row]

    def childCount(self):
        return len(self.childItems)

    def columnCount(self):
        return 1
#        if isinstance( self.itemData, str):
#            return 1
#        else:
#            return len(self.itemData)

    def BGColor(self):
        return self._BGColor
    def setBGColor(self, BGColor):
        self._BGColor = BGColor

    def data(self, column):
        if isinstance( self.itemData, str) or isinstance( self.itemData, unicode):
            if column == 0:
                return self.itemData

    def getPiceID(self):
        if self.itemData:
            return self.dbresult["priceAid"]
        
    def parent(self):
        return self.parentItem

    def row(self):
        if self.parentItem:
            return self.parentItem.childItems.index(self)

        return 0




class RouteTreeItem(object):
    def __init__(self, data, parent=None):
        self.parentItem = parent
        self.itemData = data
        self.childItems = []
        self.activeRoute = None
   
    def appendChild(self, item):
        self.childItems.append(item)

    def child(self, row):
        return self.childItems[row]

    def childCount(self):
        return len(self.childItems)

    def childPos(self, child):
        if isinstance( child, RouteTreeHopItem):
            return self.childItems.index(child )
        elif isinstance( child, list) and isinstance( child[0], QtCore.QModelIndex):
            return self.childItems.index(child[0].internalPointer())
            #print("target", type(child[0]))

    def getListIndex(self):
        if isinstance( self.itemData[0], int): #via displayed Nr.
            return self.itemData[0]-1

    def columnCount(self):
        return len(self.itemData)

    def data(self, column):
        try:
            return self.itemData[column]
        except IndexError:
            return None

    def parent(self):
        return self.parentItem

    def row(self):
        if self.parentItem:
            return self.parentItem.childItems.index(self)

        return 0

    def getInternalRoutePointer(self):
        if isinstance( self.itemData[1], dict):
            return self.itemData[1]


class RouteTreeModel(QtCore.QAbstractItemModel):
    forceHops = None

    def __init__(self, route, parent=None, forceHops=None):
        super(RouteTreeModel, self).__init__(parent)
        self.route = route
        self.cleanModel()
        self.forceHops = forceHops
        self.setupModelData(route.deals, self.rootItem)

    def cleanModel(self):
        self.rootItem  = RouteTreeItem(("Nr.","routeidx","Profit/h", "Profit","Ø Profit","StartDist","Laps/h","LapTime", "Status"))

    def columnCount(self, parent):
        if parent.isValid():
            return parent.internalPointer().columnCount()
        else:
            return self.rootItem.columnCount()

    def data(self, index, role):
        if not index.isValid():
            return None

        if role == QtCore.Qt.BackgroundColorRole:
            item = index.internalPointer()
            if isinstance( item, RouteTreeHopItem):
                return item.BGColor() #yellow or green https://srinikom.github.io/pyside-docs/PySide/QtGui/QColor.html
            elif isinstance( item, RouteTreeItem):
                if item.activeRoute:
                    return QtGui.QColor(QtCore.Qt.cyan)
            elif isinstance( item, RouteTreeInfoItem):
                return QtGui.QColor(255, 0, 0, 64)

        if role != QtCore.Qt.DisplayRole:
            return None


        item = index.internalPointer()

        return item.data(index.column())

    def flags(self, index):
        if not index.isValid():
            return QtCore.Qt.NoItemFlags

        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

    def headerData(self, section, orientation, role):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return self.rootItem.data(section)
        return None

    def index(self, row, column, parent=QtCore.QModelIndex() ):
        if not self.hasIndex(row, column, parent):
            return QtCore.QModelIndex()

        if not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()

        childItem = parentItem.child(row)
        if childItem:
            return self.createIndex(row, column, childItem)
        else:
            return QtCore.QModelIndex()

    def parent(self, index):
        if not index.isValid():
            return QtCore.QModelIndex()

        childItem = index.internalPointer()
        parentItem = childItem.parent()

        if parentItem == self.rootItem:
            return QtCore.QModelIndex()

        return self.createIndex(parentItem.row(), 0, parentItem)

    def rowCount(self, parent=None):

        if parent != None and parent.column() > 0:
            return 0

        if parent == None or not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()

        return parentItem.childCount()

    def sort(self,col, order):
        print(col, order)
        if order == QtCore.Qt.SortOrder.DescendingOrder:
            order=True
        else:
            order=False

        self.layoutAboutToBeChanged.emit()
        if col==2:
            self.route.sortDealsByProfitH(order)
            self.cleanModel()
            self.setupModelData(self.route.deals, self.rootItem)
        elif col==3:
            self.route.sortDealsByProfit(order)
            self.cleanModel()
            self.setupModelData(self.route.deals, self.rootItem)
        elif col==4:
            self.route.sortDealsByProfitAverage(order)
            self.cleanModel()
            self.setupModelData(self.route.deals, self.rootItem)
        elif col==5:
            self.route.sortDealsByStartDist(order)
            self.cleanModel()
            self.setupModelData(self.route.deals, self.rootItem)
        elif col==7:
            self.route.sortDealsByLapTime(order)
            self.cleanModel()
            self.setupModelData(self.route.deals, self.rootItem)
        self.layoutChanged.emit()

    def setupModelData(self, deals, parent):
        parents = [parent]
        count = 0
        for routeId, deal in enumerate(deals):

            if routeId >= 100: break

            timeT = "%s:%s" % (divmod(deal["time"] * deal["lapsInHour"], 60))
            timeL = "%s:%s" % (divmod(deal["time"], 60))
            
            columnData = [routeId+1, deal, deal["profitHour"], deal["profit"], deal["profitAverage"], deal["path"][0]["startDist"], "%s/%s" % (deal["lapsInHour"], timeT), timeL]
            parents[-1].appendChild(RouteTreeItem(columnData, parents[-1]))


            before = { "StationB":deal["path"][0]["StationA"], "SystemB":deal["path"][0]["SystemA"], "StarDist":deal["path"][0]["stationA.StarDist"], "refuel":deal["path"][0]["stationA.refuel"]  }
            #follow is a child
            parents.append(parents[-1].child(parents[-1].childCount() - 1))
        
            for hopID,d in enumerate(deal["path"]):
                #print(d.keys())
                columnData = "%s : %s (%d ls) (%s buy:%d sell:%d profit:%d) (%s ly)-> %s:%s" % (self.route.getSystemA(routeId, hopID), 
                                                                                                self.route.getStationA(routeId, hopID),
                                                                                                before["StarDist"] , d["itemName"],d["StationSell"],
                                                                                                d["StationBuy"],  d["profit"], d["dist"],
                                                                                                self.route.getSystemB(routeId, hopID),
                                                                                                self.route.getStationB(routeId, hopID) )


                parents[-1].appendChild(RouteTreeHopItem( columnData , parents[-1], d))



                if before["refuel"] != 1:
                    columnData = "\tWarning: %s have no refuel!?" % self.route.getStationA(routeId, hopID)
                    parents[-1].appendChild(RouteTreeInfoItem( columnData, parents[-1]))
                
                before = d

        
            backdist = self.route.mydb.getDistanceFromTo(deal["path"][0]["SystemAID"] , deal["path"][ len(deal["path"])-1 ]["SystemBID"])

            hopID += 1
        
            if deal["backToStartDeal"]:
                #print(deal["backToStartDeal"].keys())
                columnData = "%s : %s (%d ls) (%s buy:%d sell:%d profit:%d) (%s ly)-> %s:%s" % (self.route.getSystemA(routeId, hopID),
                                                                                                self.route.getStationA(routeId, hopID),
                                                                                                before["StarDist"], deal["backToStartDeal"]["itemName"],
                                                                                                deal["backToStartDeal"]["StationSell"],
                                                                                                deal["backToStartDeal"]["StationBuy"],
                                                                                                deal["backToStartDeal"]["profit"],
                                                                                                backdist, self.route.getSystemB(routeId, hopID), self.route.getStationB(routeId, hopID) ) 
                temp = { "SystemB":deal["path"][0]["SystemA"], "SystemA":before["SystemB"], "priceAid":deal["backToStartDeal"]["priceAid"] } # TODO: bad hack
                parents[-1].appendChild(RouteTreeHopItem( columnData, parents[-1], temp))
            else:
                columnData = "%s : %s (%d ls) (no back deal) (%s ly) ->%s : %s" % (self.route.getSystemA(routeId, hopID),
                                                                                   self.route.getStationA(routeId, hopID),
                                                                                   before["StarDist"], backdist,
                                                                                   self.route.getSystemB(routeId, hopID),
                                                                                   self.route.getStationB(routeId, hopID)  )
                parents[-1].appendChild(RouteTreeInfoItem( columnData, parents[-1]))

        
            if before["refuel"] != 1:
                columnData = "\tWarning: %s have no refuel!?" % self.route.getStationA(routeId, hopID)
                parents[-1].appendChild(RouteTreeInfoItem(columnData, parents[-1]))
        
            # not more a child
            parents.pop()



class tool(QtGui.QWidget):
    main = None
    mydb = None
    route = None
    activeRoutePointer = None
    connectedDealsFromToWindows = None

    def __init__(self, main):
        super(tool, self).__init__(main)

        self.main = main
        self.mydb = main.mydb
        self.initRoute()
        self.guitools = guitools.guitools(self)
        self.createTimer()
        self.createActions()

    def getWideget(self):

        gridLayout = QtGui.QGridLayout()


        self.forceMaxHops = QtGui.QCheckBox("Force Max Hops")
        if self.mydb.getConfig("option_mhr_forceMaxHops"):
            self.forceMaxHops.setChecked(True)
        self.forceMaxHops.setToolTip("Show only routes with Max Hops+Back Hop")
        gridLayout.addWidget(self.forceMaxHops, 1, 0)


        self.autoUpdateLocation = QtGui.QCheckBox("Location Update")
        self.autoUpdateLocation.setChecked(True)
        self.autoUpdateLocation.stateChanged.connect( self.updateLocation )
        gridLayout.addWidget(self.autoUpdateLocation, 3, 0)

        label = QtGui.QLabel("Max Hops:")
        self.maxHopsspinBox = QtGui.QSpinBox()
        self.maxHopsspinBox.setRange(1, 20)
        self.maxHopsspinBox.setValue( self.route.getOption("tradingHops"))
        gridLayout.addWidget(label, 1, 1)
        gridLayout.addWidget(self.maxHopsspinBox, 1, 2)

        label = QtGui.QLabel("Search Range:")
        self.searchRangeSpinBox = QtGui.QSpinBox()
        self.searchRangeSpinBox.setRange(0, 1000)
        self.searchRangeSpinBox.setSuffix("ly")
        self.searchRangeSpinBox.setValue( self.route.getOption("maxSearchRange") )
        gridLayout.addWidget(label, 1, 3)
        gridLayout.addWidget(self.searchRangeSpinBox, 1, 4)


        label = QtGui.QLabel("Max Data Age:")
        self.maxAgeSpinBox = QtGui.QSpinBox()
        self.maxAgeSpinBox.setRange(1, 1000)
        self.maxAgeSpinBox.setSuffix("Day")
        self.maxAgeSpinBox.setValue( self.route.getOption("maxAge") )
        gridLayout.addWidget(label, 1, 5)
        gridLayout.addWidget(self.maxAgeSpinBox, 1, 6)


        label = QtGui.QLabel("Min Profit:")
        self.minProfitSpinBox = QtGui.QSpinBox()
        self.minProfitSpinBox.setRange(1000, 10000)
        self.minProfitSpinBox.setSuffix("cr")
        self.minProfitSpinBox.setSingleStep(100)
        self.minProfitSpinBox.setValue( self.route.getOption("minTradeProfit") )
        gridLayout.addWidget(label, 2, 1)
        gridLayout.addWidget(self.minProfitSpinBox, 2, 2)


        label = QtGui.QLabel("Max Dist:")
        self.maxDistSpinBox = QtGui.QSpinBox()
        self.maxDistSpinBox.setRange(0, 1000)
        self.maxDistSpinBox.setSuffix("ly")
        self.maxDistSpinBox.setSingleStep(1)
        self.maxDistSpinBox.setValue( self.route.getOption("maxDist") )
        gridLayout.addWidget(label, 2, 3)
        gridLayout.addWidget(self.maxDistSpinBox, 2, 4)


        label = QtGui.QLabel("Max Star Dist:")
        self.maxStartDistSpinBox = QtGui.QSpinBox()
        self.maxStartDistSpinBox.setRange(10, 7000000)
        self.maxStartDistSpinBox.setSuffix("ls")
        self.maxStartDistSpinBox.setSingleStep(10)
        self.maxStartDistSpinBox.setValue( self.route.getOption("maxStarDist") )
        gridLayout.addWidget(label, 2, 5)
        gridLayout.addWidget(self.maxStartDistSpinBox, 2, 6)


        label = QtGui.QLabel("Search Accuracy:")
        self.searchLimitOption = QtGui.QComboBox()
        searchLimitOptionsList = ["normal","fast","nice","slow","all"]
        for option in searchLimitOptionsList:
            self.searchLimitOption.addItem( option )
        if self.mydb.getConfig("option_searchLimit"):
            self.searchLimitOption.setCurrentIndex(self.mydb.getConfig("option_searchLimit"))
        label.setBuddy(self.searchLimitOption)
        #self.searchLimitOption.currentIndexChanged.connect(self.hmm)
        gridLayout.addWidget(label, 3, 1)
        gridLayout.addWidget(self.searchLimitOption, 3, 2, 1, 1) #row,col,?,size



        label = QtGui.QLabel("Max Jump Dist:")
        self.maxJumpDistSpinBox = QtGui.QDoubleSpinBox()
        self.maxJumpDistSpinBox.setRange(0, 1000)
        self.maxJumpDistSpinBox.setSuffix("ly")
        self.maxJumpDistSpinBox.setSingleStep(1)
        self.maxJumpDistSpinBox.setValue( self.route.getOption("maxJumpDistance") )
        gridLayout.addWidget(label, 3, 3)
        gridLayout.addWidget(self.maxJumpDistSpinBox, 3, 4)


        label = QtGui.QLabel("Min Stock:")
        self.minStockSpinBox = QtGui.QSpinBox()
        self.minStockSpinBox.setRange(1000, 1000000)
        self.minStockSpinBox.setSingleStep(100)
        self.minStockSpinBox.setValue( self.route.getOption("minStock") )
        gridLayout.addWidget(label, 3, 5)
        gridLayout.addWidget(self.minStockSpinBox, 3, 6)


        locationLabel = QtGui.QLabel("Location:")
        self.locationlineEdit = guitools.LineEdit()
        self.locationlineEdit.setText( self.main.location.getLocation() )
        self.locationlineEdit.textChanged.connect(self.triggerLocationChanged)


        locationGroupBox = QtGui.QGroupBox()
        locationGroupBox.setFlat(True)

        layout = QtGui.QHBoxLayout()

        self.showOptions = QtGui.QCheckBox("Show Options")
        if self.mydb.getConfig("option_mhr_showOptions") != 0:
            self.showOptions.setChecked(True)
        self.showOptions.stateChanged.connect( self.optionsGroupBoxToggleViewAction )

        self.searchbutton = QtGui.QPushButton("Search")
        self.searchbutton.clicked.connect(self.startRouteSearch)

        layout.addWidget(locationLabel)
        layout.addWidget(self.locationlineEdit)
        layout.addWidget(self.showOptions)
        layout.addWidget(self.searchbutton)

        locationGroupBox.setLayout(layout)


        self.optionsGroupBox = QtGui.QGroupBox("Options")
        self.optionsGroupBox.setLayout(gridLayout)


        self.listView = QtGui.QTreeView()
        self.listView.setAlternatingRowColors(True)
        self.listView.setSortingEnabled(True)
        self.listView.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.listView.setSelectionBehavior(QtGui.QAbstractItemView.SelectItems)

        self.listView.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.listView.customContextMenuRequested.connect(self.routelistContextMenuEvent)

        vGroupBox = QtGui.QGroupBox()
        vGroupBox.setFlat(True)
        layout = QtGui.QVBoxLayout()

        layout.addWidget(self.optionsGroupBox)
        layout.addWidget(locationGroupBox)
        layout.addWidget(self.listView)

        vGroupBox.setLayout(layout)

        self.guitools.setSystemComplete("", self.locationlineEdit)
        self.optionsGroupBoxToggleViewAction()

        return vGroupBox

    def routelistContextMenuEvent(self, event):

        menu = QtGui.QMenu(self)

        menu.addAction(self.copyAct)

        indexes = self.listView.selectionModel().selectedIndexes()
        if isinstance( indexes[0].internalPointer(), RouteTreeHopItem):
            if self.main.dealsFromToWidget:
                menu.addAction(self.addRouteHopAsFromSystemInDealsFromToFinderAct)
                menu.addAction(self.addRouteHopAsTargetSystemInDealsFromToFinderAct)
            menu.addAction(self.markFakeItemAct)

        elif isinstance( indexes[0].internalPointer(), RouteTreeItem):
            menu.addAction(self.clipbordRouteHelperAct)
            if self.main.dealsFromToWidget:
                self.connectToDealsFromToWindowsAct.setChecked(False)
                menu.addAction(self.connectToDealsFromToWindowsAct)
                if self.connectedDealsFromToWindows:
                    self.connectToDealsFromToWindowsAct.setChecked(True)
                    menu.addAction(self.disconnectFromDealsFromToWindowAct)

        else:
            print(type(indexes[0].internalPointer()))

        menu.exec_(self.listView.viewport().mapToGlobal(event))

    def optionsGroupBoxToggleViewAction(self):
        if self.showOptions.isChecked():
            self.optionsGroupBox.show()
        else:
            self.optionsGroupBox.hide()
            

    def initRoute(self):
        ''' init the route on start and set saved options'''

        self.route = elite.dealsroute(self.mydb)

        tradingHops = self.mydb.getConfig( 'option_tradingHops' )
        if tradingHops:
            self.route.setOption( "tradingHops", tradingHops )

        maxJumpDistance = self.mydb.getConfig( 'option_maxJumpDistance' )
        if maxJumpDistance:
            self.route.setOption( "maxJumpDistance", maxJumpDistance )

        maxDist = self.mydb.getConfig( 'option_maxDist' )
        if maxDist:
            self.route.setOption( "maxDist", maxDist )

        maxSearchRange = self.mydb.getConfig( 'option_maxSearchRange' )
        if maxSearchRange:
            self.route.setOption( "maxSearchRange", maxSearchRange )

        minStock = self.mydb.getConfig( 'option_minStock' )
        if minStock:
            self.route.setOption( "minStock", minStock )

        maxStarDist = self.mydb.getConfig( 'option_maxStarDist' )
        if maxStarDist:
            self.route.setOption( "maxStarDist", maxStarDist )

        minTradeProfit = self.mydb.getConfig( 'option_minTradeProfit' )
        if minTradeProfit:
            self.route.setOption( "minTradeProfit", minTradeProfit )


    def saveOptions(self):
        #save last options
        self.mydb.setConfig( 'option_tradingHops', self.maxHopsspinBox.value() )
        self.mydb.setConfig( 'option_maxJumpDistance', self.maxJumpDistSpinBox.value() )
        self.mydb.setConfig( 'option_maxDist', self.maxDistSpinBox.value() )
        self.mydb.setConfig( 'option_maxSearchRange', self.searchRangeSpinBox.value() )
        self.mydb.setConfig( 'option_minStock', self.minStockSpinBox.value() )
        self.mydb.setConfig( 'option_maxStarDist', self.maxStartDistSpinBox.value() )
        self.mydb.setConfig( 'option_minTradeProfit', self.minProfitSpinBox.value() )
        self.mydb.setConfig( 'option_searchLimit', self.searchLimitOption.currentIndex() )

        self.mydb.setConfig( 'option_mhr_showOptions', self.showOptions.isChecked() )
        self.mydb.setConfig( 'option_mhr_forceMaxHops', self.forceMaxHops.isChecked() )


    def startRouteSearch(self):
        self.activeRoutePointer = None
        self.main.lockDB()

        starttime = timeit.default_timer()

        self.route.setOption( "startSystem", self.locationlineEdit.text() )
        self.route.setOption( "tradingHops", self.maxHopsspinBox.value() )
        self.route.setOption( "maxJumpDistance", self.maxJumpDistSpinBox.value() )
        self.route.setOption( "maxDist", self.maxDistSpinBox.value() )
        self.route.setOption( "maxSearchRange", self.searchRangeSpinBox.value() )
        self.route.setOption( "minStock", self.minStockSpinBox.value() )
        self.route.setOption( "maxStarDist", self.maxStartDistSpinBox.value() )
        self.route.setOption( "maxAge", self.maxAgeSpinBox.value() )
        self.route.setOption( "minTradeProfit", self.minProfitSpinBox.value() )

        
        self.route.calcDefaultOptions()

        forceHops = None
        if self.forceMaxHops.isChecked():
            forceHops = self.maxHopsspinBox.value()
        self.route.forceHops = forceHops
        
        self.route.limitCalc( self.searchLimitOption.currentIndex() ) #options (normal, fast, nice, slow, all)


        self.route.calcRoute()
        
#        self.route.printList()


        routeModel = RouteTreeModel(self.route, self, forceHops)
        QtCore.QObject.connect(routeModel, QtCore.SIGNAL ('layoutChanged()'), self.routeModellayoutChanged)
        self.listView.setModel(routeModel)
#        routeModel.layoutChanged.emit()
        self.listView.sortByColumn( 2, QtCore.Qt.SortOrder.DescendingOrder )
        self.listView.hideColumn(1)

        self.triggerLocationChanged()
        self.listView.show()

        self.main.setStatusBar("Route Calculated (%ss) %d routes found" % ( round(timeit.default_timer() - starttime, 2), len(self.route.deals)) )

        self.main.unlockDB()

    def routeModellayoutChanged(self):
        routeModel = self.listView.model()
        for rid in range(0,routeModel.rowCount(QtCore.QModelIndex())):
            #rid item count
            for cid in range( 0, routeModel.rowCount(routeModel.index(rid,0)) ):
                #cid child item count
                self.listView.setFirstColumnSpanned(cid, routeModel.index(rid,0) , True)        

        self.listView.expandToDepth(1)

        for i in range(0, 5):
            self.listView.resizeColumnToContents(i)

        self.triggerLocationChanged()

    def createTimer(self):
        self.autoUpdateLocationTimer = QtCore.QTimer()
        self.autoUpdateLocationTimer.start(1000*60)
        self.autoUpdateLocationTimer.timeout.connect(self.updateLocation)

    def updateLocation(self):
        if self.autoUpdateLocation.isChecked():

            self.autoUpdateLocationTimer.stop()
            starttime = timeit.default_timer()

            self.locationlineEdit.setText( self.main.location.getLocation() )
            print("location updatet %ss" % round(timeit.default_timer() - starttime, 2) )

            self.autoUpdateLocationTimer.start()
        else:
            print("stop update location timer")
            self.autoUpdateLocationTimer.stop()

        
    def triggerLocationChanged(self):
        print("triggerLocationChanged")
        self.setLocationColors()
        self.updateConnectedDealsFromToWindow()

    def setLocationColors(self):
        location = self.locationlineEdit.text()
        routeModel = self.listView.model()

        if not routeModel or not routeModel.rowCount(): return
        
        if location and routeModel:
            for rid in range(0,routeModel.rowCount(QtCore.QModelIndex())):
                route = routeModel.index( rid, 0).internalPointer()
                for cid in range( 0, route.childCount() ):
                    child = route.child(cid)
                    #print(child)
                    if isinstance( child, RouteTreeHopItem):
                        if child.dbresult["SystemA"].lower() == location.lower():
                            if route.activeRoute:
                                child.setBGColor( QtGui.QColor(QtCore.Qt.green) )
                            else:
                                child.setBGColor( QtGui.QColor(QtCore.Qt.yellow) )
                        else:
                            child.setBGColor(None)
        self.listView.dataChanged(routeModel.index( 0, 0), routeModel.index( rid, 0))

    def createActions(self):
        self.markFakeItemAct = QtGui.QAction("Set Item as Fake", self,
                statusTip="Set not existing items as Fake and filter it on next search", triggered=self.markFakeItem)

        self.clipbordRouteHelperAct = QtGui.QAction("Start clipboard Route Helper", self, checkable=True,
                statusTip="Start a helper job to set automatly the next routehop to clipboard", triggered=self.clipbordRouteHelper)

        self.addRouteHopAsTargetSystemInDealsFromToFinderAct = QtGui.QAction("Set as To in (Deals From To Finder 1)", self,
                statusTip="Set System/Station as To in Deals Finder", triggered=self.addRouteHopAsTargetSystemInDealsFromToFinder)

        self.addRouteHopAsFromSystemInDealsFromToFinderAct = QtGui.QAction("Set as From in (Deals From To Finder 1)", self,
                statusTip="Set System/Station as From in Deals Finder", triggered=self.addRouteHopAsFromSystemInDealsFromToFinder)

        self.connectToDealsFromToWindowsAct = QtGui.QAction("Connect Route to (Deals From To Finder 1)", self, checkable=True,
                statusTip="Update (Deals From To Finder 1) with current Route position", triggered=self.connectToDealsFromToWindows)

        self.disconnectFromDealsFromToWindowAct = QtGui.QAction("Disconnect (Deals From To Finder 1)", self,
                statusTip="Disconnect From (Deals From To Finder 1) window", triggered=self.disconnectFromDealsFromToWindow)

        self.copyAct = QtGui.QAction("Copy", self, triggered=self.guitools.copyToClipboard, shortcut=QtGui.QKeySequence.Copy)

    def setActiveRoutePointer(self):
        indexes = self.listView.selectionModel().selectedIndexes()
 
        if isinstance( indexes[0].internalPointer(), RouteTreeItem):
            if self.activeRoutePointer:
                self.activeRoutePointer.activeRoute = None
            self.activeRoutePointer = indexes[0].internalPointer()
            self.activeRoutePointer.activeRoute = True

    def clipbordRouteHelper(self):
        self.setActiveRoutePointer()

        self.timer_setNextRouteHopToClipbord = QtCore.QTimer()
        self.timer_setNextRouteHopToClipbord.start(1000*60)
        self.timer_setNextRouteHopToClipbord.timeout.connect(self.setNextRouteHopToClipbord)

        self.clipbordRouteHelperAct.setChecked(True)
        self.triggerLocationChanged()
        self.setNextRouteHopToClipbord(init=True)
        
    def setNextRouteHopToClipbord(self, init=None):
        ''' helper to set next route hop to clipboard '''
        if not self.activeRoutePointer:
            return
        
        clipbordText = self.main.clipboard.text()

        if init:
            self.lastClipboardEntry = None
        elif self.lastClipboardEntry != clipbordText:
            #stop timer and job do other tool use the clipbord
            print("setNextRouteHopToClipbord stop job")
            self.timer_setNextRouteHopToClipbord.stop()
            self.clipbordRouteHelperAct.setChecked(False)
            return

        child = self.getCurrentHopFromActiveRoute()
        if child:
            system = child.dbresult["SystemB"]

            if system != clipbordText:
                self.main.clipboard.setText( system )
                self.lastClipboardEntry = system
                print("setNextRouteHopToClipbord set clipboard to", system)

        if not self.lastClipboardEntry:
            # not in route? set the first hop to clipboard
            child = self.activeRoutePointer.child( 0 )
            system = child.dbresult["SystemA"]
            self.main.clipboard.setText( system )
            self.lastClipboardEntry = system
            print("setNextRouteHopToClipbord set clipboard to", system)

        self.timer_setNextRouteHopToClipbord.start()
    
    def markFakeItem(self):
        print("markFakeItem")

        indexes = self.listView.selectionModel().selectedIndexes()
 
        if isinstance( indexes[0].internalPointer(), RouteTreeHopItem):
            id = indexes[0].internalPointer().getPiceID()
            if id:

                msgBox = QtGui.QMessageBox(QtGui.QMessageBox.Warning,
                        "Warning", "Warning: fake items are ignored everywhere and no longer displayed",
                        QtGui.QMessageBox.NoButton, self)

                msgBox.addButton("Save as Facke", QtGui.QMessageBox.AcceptRole)
                msgBox.addButton("Cancel", QtGui.QMessageBox.RejectRole)

                if msgBox.exec_() == QtGui.QMessageBox.AcceptRole:
                    print("set %s as fakeprice" % id)
                    self.main.lockDB()
                    self.mydb.setFakePrice(id)
                    self.main.unlockDB()

    def getSelectedRouteHopID(self):
        indexes = self.listView.selectionModel().selectedIndexes()
        
        if isinstance( indexes[0].internalPointer(), RouteTreeHopItem):

            routeId = indexes[0].internalPointer().parent().getListIndex()
            hopID =  indexes[0].internalPointer().parent().childPos( indexes )

#            routeDeal = indexes[0].internalPointer().parent().getInternalRoutePointer()
#            print(self.route.deals.index(routeDeal), routeId )
            return (routeId, hopID)

        return (None, None)

    def addRouteHopAsTargetSystemInDealsFromToFinder(self):

        (routeId, hopID) = self.getSelectedRouteHopID()
        if routeId == None or hopID == None:
            return

        toStation = self.route.getStationA(routeId,hopID)
        toSystem = self.route.getSystemA(routeId,hopID)
        #TODO: set it only in first Deals window current
        if toSystem and toStation:
            self.main.dealsFromToWidget[0].toSystem.setText(toSystem)
            self.main.dealsFromToWidget[0].toStation.setText(toStation)

    def addRouteHopAsFromSystemInDealsFromToFinder(self):

        (routeId, hopID) = self.getSelectedRouteHopID()
        if routeId == None or hopID == None: return

        station = self.route.getStationA(routeId,hopID)
        system = self.route.getSystemA(routeId,hopID)
        #TODO: set it only in first Deals window current
        if system and station:
            self.main.dealsFromToWidget[0].fromSystem.setText(system)
            self.main.dealsFromToWidget[0].fromStation.setText(station)

    def connectToDealsFromToWindows(self):
        if self.main.dealsFromToWidget:
            self.setActiveRoutePointer()
            self.triggerLocationChanged()

            self.connectedDealsFromToWindows = self.main.dealsFromToWidget[0]
            self.connectedDealsFromToWindows.autoUpdateLocation.setChecked(False)

            self.updateConnectedDealsFromToWindow(init=True)

    def disconnectFromDealsFromToWindow(self):
        self.connectedDealsFromToWindows = None

    def getCurrentHopFromActiveRoute(self):
        location = self.main.location.getLocation()

        for cid in range( 0, self.activeRoutePointer.childCount() ):
            child = self.activeRoutePointer.child(cid)
            if isinstance( child, RouteTreeHopItem):

                if child.dbresult["SystemB"] == location:
                    if self.activeRoutePointer.childCount() > cid+1:
                        child = self.activeRoutePointer.child(cid+1)
                    else: #start system is next hop
                        child = self.activeRoutePointer.child( 0 )
                    return child

    def updateConnectedDealsFromToWindow(self, init=None):
        if not self.connectedDealsFromToWindows or  not self.activeRoutePointer:
            return

        routeId = self.activeRoutePointer.getListIndex()
        
        currentHop = self.getCurrentHopFromActiveRoute()
        if currentHop == None and init:
            ''' is init and im not inside the route set only the To part from first hop '''
            systemA = self.route.getSystemA(routeId, 0)
            stationA = self.route.getStationA(routeId, 0)

            self.connectedDealsFromToWindows.toSystem.setText(systemA)
            self.connectedDealsFromToWindows.toStation.setText(stationA)
            return

        hopID =  self.activeRoutePointer.childPos( currentHop )

        if routeId == None or hopID == None:
            return

        systemA = self.route.getSystemA(routeId, hopID)
        stationA = self.route.getStationA(routeId, hopID)

        systemB = self.route.getSystemB(routeId, hopID)
        stationB = self.route.getStationB(routeId, hopID)

        self.connectedDealsFromToWindows.fromSystem.setText(systemA)
        self.connectedDealsFromToWindows.fromStation.setText(stationA)

        self.connectedDealsFromToWindows.toSystem.setText(systemB)
        self.connectedDealsFromToWindows.toStation.setText(stationB)

