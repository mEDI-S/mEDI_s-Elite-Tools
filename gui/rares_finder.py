# -*- coding: UTF8

'''
Created on 06.10.2015

@author: mEDI
'''
from PySide import QtCore, QtGui
import PySide

import gui.guitools as guitools
import elite
from sqlite3_functions import calcDistance

__toolname__ = "Rares Finder"
__internalName__ = "RaFi"
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
        self.rares = elite.rares(self.mydb)

    def getWideget(self):

        locationButton = QtGui.QToolButton()
        locationButton.setIcon(self.guitools.getIconFromsvg("img/location.svg"))
        locationButton.clicked.connect(self.setCurentLocation)
        locationButton.setToolTip("Current Location")


        locationLabel = QtGui.QLabel("Location:")
        self.locationlineEdit = guitools.LineEdit()
        self.locationlineEdit.setText(self.main.location.getLocation())
        self.locationlineEdit.textChanged.connect(self.showRares)



        self.searchbutton = QtGui.QPushButton("Search")
        self.searchbutton.clicked.connect(self.showRares)



        layout = QtGui.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        layout.addWidget(locationLabel)
        layout.addWidget(locationButton)
        
        layout.addWidget(self.locationlineEdit)
        
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
        layout.setContentsMargins(6, 6, 6, 6)

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

    def saveItemEdit(self, item):

        model = self.listView.model()
        changesSaved = None
        rareID = model.item(item.row(), self.headerList.index("Id")).data(0)
        print(item.data(0), item.column())


        if self.headerList.index("Price") == item.column():
            print("save new price")
            changesSaved = self.rares.updatePrice(rareID, int(item.data(0)) )

        elif self.headerList.index("Name") == item.column():
            print("save new Name")
            changesSaved = self.rares.updateName(rareID, item.data(0) )

        elif self.headerList.index("Max Ava.") == item.column():
            print("save new Max Ava.")
            changesSaved = self.rares.updateMaxAvail(rareID, int(item.data(0)) )

        elif self.headerList.index("Comment") == item.column():
            print("save new Comment")
            changesSaved = self.rares.updateComment(rareID, item.data(0) )

        if changesSaved:
            self.main.setStatusBar("changes saved")


    def showRares(self):

        firstrun = False
        if not self.listView.header().count():
            firstrun = True

        self.headerList = ["Id", "Name", "System", "Permit", "StarDist", "Station", "Distance", "Price", "Max Ava.", "Comment" ""]

        model = QtGui.QStandardItemModel(0, len(self.headerList), self)
        for x, column in enumerate(self.headerList):
            model.setHeaderData(x, QtCore.Qt.Horizontal, column)

        
        location = self.locationlineEdit.text()
        systemID = self.mydb.getSystemIDbyName(location)
        currentSystem = None
        if systemID:
            currentSystem = self.mydb.getSystemData(systemID)

        rareslist = self.rares.getRaresList()

        for rares in rareslist:
            model.insertRow(0)
            model.setData(model.index(0, self.headerList.index("Id")), rares["id"])
            model.item(0, self.headerList.index("Id")).setTextAlignment(QtCore.Qt.AlignRight)
            model.item(0, self.headerList.index("Id")).setEditable(False)

            model.setData(model.index(0, self.headerList.index("Name")), rares["Name"])
            model.item(0, self.headerList.index("Name")).setEditable(True)

            
            model.setData(model.index(0, self.headerList.index("System")), rares["System"])
            model.item(0, self.headerList.index("System")).setEditable(False)

            model.setData(model.index(0, self.headerList.index("Permit")), "No" if not rares["permit"] else "Yes")
            model.item(0, self.headerList.index("Permit")).setTextAlignment(QtCore.Qt.AlignCenter)
            model.item(0, self.headerList.index("Permit")).setEditable(False)

            model.setData(model.index(0, self.headerList.index("StarDist")), rares["StarDist"])
            model.item(0, self.headerList.index("StarDist")).setTextAlignment(QtCore.Qt.AlignRight)
            model.item(0, self.headerList.index("StarDist")).setEditable(False)

            model.setData(model.index(0, self.headerList.index("Station")), rares["Station"])
            model.item(0, self.headerList.index("Station")).setEditable(False)

            if currentSystem and currentSystem["posX"] and rares["posX"]:
                distance = calcDistance(currentSystem["posX"], currentSystem["posY"], currentSystem["posZ"], rares["posX"], rares["posY"], rares["posZ"])
                model.setData(model.index(0, self.headerList.index("Distance")), distance)
                model.item(0, self.headerList.index("Distance")).setTextAlignment(QtCore.Qt.AlignRight)
                model.item(0, self.headerList.index("Distance")).setEditable(False)

            
            model.setData(model.index(0, self.headerList.index("Price")), rares["Price"])
            model.item(0, self.headerList.index("Price")).setTextAlignment(QtCore.Qt.AlignRight)

            model.setData(model.index(0, self.headerList.index("Max Ava.")), rares["MaxAvail"])
            model.item(0, self.headerList.index("Max Ava.")).setTextAlignment(QtCore.Qt.AlignRight)

            model.setData(model.index(0, self.headerList.index("Comment")), rares["comment"])
            model.item(0, self.headerList.index("Comment")).setEditable(True)

        model.itemChanged.connect(self.saveItemEdit)

        self.listView.setModel(model)

        if firstrun:
            self.listView.sortByColumn(self.headerList.index("Distance"), PySide.QtCore.Qt.SortOrder.AscendingOrder)

        for i in range(0, len(self.headerList)):
            self.listView.resizeColumnToContents(i)
