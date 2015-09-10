# -*- coding: UTF8

'''
Created on 07.09.2015

@author: mEDI
'''
from PySide import QtCore, QtGui
import PySide

import gui.guitools as guitools

__toolname__ = "Power Control Finder"
__statusTip__ = "Find controlled systems by Power"

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
        configval = self.mydb.getConfig( 'option_pcf_location' )
        if configval:
            self.locationlineEdit.setText( configval )
        else:
            self.locationlineEdit.setText( self.main.location.getLocation() )
        self.locationlineEdit.textChanged.connect(self.searchPower)


        ShipLabel = QtGui.QLabel("Power:")
        self.powerComboBox = QtGui.QComboBox()

        powers = self.mydb.getAllPowers()
        self.powerList = []
        for power in powers:
            self.powerComboBox.addItem( power["Name"] )
            self.powerList.append(power["id"])

        if self.mydb.getConfig("option_pcf_power"):
            self.powerComboBox.setCurrentIndex(self.mydb.getConfig("option_pcf_power"))

        self.powerComboBox.currentIndexChanged.connect(self.searchPower)

        self.searchbutton = QtGui.QPushButton("Search")
        self.searchbutton.clicked.connect(self.searchPower)



        layout = QtGui.QHBoxLayout()

        layout.addWidget(locationLabel)
        layout.addWidget(locationButton)
        
        layout.addWidget(self.locationlineEdit)
        layout.addWidget(ShipLabel)
        layout.addWidget(self.powerComboBox)
        
        layout.addWidget(self.searchbutton)

        locationGroupBox = QtGui.QGroupBox()
        locationGroupBox.setFlat(True)
        locationGroupBox.setStyleSheet("""QGroupBox {border:0;margin:0;padding:0;}  margin:0;padding:0;""")
        locationGroupBox.setLayout(layout)


        self.listView = QtGui.QTreeView()


        self.listView.setRootIsDecorated(False)
        self.listView.setAlternatingRowColors(True)
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
        self.searchPower()
        
        return vGroupBox


    def myContextMenuEvent(self, event):
        menu = QtGui.QMenu(self)

        menu.addAction(self.copyAct)

        menu.exec_(self.listView.viewport().mapToGlobal(event))

    def createActions(self):
        self.copyAct = QtGui.QAction("Copy", self, triggered=self.guitools.copyToClipboard, shortcut=QtGui.QKeySequence.Copy)



    def setCurentLocation(self):
        self.locationlineEdit.setText( self.main.location.getLocation() )


    def saveOptions(self):
        # save last options
        self.mydb.setConfig('option_pcf_power', self.powerComboBox.currentIndex())
        self.mydb.setConfig( 'option_pcf_location', self.locationlineEdit.text() )


    def searchPower(self):

        firstrun = False
        if not self.listView.header().count():
            firstrun = True

        self.headerList = ["System", "Distance", "Permit", ""]

        model = QtGui.QStandardItemModel(0, len(self.headerList), self)
        for x,column in enumerate(self.headerList):
            model.setHeaderData(x, QtCore.Qt.Horizontal, column)

        location = self.locationlineEdit.text()
        systemID = self.mydb.getSystemIDbyName(location)

        powerID = self.powerList[ self.powerComboBox.currentIndex() ]

        systems = self.mydb.getSystemsWithPower(powerID, systemID)


        for system in systems:
            model.insertRow(0)
            model.setData(model.index(0, self.headerList.index("System") ), system["System"])

            model.setData(model.index(0, self.headerList.index("Distance") ),  system["dist"])
            model.item(0, self.headerList.index("Distance")).setTextAlignment(QtCore.Qt.AlignRight)

            model.setData(model.index(0, self.headerList.index("Permit") ),  "No" if not system["permit"] else "Yes" )
            model.item(0, self.headerList.index("Permit")).setTextAlignment(QtCore.Qt.AlignCenter)

        self.listView.setModel(model)

        if firstrun:
            self.listView.sortByColumn( self.headerList.index("Distance"), PySide.QtCore.Qt.SortOrder.AscendingOrder )

        for i in range(0, len(self.headerList) ):
            self.listView.resizeColumnToContents(i)
