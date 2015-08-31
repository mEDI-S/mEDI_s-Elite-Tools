# -*- coding: UTF8

'''
Created on 30.08.2015

@author: mEDI
'''
from PySide import QtCore, QtGui
import PySide

import gui.guitools as guitools

__toolname__ = "Shipyard Finder"
__statusTip__ = "Open A %s Window" % __toolname__

class tool(QtGui.QWidget):
    main = None
    mydb = None
    route = None

    def __init__(self, main):
        super(tool, self).__init__(main)

        self.main = main
        self.mydb = main.mydb
        self.guitools = guitools.guitools(self)

    def getWideget(self):



        locationButton = QtGui.QToolButton()
        locationButton.setIcon(self.guitools.getIconFromsvg("img/location.svg"))
        locationButton.clicked.connect(self.setCurentLocation)
        locationButton.setToolTip("Current Location")



        locationLabel = QtGui.QLabel("Location:")
        self.locationlineEdit = guitools.LineEdit()
        self.locationlineEdit.setText( self.main.location.getLocation() )
        self.locationlineEdit.textChanged.connect(self.searchShip)


        ShipLabel = QtGui.QLabel("Ship:")
        self.shipComboBox = QtGui.QComboBox()

        ships = self.mydb.getAllShipnames()
        self.shipList = []
        for ship in ships:
            self.shipComboBox.addItem( ship["Name"] )
            self.shipList.append(ship["id"])
        self.shipComboBox.currentIndexChanged.connect(self.searchShip)

        self.searchbutton = QtGui.QPushButton("Search")
        self.searchbutton.clicked.connect(self.searchShip)



        layout = QtGui.QHBoxLayout()

        layout.addWidget(locationLabel)
        layout.addWidget(locationButton)
        
        layout.addWidget(self.locationlineEdit)
        layout.addWidget(ShipLabel)
        layout.addWidget(self.shipComboBox)
        
        layout.addWidget(self.searchbutton)

        locationGroupBox = QtGui.QGroupBox()
        #locationGroupBox.setFlat(True)
        locationGroupBox.setLayout(layout)


        self.shipsview = QtGui.QTreeView()

        self.proxyModel = QtGui.QSortFilterProxyModel()
        self.proxyModel.setDynamicSortFilter(True)

        self.shipsview.setRootIsDecorated(False)
        self.shipsview.setAlternatingRowColors(True)
        self.shipsview.setModel(self.proxyModel)
        self.shipsview.setSortingEnabled(True)



        vGroupBox = QtGui.QGroupBox()
        vGroupBox.setFlat(True)

        layout = QtGui.QVBoxLayout()

        layout.addWidget(locationGroupBox)
        layout.addWidget(self.shipsview)



        vGroupBox.setLayout(layout)

        self.guitools.setSystemComplete("", self.locationlineEdit)
        
        return vGroupBox



    def setCurentLocation(self):
        self.locationlineEdit.setText( self.main.location.getLocation() )


    def searchShip(self):

        firstrun = False
        if not self.shipsview.header().count():
            firstrun = True

        self.headerList = ["System", "Station", "Distance", "Age"]

        model = QtGui.QStandardItemModel(0, len(self.headerList), self)
        for x,column in enumerate(self.headerList):
            model.setHeaderData(x, QtCore.Qt.Horizontal, column)

        location = self.locationlineEdit.text()
        systemID = self.mydb.getSystemIDbyName(location)

        shipID = self.shipList[ self.shipComboBox.currentIndex() ]

        shipyards = self.mydb.getShipyardWithShip(shipID, systemID)


        for shipyard in shipyards:
            model.insertRow(0)
            
            model.setData(model.index(0, self.headerList.index("System") ), shipyard["System"])
            model.setData(model.index(0, self.headerList.index("Station") ), shipyard["Station"])
            model.setData(model.index(0, self.headerList.index("Distance") ), shipyard["dist"])
            model.setData(model.index(0, self.headerList.index("Age") ), guitools.convertDateimeToAgeStr(shipyard["age"]) )

        self.shipsview.setModel(model)

        if firstrun:
            self.shipsview.sortByColumn( self.headerList.index("Distance"), PySide.QtCore.Qt.SortOrder.AscendingOrder )

        for i in range(0, len(self.headerList) ):
            self.shipsview.resizeColumnToContents(i)
