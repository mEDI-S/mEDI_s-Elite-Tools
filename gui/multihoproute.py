# -*- coding: UTF8

'''
Created on 19.08.2015

@author: mEDI
'''
from PySide import QtCore, QtGui
import elite
import timeit
import gui.guitools as guitools


__toolname__ = "Multi Hop Route Finder"
__internalName__ = "MuHoRoFi"
__statusTip__ = "Open A %s Window" % __toolname__
_debug = None


class RouteTreeInfoItem(object):
    parentItem = None

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
        if isinstance(self.itemData, str) or isinstance(self.itemData, unicode):
            if column == 0:
                return self.itemData
        
    def parent(self):
        return self.parentItem

    def row(self):
        if self.parentItem:
            return self.parentItem.childItems.index(self)

        return 0



class RouteTreeHopItem(object):
    parentItem = None

    def __init__(self, data, parent=None):
        self.parentItem = parent
        self.itemData = data
        self.childItems = []
        self._BGColor = None
        
    def appendChild(self, item):
        self.childItems.append(item)

    def child(self, row):
        return self.childItems[row]

    def childCount(self):
        return len(self.childItems)

    def columnCount(self):
        return 1

    def BGColor(self):
        return self._BGColor

    def setBGColor(self, BGColor):
        self._BGColor = BGColor

    def data(self, column):
        if isinstance(self.itemData, str) or isinstance(self.itemData, unicode):
            if column == 0:
                return self.itemData
     
    def parent(self):
        if self.parentItem:
            return self.parentItem

    def row(self):
        if self.parentItem:
            return self.parentItem.childItems.index(self)

        return 0




class RouteTreeItem(object):
    parentItem = None
    childItems = []

    def __init__(self, data, parent=None):
        self.childItems = []
        self.parentItem = parent
        self.itemData = data

    def appendChild(self, item):
        self.childItems.append(item)

    def child(self, row):
        return self.childItems[row]

    def childCount(self):
        return len(self.childItems)

    def childPos(self, child):
        if isinstance(child, RouteTreeHopItem):
            return self.childItems.index(child)
        elif isinstance(child, list) and isinstance(child[0], QtCore.QModelIndex):
            return self.childItems.index(child[0].internalPointer())


    def hopPos(self, child):
        if isinstance(child, list) and isinstance(child[0], QtCore.QModelIndex):
            child = child[0].internalPointer()

        if isinstance(child, RouteTreeHopItem):
            pos = -1
            for item in self.childItems:
                if isinstance(item, RouteTreeHopItem):
                    pos += 1
                if item == child:
                    return pos


    def getListIndex(self):
        if isinstance(self.itemData[0], int):  # via displayed Nr.
            return self.itemData[0] - 1

    def columnCount(self):
        return len(self.itemData)

    def data(self, column):
        if isinstance(self.itemData, list) and column < len(self.itemData):
            return self.itemData[column]
        elif isinstance(self.itemData, tuple) and column < len(self.itemData):
            return self.itemData[column]
        elif column != 8:
            print(type(self.itemData), column)

    def parent(self):
        if self.parentItem:
            return self.parentItem

    def row(self):
        if self.parentItem:
            return self.parentItem.childItems.index(self)

        return 0

    def getInternalRoutePointer(self):
        if isinstance(self.itemData[1], dict):
            return self.itemData[1]



class RouteTreeModel(QtCore.QAbstractItemModel):
    forceHops = None

    def __init__(self, route, parent=None, forceHops=None):
        super(RouteTreeModel, self).__init__(parent)
        self.route = route
        self.cleanModel()
        self.forceHops = forceHops
        self.setupModelData()

    def cleanModel(self):
        if _debug:
            print("cleanModel")
           
        self.rootItem = RouteTreeItem(("Nr.", "routeidx", "Profit/h", "Profit", "Ø Profit", "StartDist", "Laps/h", "LapTime", "Status"))

    def columnCount(self, parent):
        if parent.isValid():
            return parent.internalPointer().columnCount()
        elif self.rootItem:
            return self.rootItem.columnCount()
            
    def data(self, index, role):
        if not index.isValid():
            return None

        if role == QtCore.Qt.BackgroundColorRole:
            item = index.internalPointer()
            if isinstance(item, RouteTreeHopItem):
                return item.BGColor()  # yellow or green https://srinikom.github.io/pyside-docs/PySide/QtGui/QColor.html
            elif isinstance(item, RouteTreeItem):
                pointer = item.getInternalRoutePointer()
                if pointer and pointer["activeRoute"]:
                    return QtGui.QColor(QtCore.Qt.cyan)
            elif isinstance(item, RouteTreeInfoItem):
                return QtGui.QColor(255, 0, 0, 64)

        if role == QtCore.Qt.TextAlignmentRole:
            item = index.internalPointer()
            if isinstance(item, RouteTreeItem):
                if index.column() == 0:
                    return QtCore.Qt.AlignCenter
                elif index.column() > 0 and index.column() < 5:  # all profit = align right
                    return QtCore.Qt.AlignRight
                else:
                    return QtCore.Qt.AlignCenter
                    
        if role != QtCore.Qt.DisplayRole:
            return None


        item = index.internalPointer()
        if isinstance(index, QtCore.QModelIndex) and not self.route.locked:
            return item.data(index.column())

    def flags(self, index):
        if not index.isValid():
            return QtCore.Qt.NoItemFlags

        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

    def headerData(self, section, orientation, role):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return self.rootItem.data(section)

        if role == QtCore.Qt.TextAlignmentRole:
            return QtCore.Qt.AlignCenter

    def index(self, row, column, parent=QtCore.QModelIndex()):
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
        if not index.isValid() or self.route.locked:
            return QtCore.QModelIndex()
        childItem = index.internalPointer()
        if childItem:
            parentItem = childItem.parent()
        else:
            return QtCore.QModelIndex()
            
        if parentItem is None:
            return QtCore.QModelIndex()
        elif parentItem == self.rootItem:
            return QtCore.QModelIndex()
            
        return self.createIndex(parentItem.row(), 0, parentItem)

    def rowCount(self, parent=None):

        if parent is not None and parent.column() > 0:
            return 0

        if parent is None or not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()

        return parentItem.childCount()

    def sort(self, col, order):
        if _debug:
            print("sort")
        # print(col, order)
        if self.route.locked:
            return
        if order == QtCore.Qt.SortOrder.DescendingOrder:
            order = True
        else:
            order = False
        self.layoutAboutToBeChanged.emit()
        self.modelAboutToBeReset.emit()
        if col == 2:
            self.route.sortDealsByProfitH(order)
            self.cleanModel()
            self.setupModelData()
        elif col == 3:
            self.route.sortDealsByProfit(order)
            self.cleanModel()
            self.setupModelData()
        elif col == 4:
            self.route.sortDealsByProfitAverage(order)
            self.cleanModel()
            self.setupModelData()
        elif col == 5:
            self.route.sortDealsByStartDist(order)
            self.cleanModel()
            self.setupModelData()
        elif col == 7:
            self.route.sortDealsByLapTime(order)
            self.cleanModel()
            self.setupModelData()
        self.modelReset.emit()
        self.layoutChanged.emit()

    def setupModelData(self):
        if _debug:
            print("setupModelData")
        parents = [self.rootItem]

        for routeId, deal in enumerate(self.route.deals):

            if routeId >= 100:
                break
            timeT = "%s:%s" % (divmod(deal["time"] * deal["lapsInHour"], 60))
            timeL = "%s:%s" % (divmod(deal["time"], 60))

            
            columnData = [routeId + 1, deal, deal["profitHour"], deal["profit"], deal["profitAverage"], deal["path"][0]["startDist"], "%s/%s" % (deal["lapsInHour"], timeT), timeL]

            parents[-1].appendChild(RouteTreeItem(columnData, parents[-1]))


            before = { "StationB": deal["path"][0]["StationA"], "SystemB": deal["path"][0]["SystemA"], "StarDist": deal["path"][0]["stationA.StarDist"], "refuel": deal["path"][0]["stationA.refuel"] }
            # follow is a child
            parents.append(parents[-1].child(parents[-1].childCount() - 1))
        
            for hopID, d in enumerate(deal["path"]):
                # print(d.keys())
                columnData = "%s : %s (%d ls) (%s buy:%d sell:%d profit:%d) (%s ly)-> %s:%s" % (self.route.getSystemA(deal, hopID),
                                                                                                self.route.getStationA(deal, hopID),
                                                                                                before["StarDist"], d["itemName"], d["StationSell"],
                                                                                                d["StationBuy"], d["profit"], d["dist"],
                                                                                                self.route.getSystemB(deal, hopID),
                                                                                                self.route.getStationB(deal, hopID))


                parents[-1].appendChild(RouteTreeHopItem(columnData, parents[-1]))



                if before["refuel"] != 1:
                    columnData = "\tWarning: %s have no refuel!?" % self.route.getStationA(deal, hopID)
                    parents[-1].appendChild(RouteTreeInfoItem(columnData, parents[-1]))
                
                before = d

        
            backdist = self.route.mydb.getDistanceFromTo(deal["path"][0]["SystemAID"], deal["path"][ len(deal["path"]) - 1 ]["SystemBID"])

            hopID += 1
        
            if deal["backToStartDeal"]:
                # print(deal["backToStartDeal"].keys())
                columnData = "%s : %s (%d ls) (%s buy:%d sell:%d profit:%d) (%s ly)-> %s:%s" % (self.route.getSystemA(deal, hopID),
                                                                                                self.route.getStationA(deal, hopID),
                                                                                                before["StarDist"], deal["backToStartDeal"]["itemName"],
                                                                                                deal["backToStartDeal"]["StationSell"],
                                                                                                deal["backToStartDeal"]["StationBuy"],
                                                                                                deal["backToStartDeal"]["profit"],
                                                                                                backdist,
                                                                                                self.route.getSystemB(deal, hopID),
                                                                                                self.route.getStationB(deal, hopID))
                parents[-1].appendChild(RouteTreeHopItem(columnData, parents[-1]))
            else:
                columnData = "%s : %s (%d ls) (no back deal) (%s ly) ->%s : %s" % (self.route.getSystemA(deal, hopID),
                                                                                   self.route.getStationA(deal, hopID),
                                                                                   before["StarDist"], backdist,
                                                                                   self.route.getSystemB(deal, hopID),
                                                                                   self.route.getStationB(deal, hopID))
                parents[-1].appendChild(RouteTreeInfoItem(columnData, parents[-1]))

        
            if before["refuel"] != 1:
                columnData = "\tWarning: %s have no refuel!?" % self.route.getStationA(deal, hopID)
                parents[-1].appendChild(RouteTreeInfoItem(columnData, parents[-1]))
        
            # not more a child
            parents.pop()



class tool(QtGui.QWidget):
    main = None
    mydb = None
    route = None
    activeRoutePointer = None
    connectedDealsFromToWindows = None
    layoutLock = None
    enabelSortingTimer = None
    
#    _debug = True
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

        gridLayout.setColumnStretch(1, 1)
        gridLayout.setColumnStretch(3, 2)
        gridLayout.setColumnStretch(4, 1)
        gridLayout.setColumnStretch(6, 2)
        gridLayout.setColumnStretch(7, 1)
        gridLayout.setColumnStretch(9, 2)

        self.forceMaxHops = QtGui.QCheckBox("Force Max Hops")
        if self.mydb.getConfig("option_mhr_forceMaxHops"):
            self.forceMaxHops.setChecked(True)
        self.forceMaxHops.setToolTip("Show only routes with Max Hops+Back Hop")
        gridLayout.addWidget(self.forceMaxHops, 1, 0)

        self.onlyLpadsize = QtGui.QCheckBox("Only L Pads")
        if self.mydb.getConfig("option_mhr_onlyLpadsize"):
            self.onlyLpadsize.setChecked(True)
        self.onlyLpadsize.setToolTip("Find only stations with a large landingpad")
        gridLayout.addWidget(self.onlyLpadsize, 2, 0)


        self.autoUpdateLocation = QtGui.QCheckBox("Location Update")
        self.autoUpdateLocation.setChecked(True)
        self.autoUpdateLocation.stateChanged.connect(self.updateLocation)
        gridLayout.addWidget(self.autoUpdateLocation, 3, 0)


        label = QtGui.QLabel("Max Hops:")
        self.maxHopsspinBox = QtGui.QSpinBox()
        self.maxHopsspinBox.setRange(1, 20)
        self.maxHopsspinBox.setAlignment(QtCore.Qt.AlignRight)
        self.maxHopsspinBox.setValue(self.route.getOption("tradingHops"))
        gridLayout.addWidget(label, 1, 2)
        gridLayout.addWidget(self.maxHopsspinBox, 1, 3)


        label = QtGui.QLabel("Search Range:")
        self.searchRangeSpinBox = QtGui.QSpinBox()
        self.searchRangeSpinBox.setRange(0, 1000)
        self.searchRangeSpinBox.setSuffix("ly")
        self.searchRangeSpinBox.setAlignment(QtCore.Qt.AlignRight)
        self.searchRangeSpinBox.setValue(self.route.getOption("maxSearchRange"))
        gridLayout.addWidget(label, 1, 5)
        gridLayout.addWidget(self.searchRangeSpinBox, 1, 6)


        label = QtGui.QLabel("Max Data Age:")
        self.maxAgeSpinBox = QtGui.QSpinBox()
        self.maxAgeSpinBox.setRange(1, 1000)
        self.maxAgeSpinBox.setSuffix("Day")
        self.maxAgeSpinBox.setAlignment(QtCore.Qt.AlignRight)
        self.maxAgeSpinBox.setValue(self.route.getOption("maxAge"))
        gridLayout.addWidget(label, 1, 8)
        gridLayout.addWidget(self.maxAgeSpinBox, 1, 9)



        label = QtGui.QLabel("Min Profit:")
        self.minProfitSpinBox = QtGui.QSpinBox()
        self.minProfitSpinBox.setRange(1000, 10000)
        self.minProfitSpinBox.setSuffix("cr")
        self.minProfitSpinBox.setSingleStep(100)
        self.minProfitSpinBox.setAlignment(QtCore.Qt.AlignRight)
        self.minProfitSpinBox.setValue(self.route.getOption("minTradeProfit"))
        gridLayout.addWidget(label, 2, 2)
        gridLayout.addWidget(self.minProfitSpinBox, 2, 3)



        label = QtGui.QLabel("Max Dist:")
        self.maxDistSpinBox = QtGui.QSpinBox()
        self.maxDistSpinBox.setRange(0, 1000)
        self.maxDistSpinBox.setSuffix("ly")
        self.maxDistSpinBox.setSingleStep(1)
        self.maxDistSpinBox.setAlignment(QtCore.Qt.AlignRight)
        self.maxDistSpinBox.setValue(self.route.getOption("maxDist"))
        gridLayout.addWidget(label, 2, 5)
        gridLayout.addWidget(self.maxDistSpinBox, 2, 6)



        label = QtGui.QLabel("Max Star Dist:")
        self.maxStartDistSpinBox = QtGui.QSpinBox()
        self.maxStartDistSpinBox.setRange(10, 7000000)
        self.maxStartDistSpinBox.setSuffix("ls")
        self.maxStartDistSpinBox.setSingleStep(100)
        self.maxStartDistSpinBox.setAlignment(QtCore.Qt.AlignRight)
        self.maxStartDistSpinBox.setValue(self.route.getOption("maxStarDist"))
        gridLayout.addWidget(label, 2, 8)
        gridLayout.addWidget(self.maxStartDistSpinBox, 2, 9)



        label = QtGui.QLabel("Search Accuracy:")
        self.searchLimitOption = QtGui.QComboBox()
        searchLimitOptionsList = ["normal", "fast", "nice", "slow", "all"]
        for option in searchLimitOptionsList:
            self.searchLimitOption.addItem(option)
        if self.mydb.getConfig("option_searchLimit"):
            self.searchLimitOption.setCurrentIndex(self.mydb.getConfig("option_searchLimit"))
        label.setBuddy(self.searchLimitOption)
        # self.searchLimitOption.currentIndexChanged.connect(self.hmm)
        gridLayout.addWidget(label, 3, 2)
        gridLayout.addWidget(self.searchLimitOption, 3, 3, 1, 1)  # row,col,?,size



        label = QtGui.QLabel("Max Jump Dist:")
        self.maxJumpDistSpinBox = QtGui.QDoubleSpinBox()
        self.maxJumpDistSpinBox.setRange(0, 1000)
        self.maxJumpDistSpinBox.setSuffix("ly")
        self.maxJumpDistSpinBox.setSingleStep(1)
        self.maxJumpDistSpinBox.setAlignment(QtCore.Qt.AlignRight)
        self.maxJumpDistSpinBox.setValue(self.route.getOption("maxJumpDistance"))
        gridLayout.addWidget(label, 3, 5)
        gridLayout.addWidget(self.maxJumpDistSpinBox, 3, 6)


        label = QtGui.QLabel("Min Stock:")
        self.minStockSpinBox = QtGui.QSpinBox()
        self.minStockSpinBox.setRange(1000, 1000000)
        self.minStockSpinBox.setSingleStep(100)
        self.minStockSpinBox.setAlignment(QtCore.Qt.AlignRight)
        self.minStockSpinBox.setValue(self.route.getOption("minStock"))
        gridLayout.addWidget(label, 3, 8)
        gridLayout.addWidget(self.minStockSpinBox, 3, 9)


        locationLabel = QtGui.QLabel("Location:")
        self.locationlineEdit = guitools.LineEdit()
        self.locationlineEdit.setText(self.main.location.getLocation())
        self.locationlineEdit.textChanged.connect(self.triggerLocationChanged)

        locationButton = QtGui.QToolButton()
        locationButton.setIcon(self.guitools.getIconFromsvg("img/location.svg"))
        locationButton.clicked.connect(self.setCurentLocation)
        locationButton.setToolTip("Current Location")

        locationGroupBox = QtGui.QGroupBox()
        locationGroupBox.setFlat(True)
        locationGroupBox.setStyleSheet("""QGroupBox {border:0;margin:0;padding:0;}  margin:0;padding:0;""")

        layout = QtGui.QHBoxLayout()

        self.showOptions = QtGui.QCheckBox("Show Options")
        if self.mydb.getConfig("option_mhr_showOptions") != 0:
            self.showOptions.setChecked(True)
        self.showOptions.stateChanged.connect(self.optionsGroupBoxToggleViewAction)

        self.searchbutton = QtGui.QPushButton("Search")
        self.searchbutton.clicked.connect(self.startRouteSearch)

        layout.addWidget(locationLabel)
        layout.addWidget(locationButton)
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
        if isinstance(indexes[0].internalPointer(), RouteTreeHopItem):
            if len(self.main.dealsFromToWidget) > 1:
                menu.addAction(self.addRouteHopAsFromSystemInDealsFromToFinderAct)
                menu.addAction(self.addRouteHopAsTargetSystemInDealsFromToFinderAct)
            menu.addAction(self.markFakeItemAct)

        elif isinstance(indexes[0].internalPointer(), RouteTreeItem):
            menu.addAction(self.clipbordRouteHelperAct)
            if len(self.main.dealsFromToWidget) > 1:
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
            
    def setCurentLocation(self):
        self.locationlineEdit.setText(self.main.location.getLocation())

    def initRoute(self):
        ''' init the route on start and set saved options'''

        self.route = elite.dealsroute(self.mydb)

        tradingHops = self.mydb.getConfig('option_tradingHops')
        if tradingHops:
            self.route.setOption("tradingHops", tradingHops)

        maxJumpDistance = self.mydb.getConfig('option_maxJumpDistance')
        if maxJumpDistance:
            self.route.setOption("maxJumpDistance", maxJumpDistance)

        maxDist = self.mydb.getConfig('option_maxDist')
        if maxDist:
            self.route.setOption("maxDist", maxDist)

        maxSearchRange = self.mydb.getConfig('option_maxSearchRange')
        if maxSearchRange:
            self.route.setOption("maxSearchRange", maxSearchRange)

        minStock = self.mydb.getConfig('option_minStock')
        if minStock:
            self.route.setOption("minStock", minStock)

        maxStarDist = self.mydb.getConfig('option_maxStarDist')
        if maxStarDist:
            self.route.setOption("maxStarDist", maxStarDist)

        minTradeProfit = self.mydb.getConfig('option_minTradeProfit')
        if minTradeProfit:
            self.route.setOption("minTradeProfit", minTradeProfit)


    def saveOptions(self):
        # save last options
        self.mydb.setConfig('option_tradingHops', self.maxHopsspinBox.value())
        self.mydb.setConfig('option_maxJumpDistance', self.maxJumpDistSpinBox.value())
        self.mydb.setConfig('option_maxDist', self.maxDistSpinBox.value())
        self.mydb.setConfig('option_maxSearchRange', self.searchRangeSpinBox.value())
        self.mydb.setConfig('option_minStock', self.minStockSpinBox.value())
        self.mydb.setConfig('option_maxStarDist', self.maxStartDistSpinBox.value())
        self.mydb.setConfig('option_minTradeProfit', self.minProfitSpinBox.value())
        self.mydb.setConfig('option_searchLimit', self.searchLimitOption.currentIndex())

        self.mydb.setConfig('option_mhr_showOptions', self.showOptions.isChecked())
        self.mydb.setConfig('option_mhr_forceMaxHops', self.forceMaxHops.isChecked())

        self.mydb.setConfig('option_mhr_onlyLpadsize', self.onlyLpadsize.isChecked())

    def startRouteSearch(self):
        self.unsetActiveRoutePointer()

        self.main.lockDB()

        starttime = timeit.default_timer()

        self.route.setOption("startSystem", self.locationlineEdit.text())
        self.route.setOption("tradingHops", self.maxHopsspinBox.value())
        self.route.setOption("maxJumpDistance", self.maxJumpDistSpinBox.value())
        self.route.setOption("maxDist", self.maxDistSpinBox.value())
        self.route.setOption("maxSearchRange", self.searchRangeSpinBox.value())
        self.route.setOption("minStock", self.minStockSpinBox.value())
        self.route.setOption("maxStarDist", self.maxStartDistSpinBox.value())
        self.route.setOption("maxAge", self.maxAgeSpinBox.value())
        self.route.setOption("minTradeProfit", self.minProfitSpinBox.value())

        if self.onlyLpadsize.isChecked():
            self.route.setOption("padsize", ["L"])
        else:
            self.route.setOption("padsize", None)
            
        self.route.calcDefaultOptions()

        forceHops = None
        if self.forceMaxHops.isChecked():
            forceHops = self.maxHopsspinBox.value()
        self.route.forceHops = forceHops
        
        self.route.limitCalc(self.searchLimitOption.currentIndex())  # options (normal, fast, nice, slow, all)


        self.route.calcRoute()
        
#        self.route.printList()


        self.routeModel = RouteTreeModel(self.route, self, forceHops)
        
        QtCore.QObject.connect(self.routeModel, QtCore.SIGNAL('layoutAboutToBeChanged()'), self.routeModellayoutAboutToBeChanged)
        QtCore.QObject.connect(self.routeModel, QtCore.SIGNAL('layoutChanged()'), self.routeModellayoutChanged)
        QtCore.QObject.connect(self.routeModel, QtCore.SIGNAL('modelAboutToBeReset()'), self.routeModelmodelAboutToBeReset)
        QtCore.QObject.connect(self.routeModel, QtCore.SIGNAL('modelReset()'), self.routeModemodelReset)

        self.listView.setModel(self.routeModel)
#        routeModel.layoutChanged.emit()

        self.listView.sortByColumn(2, QtCore.Qt.SortOrder.DescendingOrder)
        self.listView.hideColumn(1)

        self.listView.show()

        self.main.setStatusBar("Route Calculated (%ss) %d routes found" % (round(timeit.default_timer() - starttime, 2), len(self.route.deals)))

        self.main.unlockDB()
        self.triggerLocationChanged()

    def routeModelmodelAboutToBeReset(self):
        if _debug:
            print("routeModelmodelAboutToBeReset")


    def routeModemodelReset(self):
        if _debug:
            print("routeModelmodelAboutToBeReset")


    def enabelSorting(self):
        self.listView.setSortingEnabled(True)
        self.enabelSortingTimer = None

    def routeModellayoutAboutToBeChanged(self):
        if _debug:
            print("routeModellayoutAboutToBeChanged")
        self.autoUpdateLocationTimer.stop()
        self.layoutLock = True

    def routeModellayoutChanged(self):
        if _debug:
            print("routeModellayoutChanged")

        for rid in range(0, self.listView.model().rowCount(QtCore.QModelIndex())):
            # rid item count
            for cid in range(0, self.listView.model().rowCount(self.listView.model().index(rid, 0))):
                # cid child item count
                self.listView.setFirstColumnSpanned(cid, self.listView.model().index(rid, 0), True)

        self.listView.expandToDepth(1)

#        for i in range(0, 7):
#            self.listView.resizeColumnToContents(i)

        self.layoutLock = None

        self.triggerLocationChanged()
        self.autoUpdateLocationTimer.start()


    def createTimer(self):
        self.autoUpdateLocationTimer = QtCore.QTimer()
        self.autoUpdateLocationTimer.start(1000 * 60)
        self.autoUpdateLocationTimer.timeout.connect(self.updateLocation)

    def updateLocation(self):
        if self.autoUpdateLocation.isChecked():

            self.autoUpdateLocationTimer.stop()

            location = self.main.location.getLocation()
            if not location:
                print("stop update location")
                self.autoUpdateLocation.setChecked(False)
                return

            self.locationlineEdit.setText(location)

            self.autoUpdateLocationTimer.start()
        else:
            print("stop update location timer")
            self.autoUpdateLocationTimer.stop()

        
    def triggerLocationChanged(self):
        if _debug:
            print("triggerLocationChanged")

        if self.route.locked or self.layoutLock:
            return

        self.updateConnectedDealsFromToWindow()
        self.setLocationColors()

    def setLocationColors(self):
        if _debug:
            print("setLocationColors")
        location = self.locationlineEdit.text()

        if self.route.locked or self.layoutLock:
            return

        if not self.listView.model() or not self.listView.model().rowCount():
            return
        hopID = self.getCurrentHopFromActiveRoute()  # only to fill deal["lastHop"]

        if location and self.listView.model():
            for rid in range(0, self.listView.model().rowCount(QtCore.QModelIndex())):
                if self.layoutLock:
                    return
                guiRroute = self.listView.model().index(rid, 0).internalPointer()
                hopID = -1
                for cid in range(0, guiRroute.childCount()):
                    child = guiRroute.child(cid)
                    # print(child)
                    if isinstance(child, RouteTreeHopItem):
                        hopID += 1
                        deal = child.parent().getInternalRoutePointer()
                        if self.route.getSystemA(deal, hopID).lower() == location.lower():
                            if deal["activeRoute"]:
                                child.setBGColor(QtGui.QColor(0, 255, 0, 128))
                            else:
                                child.setBGColor(QtGui.QColor(255, 255, 128, 255))
                        elif deal["activeRoute"] and hopID == deal["lastHop"]:
                                child.setBGColor(QtGui.QColor(0, 255, 0, 64))
                        else:
                            child.setBGColor(None)

        self.listView.dataChanged(self.listView.model().index(0, 0), self.listView.model().index(self.listView.model().rowCount(QtCore.QModelIndex()), 0))

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
 
        if isinstance(indexes[0].internalPointer(), RouteTreeItem):
            if self.activeRoutePointer:
                self.activeRoutePointer["activeRoute"] = None

            self.activeRoutePointer = indexes[0].internalPointer().getInternalRoutePointer()
            
            self.activeRoutePointer["activeRoute"] = True

    def unsetActiveRoutePointer(self):
        if self.activeRoutePointer:
            self.activeRoutePointer["activeRoute"] = None
        self.activeRoutePointer = None

    def clipbordRouteHelper(self):
        self.setActiveRoutePointer()

        self.timer_setNextRouteHopToClipbord = QtCore.QTimer()
        self.timer_setNextRouteHopToClipbord.start(1000 * 60)
        self.timer_setNextRouteHopToClipbord.timeout.connect(self.setNextRouteHopToClipbord)

        self.clipbordRouteHelperAct.setChecked(True)
        self.setNextRouteHopToClipbord(init=True)
        self.triggerLocationChanged()
        
    def setNextRouteHopToClipbord(self, init=None):
        ''' helper to set next route hop to clipboard '''
        if _debug:
            print("setNextRouteHopToClipbord")

        if not self.activeRoutePointer:
            return
        
        clipbordText = self.main.clipboard.text()

        if init:
            self.lastClipboardEntry = None
        elif self.lastClipboardEntry != clipbordText:
            # stop timer and job do other tool use the clipbord
            print("setNextRouteHopToClipbord stop job")
            self.timer_setNextRouteHopToClipbord.stop()
            self.clipbordRouteHelperAct.setChecked(False)
            return

        
        hopID = self.getCurrentHopFromActiveRoute()
        if hopID is not None:
            systemA = self.route.getSystemB(self.activeRoutePointer, hopID)

            if systemA != clipbordText:
                systemB = self.route.getSystemB(self.activeRoutePointer, hopID)
                self.main.clipboard.setText(systemB)
                self.lastClipboardEntry = systemB
                print("setNextRouteHopToClipbord1 set clipboard to", systemB)

        if not self.lastClipboardEntry:
            # not in route? set the first hop to clipboard
            system = self.route.getSystemA(self.activeRoutePointer, 0)
            if system:
                self.main.clipboard.setText(system)
                self.lastClipboardEntry = system
    
                print("setNextRouteHopToClipbord2 set clipboard to", system)

        self.timer_setNextRouteHopToClipbord.start()
    
    def markFakeItem(self):

        route, hopID = self.getSelectedRouteHopID()
        priceID = self.route.getPriceID(route, hopID)
        if priceID:

            msgBox = QtGui.QMessageBox(QtGui.QMessageBox.Warning,
                    "Warning", "Warning: fake items are ignored everywhere and no longer displayed",
                    QtGui.QMessageBox.NoButton, self)

            msgBox.addButton("Save as Facke", QtGui.QMessageBox.AcceptRole)
            msgBox.addButton("Cancel", QtGui.QMessageBox.RejectRole)

            if msgBox.exec_() == QtGui.QMessageBox.AcceptRole:
                print("set %s as fakeprice" % priceID)
                self.main.lockDB()
                self.mydb.setFakePrice(priceID)
                self.main.unlockDB()

    def getSelectedRouteHopID(self):
        if _debug:
            print("getSelectedRouteHopID")

        indexes = self.listView.selectionModel().selectedIndexes()
        
        if isinstance(indexes[0].internalPointer(), RouteTreeHopItem):

            hopID = indexes[0].internalPointer().parent().hopPos(indexes)
            
            route = indexes[0].internalPointer().parent().getInternalRoutePointer()
            
            return (route, hopID)

        return (None, None)

    def addRouteHopAsTargetSystemInDealsFromToFinder(self):
        if _debug:
            print("addRouteHopAsTargetSystemInDealsFromToFinder")

        route, hopID = self.getSelectedRouteHopID()
        if route is None or hopID is None:
            return

        toStation = self.route.getStationA(route, hopID)
        toSystem = self.route.getSystemA(route, hopID)
        # TODO: set it only in first Deals window current
        if toSystem and toStation:
            self.main.dealsFromToWidget[1].toSystem.setText(toSystem)
            self.main.dealsFromToWidget[1].toStation.setText(toStation)

    def addRouteHopAsFromSystemInDealsFromToFinder(self):

        route, hopID = self.getSelectedRouteHopID()
        if route is None or hopID is None:
            return

        station = self.route.getStationA(route, hopID)
        system = self.route.getSystemA(route, hopID)
        # TODO: set it only in first Deals window current
        if system and station:
            self.main.dealsFromToWidget[1].fromSystem.setText(system)
            self.main.dealsFromToWidget[1].fromStation.setText(station)

    def connectToDealsFromToWindows(self):
        if _debug:
            print("connectToDealsFromToWindows")
        if self.connectedDealsFromToWindows:
            indexes = self.listView.selectionModel().selectedIndexes()
            if self.activeRoutePointer == indexes[0].internalPointer().getInternalRoutePointer():
                self.connectedDealsFromToWindows = None
                return

        if self.main.dealsFromToWidget:
            self.setActiveRoutePointer()
            self.triggerLocationChanged()

            self.connectedDealsFromToWindows = self.main.dealsFromToWidget[1]
            self.connectedDealsFromToWindows.autoUpdateLocation.setChecked(False)

            self.updateConnectedDealsFromToWindow(init=True)

    def disconnectFromDealsFromToWindow(self):
        self.connectedDealsFromToWindows = None

    def getCurrentHopFromActiveRoute(self):
        if _debug:
            print("getCurrentHopFromActiveRoute")
        if not self.activeRoutePointer:
            return
        
        location = self.main.location.getLocation()

        hopCount = len(self.activeRoutePointer["path"])

        for i in range(0, hopCount + 1):
            if not self.activeRoutePointer["lastHop"]:
                cid = i
            else:
                cid = self.activeRoutePointer["lastHop"] + i

                if cid > hopCount:
                    cid = i - self.activeRoutePointer["lastHop"]

            systemA = self.route.getSystemA(self.activeRoutePointer, cid)

            if systemA == location:
                hopID = cid
                if hopID > hopCount:
                    hopID = 0
                self.activeRoutePointer["lastHop"] = hopID
                print("return", hopID)
                return hopID

    def updateConnectedDealsFromToWindow(self, init=None):
        if _debug:
            print("updateConnectedDealsFromToWindow")
        if not self.connectedDealsFromToWindows or not self.activeRoutePointer:
            return

        
        hopID = self.getCurrentHopFromActiveRoute()
        if hopID is None and init:
            ''' is init and im not inside the route set only the To part from first hop '''
            systemA = self.route.getSystemA(self.activeRoutePointer, 0)
            stationA = self.route.getStationA(self.activeRoutePointer, 0)

            self.connectedDealsFromToWindows.toSystem.setText(systemA)
            self.connectedDealsFromToWindows.toStation.setText(stationA)
            return


        if hopID is None:
            return

        systemA = self.route.getSystemA(self.activeRoutePointer, hopID)
        stationA = self.route.getStationA(self.activeRoutePointer, hopID)

        systemB = self.route.getSystemB(self.activeRoutePointer, hopID)
        stationB = self.route.getStationB(self.activeRoutePointer, hopID)

        self.connectedDealsFromToWindows.fromSystem.setText(systemA)
        self.connectedDealsFromToWindows.fromStation.setText(stationA)

        self.connectedDealsFromToWindows.toSystem.setText(systemB)
        self.connectedDealsFromToWindows.toStation.setText(stationB)
