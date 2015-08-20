# -*- coding: UTF8

'''
Created on 19.08.2015

@author: mEDI
'''
from PySide import QtCore, QtGui
import elite



class RouteTreeChildItem(object):
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
        if isinstance( self.itemData, str):
            return 1
        else:
            return len(self.itemData)

    def data(self, column):
        if isinstance( self.itemData, str):
            if column == 5:
                return self.itemData
        else:
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




class RouteTreeItem(object):
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


class RouteTreeModel(QtCore.QAbstractItemModel):
    def __init__(self, route, parent=None):
        super(RouteTreeModel, self).__init__(parent)
        self.route = route
        self.rootItem = RouteTreeItem(("Nr.","Profit/h", "Profit","StartDist","Laps/h","LapTime" ))
        self.setupModelData(route.deals, self.rootItem)

    def columnCount(self, parent):
        if parent.isValid():
            return parent.internalPointer().columnCount()
        else:
            return self.rootItem.columnCount()

    def data(self, index, role):
        if not index.isValid():
            return None

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

    def index(self, row, column, parent):
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

    def rowCount(self, parent):
        if parent.column() > 0:
            return 0

        if not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()

        return parentItem.childCount()

    def setupModelData(self, deals, parent):
        parents = [parent]
        indentations = [0]

        number = 0

        for i, deal in enumerate(deals):
            if i >= 40: break

            timeT = "%s:%s" % (divmod(deal["time"] * deal["lapsInHour"], 60))
            timeL = "%s:%s" % (divmod(deal["time"], 60))
            
            columnData = [i+1 , deal["profitHour"], deal["profit"], deal["path"][0]["startDist"], "%s/%s" % (deal["lapsInHour"], timeT), timeL]
            parents[-1].appendChild(RouteTreeItem(columnData, parents[-1]))
#            parents = []

            before = { "StationB":deal["path"][0]["StationA"], "SystemB":deal["path"][0]["SystemA"], "StarDist":deal["path"][0]["stationA.StarDist"], "refuel":deal["path"][0]["stationA.refuel"]  }
            #follow is a child
            parents.append(parents[-1].child(parents[-1].childCount() - 1))
        
            for x,d in enumerate(deal["path"]):
                #print(d.keys())
                columnData = "%s : %s (%d ls) (%s buy:%d sell:%d profit:%d) (%s ly)-> %s:%s" % (before["SystemB"], before["StationB"], before["StarDist"] , d["itemName"],d["StationSell"], d["StationBuy"],  d["profit"], d["dist"],d["SystemB"],d["StationB"] )


#                Item =  QtGui.QTreeWidgetItem()
#                Item.setText(0,columnData)
#                parents[-1].appendChild(Item)
                parents[-1].appendChild(RouteTreeChildItem(columnData, parents[-1]))

                if before["refuel"] != 1:
                    columnData = "\tWarning: %s have no refuel!?" % before["StationB"]
                    parents[-1].appendChild(RouteTreeChildItem(columnData, parents[-1]))
                
                before = d

        
            backdist = self.route.mydb.getDistanceFromTo(deal["path"][0]["SystemAID"] , deal["path"][ len(deal["path"])-1 ]["SystemBID"])
        
            if deal["backToStartDeal"]:
                #print(deal["backToStartDeal"].keys())
                columnData = "%s : %s (%d ls) (%s buy:%d sell:%d profit:%d) (%s ly)-> %s:%s" % (before["SystemB"], deal["backToStartDeal"]["fromStation"] , before["StarDist"], deal["backToStartDeal"]["itemName"], deal["backToStartDeal"]["StationSell"],deal["backToStartDeal"]["StationBuy"],  deal["backToStartDeal"]["profit"], backdist, deal["path"][0]["SystemA"], deal["path"][0]["StationA"] ) 
            else:
                columnData = "no back deal (%s ly) ->%s : %s" % (backdist, deal["path"][0]["SystemA"], deal["path"][0]["StationA"]  )

            parents[-1].appendChild(RouteTreeChildItem(columnData, parents[-1]))
        
            if before["refuel"] != 1:
                columnData = "\tWarning: %s have no refuel!?" % before["StationB"]
                parents[-1].appendChild(RouteTreeChildItem(columnData, parents[-1]))
        
            # not more a child
            parents.pop()




class Widget(QtGui.QWidget):
    main = None
    route = None
        
    def __init__(self, main):
        super(Widget, self).__init__(main)

        self.main = main
        self.createActions()
        self.route = elite.dealsroute(self.main.mydb)


    def getWideget(self):

        gridLayout = QtGui.QGridLayout()

        label = QtGui.QLabel("Max Hops:")
        self.maxHopsspinBox = QtGui.QSpinBox()
        self.maxHopsspinBox.setRange(1, 10)
        self.maxHopsspinBox.setValue( self.route.getOption("tradingHops"))
        gridLayout.addWidget(label, 1, 0)
        gridLayout.addWidget(self.maxHopsspinBox, 1, 1)

        label = QtGui.QLabel("Search Range:")
        self.searchRangeSpinBox = QtGui.QSpinBox()
        self.searchRangeSpinBox.setRange(0, 1000)
        self.searchRangeSpinBox.setSuffix("ly")
        self.searchRangeSpinBox.setValue( self.route.getOption("maxSearchRange") )
        gridLayout.addWidget(label, 1, 2)
        gridLayout.addWidget(self.searchRangeSpinBox, 1, 3)


        label = QtGui.QLabel("Max Data Age:")
        self.maxAgeSpinBox = QtGui.QSpinBox()
        self.maxAgeSpinBox.setRange(1, 1000)
        self.maxAgeSpinBox.setSuffix("Day")
        self.maxAgeSpinBox.setValue( self.route.getOption("maxAge") )
        gridLayout.addWidget(label, 1, 4)
        gridLayout.addWidget(self.maxAgeSpinBox, 1, 5)



        label = QtGui.QLabel("Max Dist:")
        self.maxDistSpinBox = QtGui.QSpinBox()
        self.maxDistSpinBox.setRange(0, 1000)
        self.maxDistSpinBox.setSuffix("ly")
        self.maxDistSpinBox.setSingleStep(1)
        self.maxDistSpinBox.setValue( self.route.getOption("maxDist") )
        gridLayout.addWidget(label, 2, 2)
        gridLayout.addWidget(self.maxDistSpinBox, 2, 3)


        label = QtGui.QLabel("Max Star Dist:")
        self.maxStartDistSpinBox = QtGui.QSpinBox()
        self.maxStartDistSpinBox.setRange(10, 7000000)
        self.maxStartDistSpinBox.setSuffix("ls")
        self.maxStartDistSpinBox.setSingleStep(10)
        self.maxStartDistSpinBox.setValue( self.route.getOption("maxStarDist") )
        gridLayout.addWidget(label, 2, 4)
        gridLayout.addWidget(self.maxStartDistSpinBox, 2, 5)


        label = QtGui.QLabel("Min Profit:")
        self.minProfitSpinBox = QtGui.QSpinBox()
        self.minProfitSpinBox.setRange(1000, 10000)
        self.minProfitSpinBox.setSuffix("cr")
        self.minProfitSpinBox.setSingleStep(100)
        self.minProfitSpinBox.setValue( self.route.getOption("minTradeProfit") )
        gridLayout.addWidget(label, 2, 0)
        gridLayout.addWidget(self.minProfitSpinBox, 2, 1)


        label = QtGui.QLabel("Max Jump Dist:")
        self.maxJumpDistSpinBox = QtGui.QDoubleSpinBox()
        self.maxJumpDistSpinBox.setRange(0, 1000)
        self.maxJumpDistSpinBox.setSuffix("ly")
        self.maxJumpDistSpinBox.setSingleStep(1)
        self.maxJumpDistSpinBox.setValue( self.route.getOption("maxJumpDistance") )
        gridLayout.addWidget(label, 3, 2)
        gridLayout.addWidget(self.maxJumpDistSpinBox, 3, 3)


        label = QtGui.QLabel("Min Stock:")
        self.minStockSpinBox = QtGui.QSpinBox()
        self.minStockSpinBox.setRange(1000, 1000000)
        self.minStockSpinBox.setSingleStep(100)
        self.minStockSpinBox.setValue( self.route.getOption("minStock") )
        gridLayout.addWidget(label, 3, 4)
        gridLayout.addWidget(self.minStockSpinBox, 3, 5)


        locationLabel = QtGui.QLabel("Location:")
        self.locationlineEdit = QtGui.QLineEdit()
        self.locationlineEdit.setText( self.main.location.getLocation() )


        locationGroupBox = QtGui.QGroupBox()
        layout = QtGui.QHBoxLayout()

        self.showOptions = QtGui.QCheckBox("Show Options")
        self.showOptions.setChecked(True)
        self.showOptions.stateChanged.connect( self.optionsGroupBoxToggleViewAction )

        self.searchbutton = QtGui.QPushButton("Search")
        self.searchbutton.clicked.connect(self.startRouteSearch)

        layout.addWidget(locationLabel)
        layout.addWidget(self.locationlineEdit)
        layout.addWidget(self.showOptions)
        
        layout.addWidget(self.searchbutton)

        locationGroupBox.setLayout(layout)
        locationGroupBox.setFlat(True)


        self.optionsGroupBox = QtGui.QGroupBox("Options")
        self.optionsGroupBox.setLayout(gridLayout)

        self.routeview = QtGui.QTreeView()


        vGroupBox = QtGui.QGroupBox("Search")
        vGroupBox.setFlat(True)
        layout = QtGui.QVBoxLayout()

        layout.addWidget(self.optionsGroupBox)
        layout.addWidget(locationGroupBox)
        layout.addWidget(self.routeview)



        vGroupBox.setLayout(layout)

        return vGroupBox

    def optionsGroupBoxToggleViewAction(self):
        if not self.optionsGroupBox.isHidden():
            self.optionsGroupBox.hide()
        else:
            self.optionsGroupBox.show()

    def startRouteSearch(self):

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
        
        self.route.limitCalc("normal") #options (normal, fast, nice, slow, all)
        
        self.route.calcRoute()
        
        self.route.printList()

        routeModel = RouteTreeModel(self.route)
        self.routeview.setModel(routeModel)
        self.routeview.expandToDepth(1)
        for i in range(0, 5):
            self.routeview.resizeColumnToContents(i)
        
        self.routeview.show()
        
    def createActions(self):
        pass
        