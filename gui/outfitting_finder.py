# -*- coding: UTF8

'''
Created on 09.10.2015

@author: mEDI
'''
from PySide import QtCore, QtGui
from datetime import datetime, timedelta

import gui.guitools as guitools

import elite

__toolname__ = "Outfitting Finder"
__internalName__ = "OuFi"
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
        self.outfitting = elite.outfitting(self.mydb)

        self.createActions()


    def getWideget(self):

        gridLayout = QtGui.QGridLayout()
        gridLayout.setContentsMargins(6, 6, 6, 6)

        gridLayout.setColumnStretch(3, 1)
        gridLayout.setColumnStretch(6, 1)
        gridLayout.setColumnStretch(9, 1)



        label = QtGui.QLabel("Class:")
        self.classComboBox = QtGui.QComboBox()

        self.classComboBox.addItem("Any")
        for myClass in range(0, 9):
            self.classComboBox.addItem(str(myClass))
        self.classComboBox.currentIndexChanged.connect(self.searchOutfitting)
        gridLayout.addWidget(label, 1, 1)
        gridLayout.addWidget(self.classComboBox, 1, 2)


        label = QtGui.QLabel("Mount:")
        self.mountComboBox = QtGui.QComboBox()
        self.mountComboBox.addItem("Any")
        self.mountList = [None]

        for mount in self.outfitting.getMountList():
            self.mountComboBox.addItem(mount['mount'])
            self.mountList.append(mount['id'])
        self.mountComboBox.currentIndexChanged.connect(self.searchOutfitting)
        gridLayout.addWidget(label, 1, 4)
        gridLayout.addWidget(self.mountComboBox, 1, 5)






        label = QtGui.QLabel("Allegiances:")
        self.allegiancesComboBox = QtGui.QComboBox()

        allegiances = self.mydb.getAllegiances()
        self.allegiancesList = []
        self.allegiancesComboBox.addItem("Any")
        self.allegiancesList.append(None)

        for allegiance in allegiances:
            self.allegiancesComboBox.addItem(allegiance["Name"])
            self.allegiancesList.append(allegiance["id"])
        if self.mydb.getConfig("option_of_allegiances"):
            self.allegiancesComboBox.setCurrentIndex(self.mydb.getConfig("option_of_allegiances"))
        self.allegiancesComboBox.currentIndexChanged.connect(self.searchOutfitting)
        gridLayout.addWidget(label, 1, 7)
        gridLayout.addWidget(self.allegiancesComboBox, 1, 8)




        label = QtGui.QLabel("Search Range:")
        self.searchRangeSpinBox = QtGui.QSpinBox()
        self.searchRangeSpinBox.setRange(0, 1000)
        self.searchRangeSpinBox.setSuffix("ly")
        self.searchRangeSpinBox.setAlignment(QtCore.Qt.AlignRight)
        if self.mydb.getConfig("option_of_maxSearchRange"):
            self.searchRangeSpinBox.setValue(self.mydb.getConfig("option_of_maxSearchRange"))
        else:
            self.searchRangeSpinBox.setValue(150)
            
        gridLayout.addWidget(label, 1, 10)
        gridLayout.addWidget(self.searchRangeSpinBox, 1, 11)



        label = QtGui.QLabel("Max Data Age:")
        self.maxAgeSpinBox = QtGui.QSpinBox()
        self.maxAgeSpinBox.setRange(1, 1000)
        self.maxAgeSpinBox.setSuffix("Day")
        self.maxAgeSpinBox.setAlignment(QtCore.Qt.AlignRight)
        if self.mydb.getConfig("option_of_maxAge"):
            self.maxAgeSpinBox.setValue(self.mydb.getConfig("option_of_maxAge"))
        else:
            self.maxAgeSpinBox.setValue(14)
        gridLayout.addWidget(label, 1, 13)
        gridLayout.addWidget(self.maxAgeSpinBox, 1, 14)


        label = QtGui.QLabel("Rating:")
        self.ratingComboBox = QtGui.QComboBox()

        self.ratingComboBox.addItem("Any")
        for rating in self.outfitting.getRatingList():
            self.ratingComboBox.addItem( rating['Rating'] )
        self.ratingComboBox.currentIndexChanged.connect(self.searchOutfitting)
        gridLayout.addWidget(label, 2, 1)
        gridLayout.addWidget(self.ratingComboBox, 2, 2)



        label = QtGui.QLabel("Ship:")
        self.shipComboBox = QtGui.QComboBox()
        self.shipComboBox.addItem("Any")
        self.shipList = [None]

        for ship in self.mydb.getAllShipnames():
            self.shipComboBox.addItem(ship["Name"])
            self.shipList.append(ship["id"])
        self.shipComboBox.currentIndexChanged.connect(self.searchOutfitting)
        gridLayout.addWidget(label, 2, 4)
        gridLayout.addWidget(self.shipComboBox, 2, 5)




        label = QtGui.QLabel("Governments:")
        self.governmentsComboBox = QtGui.QComboBox()

        governments = self.mydb.getGovernments()
        self.governmentsList = []
        self.governmentsComboBox.addItem("Any")
        self.governmentsList.append(None)

        for government in governments:
            self.governmentsComboBox.addItem(government["Name"])
            self.governmentsList.append(government["id"])
        if self.mydb.getConfig("option_of_governments"):
            self.governmentsComboBox.setCurrentIndex(self.mydb.getConfig("option_of_governments"))
        self.governmentsComboBox.currentIndexChanged.connect(self.searchOutfitting)
        gridLayout.addWidget(label, 2, 7)
        gridLayout.addWidget(self.governmentsComboBox, 2, 8)


        label = QtGui.QLabel("Max Star Dist:")
        self.maxStartDistSpinBox = QtGui.QSpinBox()
        self.maxStartDistSpinBox.setRange(10, 7000000)
        self.maxStartDistSpinBox.setSuffix("ls")
        self.maxStartDistSpinBox.setSingleStep(10)
        self.maxStartDistSpinBox.setAlignment(QtCore.Qt.AlignRight)
        maxStarDist = self.mydb.getConfig('option_of_maxStarDist')
        if maxStarDist:
            self.maxStartDistSpinBox.setValue(maxStarDist)
        else:
            self.maxStartDistSpinBox.setValue(1500)
        gridLayout.addWidget(label, 2, 10)
        gridLayout.addWidget(self.maxStartDistSpinBox, 2, 11)



        self.optionsGroupBox = QtGui.QGroupBox("Options")
        self.optionsGroupBox.setLayout(gridLayout)






        locationButton = QtGui.QToolButton()
        locationButton.setIcon(self.guitools.getIconFromsvg("img/location.svg"))
        locationButton.clicked.connect(self.setCurentLocation)
        locationButton.setToolTip("Current Location")



        locationLabel = QtGui.QLabel("Location:")
        self.locationlineEdit = guitools.LineEdit()
        self.locationlineEdit.setText(self.main.location.getLocation())
        self.locationlineEdit.textChanged.connect(self.searchOutfitting)


        modulLabel = QtGui.QLabel("Modul:")
        self.modulComboBox = QtGui.QComboBox()

        module = self.outfitting.getOutfittingNameList()
        self.modulList = []
        for modul in module:
            self.modulComboBox.addItem(modul["modulname"])
            self.modulList.append(modul["id"])
        self.modulComboBox.currentIndexChanged.connect(self.searchOutfitting)

        self.showOptions = QtGui.QCheckBox("Show Options")
        if self.mydb.getConfig("option_of_showOptions") != 0:
            self.showOptions.setChecked(True)
        self.showOptions.stateChanged.connect(self.optionsGroupBoxToggleViewAction)


        self.searchbutton = QtGui.QPushButton("Search")
        self.searchbutton.clicked.connect(self.searchOutfitting)



        layout = QtGui.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        layout.addWidget(locationLabel)
        layout.addWidget(locationButton)
        
        layout.addWidget(self.locationlineEdit)
        layout.addWidget(modulLabel)
        layout.addWidget(self.modulComboBox)
        layout.addWidget(self.showOptions)
        
        layout.addWidget(self.searchbutton)

        locationGroupBox = QtGui.QGroupBox()
        locationGroupBox.setFlat(True)
        locationGroupBox.setStyleSheet("""QGroupBox {border:0;margin:0;padding:0;}  margin:0;padding:0;""")

        locationGroupBox.setLayout(layout)


        self.listView = QtGui.QTreeView()


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
        self.locationlineEdit.setText(self.main.location.getLocation())


    def saveOptions(self):
        self.mydb.setConfig('option_of_maxSearchRange', self.searchRangeSpinBox.value())
        self.mydb.setConfig('option_of_maxAge', self.maxAgeSpinBox.value())
        self.mydb.setConfig('option_of_maxStarDist', self.maxStartDistSpinBox.value())
        self.mydb.setConfig('option_of_showOptions', self.showOptions.isChecked())
        self.mydb.setConfig('option_of_allegiances', self.allegiancesComboBox.currentIndex())
        self.mydb.setConfig('option_of_governments', self.governmentsComboBox.currentIndex())

        sectionPosList = []
        for i in range(self.listView.header().count()):
            sectionPosList.append(self.listView.header().logicalIndex(i))

        sectionPos = ",".join(map(str, sectionPosList))
        self.mydb.setConfig('option_of.header.sectionPos', sectionPos)


    def searchOutfitting(self):

        firstrun = False
        if not self.listView.header().count():
            firstrun = True

        self.headerList = ["System", "Permit", "StarDist", "Station", "Distance", "Name", "Class", "Rating", "Mount", "Category", "Guidance", "Ship", "Age", ""]

        model = QtGui.QStandardItemModel(0, len(self.headerList), self)
        for x, column in enumerate(self.headerList):
            model.setHeaderData(x, QtCore.Qt.Horizontal, column)

        location = self.locationlineEdit.text()
        systemID = self.mydb.getSystemIDbyName(location)

        nameID = self.modulList[ self.modulComboBox.currentIndex() ]

        distance = self.searchRangeSpinBox.value()
            
        maxAgeDate = datetime.utcnow() - timedelta(days=self.maxAgeSpinBox.value())

        classID = int(self.classComboBox.currentIndex()) - 1

        rating = None
        if self.ratingComboBox.currentIndex() > 0:
            rating = self.ratingComboBox.currentText()

        mountID = self.mountList[ self.mountComboBox.currentIndex() ]

        shipID = self.shipList[ self.shipComboBox.currentIndex() ]

        outfittings = self.outfitting.getOutfitting(nameID, distance, self.maxStartDistSpinBox.value(), maxAgeDate, systemID, classID, rating, mountID, shipID, self.allegiancesComboBox.currentIndex(), self.governmentsComboBox.currentIndex())

        for outfitting in outfittings:

            model.insertRow(0)
            model.setData(model.index(0, self.headerList.index("System")), outfitting["System"])

            model.setData(model.index(0, self.headerList.index("Permit")), "No" if not outfitting["permit"] else "Yes")
            model.item(0, self.headerList.index("Permit")).setTextAlignment(QtCore.Qt.AlignCenter)

            model.setData(model.index(0, self.headerList.index("StarDist")), outfitting["StarDist"])
            model.item(0, self.headerList.index("StarDist")).setTextAlignment(QtCore.Qt.AlignRight)

            model.setData(model.index(0, self.headerList.index("Station")), outfitting["Station"])
            model.setData(model.index(0, self.headerList.index("Distance")), outfitting["dist"])
            model.item(0, self.headerList.index("Distance")).setTextAlignment(QtCore.Qt.AlignRight)

            model.setData(model.index(0, self.headerList.index("Name")), outfitting["modulname"])

            model.setData(model.index(0, self.headerList.index("Class")), outfitting["Class"])
            model.item(0, self.headerList.index("Class")).setTextAlignment(QtCore.Qt.AlignCenter)

            model.setData(model.index(0, self.headerList.index("Rating")), outfitting["Rating"])
            model.item(0, self.headerList.index("Rating")).setTextAlignment(QtCore.Qt.AlignCenter)

            model.setData(model.index(0, self.headerList.index("Mount")), outfitting["mount"])

            model.setData(model.index(0, self.headerList.index("Category")), outfitting["category"])

            if outfitting["guidance"]:
                model.setData(model.index(0, self.headerList.index("Guidance")), outfitting["guidance"])

            if outfitting["ShipID"]:
                model.setData(model.index(0, self.headerList.index("Ship")), outfitting["Name"])

            model.setData(model.index(0, self.headerList.index("Age")), guitools.convertDateimeToAgeStr(outfitting["modifydate"]))
            model.item(0, self.headerList.index("Age")).setTextAlignment(QtCore.Qt.AlignCenter)

        self.listView.setModel(model)

        if firstrun:
            sectionPos = self.mydb.getConfig('option_of.header.sectionPos')
            if sectionPos:
                sectionPosList = sectionPos.strip().split(',')
                for i, pos in enumerate(sectionPosList):
                    self.listView.header().moveSection(self.listView.header().visualIndex(int(pos)), i)

            self.listView.sortByColumn(self.headerList.index("Distance"), QtCore.Qt.SortOrder.AscendingOrder)

        for i in range(0, len(self.headerList)):
            self.listView.resizeColumnToContents(i)
