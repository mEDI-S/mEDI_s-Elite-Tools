# -*- coding: UTF8

'''
Created on 30.08.2015

@author: mEDI
'''
from PySide import QtCore, QtGui
import PySide

import gui.guitools as guitools

__toolname__ = "Shipyard Finder"
__internalName__ = "ShFi"
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
        self.createActions()
        
    def getWideget(self):



        locationButton = QtGui.QToolButton()
        locationButton.setIcon(self.guitools.getIconFromsvg("img/location.svg"))
        locationButton.clicked.connect(self.setCurentLocation)
        locationButton.setToolTip("Current Location")



        locationLabel = QtGui.QLabel("Location:")
        self.locationlineEdit = guitools.LineEdit()
        self.locationlineEdit.setText(self.main.location.getLocation())
        self.locationlineEdit.textChanged.connect(self.searchShip)


        ShipLabel = QtGui.QLabel("Ship:")
        self.shipComboBox = QtGui.QComboBox()

        ships = self.mydb.getAllShipnames()
        self.shipList = []
        for ship in ships:
            self.shipComboBox.addItem(ship["Name"])
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
        locationGroupBox.setFlat(True)
        locationGroupBox.setStyleSheet("""QGroupBox {border:0;margin:0;padding:0;}  margin:0;padding:0;""")

        # locationGroupBox.setFlat(True)
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

        layout.addWidget(locationGroupBox)
        layout.addWidget(self.listView)



        vGroupBox.setLayout(layout)

        self.guitools.setSystemComplete("", self.locationlineEdit)
        
        return vGroupBox


    def myContextMenuEvent(self, event):
        menu = QtGui.QMenu(self)

        menu.addAction(self.copyAct)

        menu.exec_(self.listView.viewport().mapToGlobal(event))

    def createActions(self):
        self.copyAct = QtGui.QAction("Copy", self, triggered=self.guitools.copyToClipboard, shortcut=QtGui.QKeySequence.Copy)



    def setCurentLocation(self):
        self.locationlineEdit.setText(self.main.location.getLocation())


    def searchShip(self):

        firstrun = False
        if not self.listView.header().count():
            firstrun = True

        self.headerList = ["System", "Permit", "StarDist", "Station", "Distance", "Age", ""]

        model = QtGui.QStandardItemModel(0, len(self.headerList), self)
        for x, column in enumerate(self.headerList):
            model.setHeaderData(x, QtCore.Qt.Horizontal, column)

        location = self.locationlineEdit.text()
        systemID = self.mydb.getSystemIDbyName(location)

        shipID = self.shipList[ self.shipComboBox.currentIndex() ]

        shipyards = self.mydb.getShipyardWithShip(shipID, systemID)


        for shipyard in shipyards:
            model.insertRow(0)
            model.setData(model.index(0, self.headerList.index("System")), shipyard["System"])

            model.setData(model.index(0, self.headerList.index("Permit")), "No" if not shipyard["permit"] else "Yes")
            model.item(0, self.headerList.index("Permit")).setTextAlignment(QtCore.Qt.AlignCenter)

            model.setData(model.index(0, self.headerList.index("StarDist")), shipyard["StarDist"])
            model.item(0, self.headerList.index("StarDist")).setTextAlignment(QtCore.Qt.AlignRight)

            model.setData(model.index(0, self.headerList.index("Station")), shipyard["Station"])
            model.setData(model.index(0, self.headerList.index("Distance")), shipyard["dist"])
            model.item(0, self.headerList.index("Distance")).setTextAlignment(QtCore.Qt.AlignRight)

            model.setData(model.index(0, self.headerList.index("Age")), guitools.convertDateimeToAgeStr(shipyard["age"]))
            model.item(0, self.headerList.index("Age")).setTextAlignment(QtCore.Qt.AlignCenter)

        self.listView.setModel(model)

        if firstrun:
            self.listView.sortByColumn(self.headerList.index("Distance"), PySide.QtCore.Qt.SortOrder.AscendingOrder)

        for i in range(0, len(self.headerList)):
            self.listView.resizeColumnToContents(i)
