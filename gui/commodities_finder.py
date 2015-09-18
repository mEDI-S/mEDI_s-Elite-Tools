# -*- coding: UTF8

'''
Created on 18.09.2015

@author: mEDI
'''
from PySide import QtCore, QtGui
import PySide

import gui.guitools as guitools
from datetime import datetime, timedelta

__toolname__ = "Commodities Finder"
__internalName__ = "CoFi"
__statusTip__ = "Open A %s Window" % __toolname__

class tool(QtGui.QWidget):
    main = None
    mydb = None

    def __init__(self, main):
        super(tool, self).__init__(main)

        self.main = main
        self.mydb = main.mydb

        self.guitools = guitools.guitools(self)
        self.createActions()

        
    def getWideget(self):


        gridLayout = QtGui.QGridLayout()

        gridLayout.setColumnStretch(1, 1)
        gridLayout.setColumnStretch(4, 1)
        gridLayout.setColumnStretch(7, 1)


        self.onlyLocation = QtGui.QCheckBox("Only Location")
        if self.mydb.getConfig("option_cf_onlyLocation"):
            self.onlyLocation.setChecked(True)
        else:
            self.onlyLocation.setChecked(False)
        self.onlyLocation.stateChanged.connect( self.searchItem )
        gridLayout.addWidget(self.onlyLocation, 1, 0)


        self.onlyLpadsize = QtGui.QCheckBox("Only L Pads")
        if self.mydb.getConfig("option_cf_onlyLpadsize"):
            self.onlyLpadsize.setChecked(True)
        self.onlyLpadsize.setToolTip("Find only stations with a large landingpad")
        self.onlyLpadsize.stateChanged.connect( self.searchItem )
        gridLayout.addWidget(self.onlyLpadsize, 2, 0)


        label = QtGui.QLabel("Search Range:")
        self.searchRangeSpinBox = QtGui.QSpinBox()
        self.searchRangeSpinBox.setRange(0, 1000)
        self.searchRangeSpinBox.setSuffix("ly")
        self.searchRangeSpinBox.setAlignment(QtCore.Qt.AlignRight)
        if self.mydb.getConfig("option_cf_maxSearchRange"):
            self.searchRangeSpinBox.setValue(self.mydb.getConfig("option_cf_maxSearchRange"))
        gridLayout.addWidget(label, 1, 2)
        gridLayout.addWidget(self.searchRangeSpinBox, 1, 3)


        label = QtGui.QLabel("Allegiances:")
        self.allegiancesComboBox = QtGui.QComboBox()

        allegiances = self.mydb.getAllegiances()
        self.allegiancesList = []
        self.allegiancesComboBox.addItem( "Any" )
        self.allegiancesList.append(None)

        for allegiance in allegiances:
            self.allegiancesComboBox.addItem( allegiance["Name"] )
            self.allegiancesList.append(allegiance["id"])
        if self.mydb.getConfig("option_cf_allegiances"):
            self.allegiancesComboBox.setCurrentIndex(self.mydb.getConfig("option_cf_allegiances"))
        self.allegiancesComboBox.currentIndexChanged.connect(self.searchItem)
        gridLayout.addWidget(label, 1, 5)
        gridLayout.addWidget(self.allegiancesComboBox, 1, 6)



        label = QtGui.QLabel("Max Data Age:")
        self.maxAgeSpinBox = QtGui.QSpinBox()
        self.maxAgeSpinBox.setRange(1, 1000)
        self.maxAgeSpinBox.setSuffix("Day")
        self.maxAgeSpinBox.setAlignment(QtCore.Qt.AlignRight)
        if self.mydb.getConfig("option_cf_maxAge"):
            self.maxAgeSpinBox.setValue(self.mydb.getConfig("option_cf_maxAge"))
        else:
            self.maxAgeSpinBox.setValue(14)
        gridLayout.addWidget(label, 1, 8)
        gridLayout.addWidget(self.maxAgeSpinBox, 1, 9)


        label = QtGui.QLabel("Buy/Sell:")
        self.buySellComboBox = QtGui.QComboBox()
        buySellList = ["Any", "Buy", "Sell"]
        for item in buySellList:
            self.buySellComboBox.addItem( item )
        if self.mydb.getConfig("option_cf_buySell"):
            self.buySellComboBox.setCurrentIndex(self.mydb.getConfig("option_cf_buySell"))
        self.buySellComboBox.currentIndexChanged.connect(self.searchItem)
        gridLayout.addWidget(label, 2, 2)
        gridLayout.addWidget(self.buySellComboBox, 2, 3)



        label = QtGui.QLabel("Governments:")
        self.governmentsComboBox = QtGui.QComboBox()

        governments = self.mydb.getGovernments()
        self.governmentsList = []
        self.governmentsComboBox.addItem( "Any" )
        self.governmentsList.append(None)

        for government in governments:
            self.governmentsComboBox.addItem( government["Name"] )
            self.governmentsList.append(government["id"])
        if self.mydb.getConfig("option_cf_governments"):
            self.governmentsComboBox.setCurrentIndex(self.mydb.getConfig("option_cf_governments"))
        self.governmentsComboBox.currentIndexChanged.connect(self.searchItem)
        gridLayout.addWidget(label, 2, 5)
        gridLayout.addWidget(self.governmentsComboBox, 2, 6)


        label = QtGui.QLabel("Max Star Dist:")
        self.maxStartDistSpinBox = QtGui.QSpinBox()
        self.maxStartDistSpinBox.setRange(10, 7000000)
        self.maxStartDistSpinBox.setSuffix("ls")
        self.maxStartDistSpinBox.setSingleStep(10)
        self.maxStartDistSpinBox.setAlignment(QtCore.Qt.AlignRight)
        maxStarDist = self.mydb.getConfig( 'option_cf_maxStarDist' )
        if maxStarDist:
            self.maxStartDistSpinBox.setValue( maxStarDist )
        else:
            self.maxStartDistSpinBox.setValue( 1500 )
        gridLayout.addWidget(label, 2, 8)
        gridLayout.addWidget(self.maxStartDistSpinBox, 2, 9)



        self.optionsGroupBox = QtGui.QGroupBox("Options")
        self.optionsGroupBox.setLayout(gridLayout)


        locationButton = QtGui.QToolButton()
        locationButton.setIcon(self.guitools.getIconFromsvg("img/location.svg"))
        locationButton.clicked.connect(self.setCurentLocation)
        locationButton.setToolTip("Current Location")



        locationLabel = QtGui.QLabel("Location:")
        self.locationlineEdit = guitools.LineEdit()
        self.locationlineEdit.setText( self.main.location.getLocation() )
        self.locationlineEdit.textChanged.connect(self.searchItem)


        nameLabel = QtGui.QLabel("Name:")
        self.itemComboBox = QtGui.QComboBox()

        items = self.mydb.getAllItemNames()
        self.itemList = []
        self.itemComboBox.addItem( "Any" )
        self.itemList.append(None)

        for item in items:
            self.itemComboBox.addItem( item["name"] )
            self.itemList.append(item["id"])
        if self.mydb.getConfig("option_cf_item"):
            self.itemComboBox.setCurrentIndex(self.mydb.getConfig("option_cf_item"))
        self.itemComboBox.currentIndexChanged.connect(self.searchItem)

        self.showOptions = QtGui.QCheckBox("Show Options")
        if self.mydb.getConfig("option_cf_showOptions") != 0:
            self.showOptions.setChecked(True)
        self.showOptions.stateChanged.connect( self.optionsGroupBoxToggleViewAction )


        self.searchbutton = QtGui.QPushButton("Search")
        self.searchbutton.clicked.connect(self.searchItem)



        layout = QtGui.QHBoxLayout()
        layout.setContentsMargins(0,0,0,0)

        layout.addWidget(locationLabel)
        layout.addWidget(locationButton)
        
        layout.addWidget(self.locationlineEdit)
        layout.addWidget(nameLabel)
        layout.addWidget(self.itemComboBox)
        layout.addWidget(self.showOptions)
        
        layout.addWidget(self.searchbutton)

        locationGroupBox = QtGui.QGroupBox()
        locationGroupBox.setFlat(True)
        locationGroupBox.setStyleSheet("""QGroupBox {border:0;margin:0;padding:0;}  margin:0;padding:0;""")

        #locationGroupBox.setFlat(True)
        locationGroupBox.setLayout(layout)


        self.listView = QtGui.QTreeView()

#        self.proxyModel = QtGui.QSortFilterProxyModel()
#        self.proxyModel.setDynamicSortFilter(True)

        self.listView.setRootIsDecorated(False)
        self.listView.setAlternatingRowColors(True)
#        self.listView.setModel(self.proxyModel)
        self.listView.setSortingEnabled(True)

        self.listView.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.listView.setSelectionBehavior(QtGui.QAbstractItemView.SelectItems)

        self.listView.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.listView.customContextMenuRequested.connect(self.myContextMenuEvent)


        vGroupBox = QtGui.QGroupBox()
        vGroupBox.setFlat(True)

        layout = QtGui.QVBoxLayout()
        layout.setContentsMargins(6,2,6,6)

        layout.addWidget(self.optionsGroupBox)
        layout.addWidget(locationGroupBox)
        layout.addWidget(self.listView)



        vGroupBox.setLayout(layout)

        self.guitools.setSystemComplete("", self.locationlineEdit)

        self.optionsGroupBoxToggleViewAction()

        return vGroupBox


    def myContextMenuEvent(self, event):
        menu = QtGui.QMenu(self)

        menu.addAction(self.copyAct)

        menu.exec_(self.listView.viewport().mapToGlobal(event))

    def optionsGroupBoxToggleViewAction(self):
        if self.showOptions.isChecked():
            self.optionsGroupBox.show()
        else:
            self.optionsGroupBox.hide()

    def createActions(self):
        self.copyAct = QtGui.QAction("Copy", self, triggered=self.guitools.copyToClipboard, shortcut=QtGui.QKeySequence.Copy)



    def setCurentLocation(self):
        self.locationlineEdit.setText( self.main.location.getLocation() )


    def saveOptions(self):
        self.mydb.setConfig( 'option_cf_onlyLpadsize', self.onlyLpadsize.isChecked() )
        self.mydb.setConfig( 'option_cf_onlyLocation', self.onlyLocation.isChecked() )
        self.mydb.setConfig( 'option_cf_maxSearchRange', self.searchRangeSpinBox.value() )
        self.mydb.setConfig( 'option_cf_maxAge', self.maxAgeSpinBox.value() )
        self.mydb.setConfig( 'option_cf_maxStarDist', self.maxStartDistSpinBox.value() )
        self.mydb.setConfig( 'option_cf_showOptions', self.showOptions.isChecked() )
        self.mydb.setConfig( 'option_cf_item', self.itemComboBox.currentIndex() )
        self.mydb.setConfig( 'option_cf_buySell', self.buySellComboBox.currentIndex() )
        self.mydb.setConfig( 'option_cf_allegiances', self.allegiancesComboBox.currentIndex() )
        self.mydb.setConfig( 'option_cf_governments', self.governmentsComboBox.currentIndex() )

        sectionPosList = []
        for i in range( self.listView.header().count() ):
            sectionPosList.append( self.listView.header().logicalIndex( i ) )

        sectionPos = ",".join( map( str, sectionPosList ) )
        self.mydb.setConfig( 'option_cf.header.sectionPos', sectionPos )


    def searchItem(self):

        firstrun = False
        if not self.listView.header().count():
            firstrun = True

        self.headerList = ["System", "Permit","StarDist", "Station", "Distance", "Item", "Stock",  "Buy", "Demand", "Sell", "Age", ""]

        model = QtGui.QStandardItemModel(0, len(self.headerList), self)
        for x,column in enumerate(self.headerList):
            model.setHeaderData(x, QtCore.Qt.Horizontal, column)

        location = self.locationlineEdit.text()
        systemID = self.mydb.getSystemIDbyName(location)

        if self.onlyLocation.isChecked():
            distance = 0
        else:
            distance = self.searchRangeSpinBox.value()
            
        maxAgeDate = datetime.utcnow() - timedelta(days = self.maxAgeSpinBox.value() )

        itemID = self.itemList[ self.itemComboBox.currentIndex() ]

        items = self.mydb.getPricesInDistance( systemID, distance, self.maxStartDistSpinBox.value(), maxAgeDate, itemID, self.onlyLpadsize.isChecked(), self.buySellComboBox.currentIndex(), self.allegiancesComboBox.currentIndex(), self.governmentsComboBox.currentIndex())


        for item in items:
            model.insertRow(0)
            model.setData(model.index(0, self.headerList.index("System") ), item["System"])

            model.setData(model.index(0, self.headerList.index("Permit") ),  "No" if not item["permit"] else "Yes" )
            model.item(0, self.headerList.index("Permit")).setTextAlignment(QtCore.Qt.AlignCenter)

            model.setData(model.index(0, self.headerList.index("StarDist") ), item["StarDist"])
            model.item(0, self.headerList.index("StarDist")).setTextAlignment(QtCore.Qt.AlignRight)

            model.setData(model.index(0, self.headerList.index("Station") ), item["Station"])

            if "dist" in item:
                model.setData(model.index(0, self.headerList.index("Distance") ),  item["dist"])
            else:
                model.setData(model.index(0, self.headerList.index("Distance") ),  0)
            model.item(0, self.headerList.index("Distance")).setTextAlignment(QtCore.Qt.AlignRight)

            model.setData(model.index(0, self.headerList.index("Item") ),  item["name"])

            model.setData(model.index(0, self.headerList.index("Stock") ),  item["Stock"])
            model.item(0, self.headerList.index("Stock")).setTextAlignment(QtCore.Qt.AlignRight)

            model.setData(model.index(0, self.headerList.index("Buy") ),  item["StationSell"])
            model.item(0, self.headerList.index("Buy")).setTextAlignment(QtCore.Qt.AlignRight)

            model.setData(model.index(0, self.headerList.index("Demand") ),  item["Dammand"])
            model.item(0, self.headerList.index("Demand")).setTextAlignment(QtCore.Qt.AlignRight)

            model.setData(model.index(0, self.headerList.index("Sell") ),  item["StationBuy"])
            model.item(0, self.headerList.index("Sell")).setTextAlignment(QtCore.Qt.AlignRight)

            model.setData(model.index(0, self.headerList.index("Age") ), guitools.convertDateimeToAgeStr(item["age"]) )
            model.item(0, self.headerList.index("Age")).setTextAlignment(QtCore.Qt.AlignCenter)

        self.listView.setModel(model)

        if firstrun:
            sectionPos  = self.mydb.getConfig( 'option_cf.header.sectionPos' )
            if sectionPos:
                sectionPosList = sectionPos.strip().split( ',' )
                for i,pos in  enumerate(sectionPosList):    
                    self.listView.header().moveSection( self.listView.header().visualIndex( int(pos) ) , i )

            self.listView.sortByColumn( self.headerList.index("Distance"), PySide.QtCore.Qt.SortOrder.AscendingOrder )

        for i in range(0, len(self.headerList) ):
            self.listView.resizeColumnToContents(i)
