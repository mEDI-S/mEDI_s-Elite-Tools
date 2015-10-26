# -*- coding: UTF8

'''
Created on 26.10.2015

@author: mEDI
'''
from PySide import QtCore, QtGui
from datetime import datetime, timedelta

import gui.guitools as guitools
from elite.eddbweb import eddbweb


__toolname__ = "Data Status"
__internalName__ = "DaSt"
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
        self.eddbweb = eddbweb()

    def getWideget(self):

        gridLayout = QtGui.QGridLayout()
        gridLayout.setContentsMargins(6, 6, 6, 6)

        gridLayout.setColumnStretch(9, 1)


        self.priceWarning = QtGui.QCheckBox("Price Warning")
        option = self.mydb.getConfig("option_ds_priceWarning")
        if option is False or option == 1:
            self.priceWarning.setChecked(True)
        self.priceWarning.setToolTip("Show price warnings, old or not existing data")
        gridLayout.addWidget(self.priceWarning, 1, 1)

        self.outfittingWarning = QtGui.QCheckBox("Outfitting Warning")
        option = self.mydb.getConfig("option_ds_outfittingWarning")
        if option is False or option == 1:
            self.outfittingWarning.setChecked(True)
        self.outfittingWarning.setToolTip("Show outfitting warnings, old or not existing data")
        gridLayout.addWidget(self.outfittingWarning, 1, 2)


        self.shipyardWarning = QtGui.QCheckBox("Shipyard Warning")
        option = self.mydb.getConfig("option_ds_shipyardWarning")
        if option is False or option == 1:
            self.shipyardWarning.setChecked(True)
        self.shipyardWarning.setToolTip("Show shipyard warnings, old or not existing data")
        gridLayout.addWidget(self.shipyardWarning, 1, 3)

        self.noStationWarning = QtGui.QCheckBox("No Station Warning")
        option = self.mydb.getConfig("option_ds_noStationWarning")
        if option is False or option == 1:
            self.noStationWarning.setChecked(True)
        self.noStationWarning.setToolTip("Show no station warnings, No station in system")
        gridLayout.addWidget(self.noStationWarning, 1, 4)


        label = QtGui.QLabel("Search Range:")
        self.searchRangeSpinBox = QtGui.QSpinBox()
        self.searchRangeSpinBox.setRange(0, 1000)
        self.searchRangeSpinBox.setSuffix("ly")
        self.searchRangeSpinBox.setAlignment(QtCore.Qt.AlignRight)
        if self.mydb.getConfig("option_ds_maxSearchRange"):
            self.searchRangeSpinBox.setValue(self.mydb.getConfig("option_ds_maxSearchRange"))
        else:
            self.searchRangeSpinBox.setValue(10)
            
        gridLayout.addWidget(label, 1, 10)
        gridLayout.addWidget(self.searchRangeSpinBox, 1, 11)



        label = QtGui.QLabel("Info > Age:")
        self.infoAgeSpinBox = QtGui.QSpinBox()
        self.infoAgeSpinBox.setRange(1, 1000)
        self.infoAgeSpinBox.setSuffix("h")
        self.infoAgeSpinBox.setAlignment(QtCore.Qt.AlignRight)
        if self.mydb.getConfig("option_ds_infoAge"):
            self.infoAgeSpinBox.setValue(self.mydb.getConfig("option_ds_infoAge"))
        else:
            self.infoAgeSpinBox.setValue(12)
        gridLayout.addWidget(label, 1, 13)
        gridLayout.addWidget(self.infoAgeSpinBox, 1, 14)




        self.optionsGroupBox = QtGui.QGroupBox("Options")
        self.optionsGroupBox.setLayout(gridLayout)


        locationButton = QtGui.QToolButton()
        locationButton.setIcon(self.guitools.getIconFromsvg("img/location.svg"))
        locationButton.clicked.connect(self.setCurentLocation)
        locationButton.setToolTip("Current Location")



        locationLabel = QtGui.QLabel("Location:")
        self.locationlineEdit = guitools.LineEdit()
        self.locationlineEdit.setText(self.main.location.getLocation())
        self.locationlineEdit.textChanged.connect(self.showStatus)



        self.showOptions = QtGui.QCheckBox("Show Options")
        option = self.mydb.getConfig("option_ds_showOptions")
        if option is False or option == 1:
            self.showOptions.setChecked(True)
        self.showOptions.stateChanged.connect(self.optionsGroupBoxToggleViewAction)


        self.searchbutton = QtGui.QPushButton("Search")
        self.searchbutton.clicked.connect(self.showStatus)



        layout = QtGui.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        layout.addWidget(locationLabel)
        layout.addWidget(locationButton)
        
        layout.addWidget(self.locationlineEdit)
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
        menu.addAction(self.editOnEDDBAct)

        menu.exec_(self.listView.viewport().mapToGlobal(event))

    def optionsGroupBoxToggleViewAction(self):
        if self.showOptions.isChecked():
            self.optionsGroupBox.show()
        else:
            self.optionsGroupBox.hide()


    def createActions(self):
        self.copyAct = QtGui.QAction("Copy", self, triggered=self.guitools.copyToClipboard, shortcut=QtGui.QKeySequence.Copy)

        self.editOnEDDBAct = QtGui.QAction("Edit On EDDB", self, triggered=self.editOnEDDB)



    def editOnEDDB(self):

        indexes = self.listView.selectionModel().selectedIndexes()
        system = self.listView.model().item(indexes[0].row(), self.headerList.index("System")).data(0)
        station = self.listView.model().item(indexes[0].row(), self.headerList.index("Station")).data(0)
        url = None
        
        if not system:
            print("error: station not found on eddb")
            return

        if system and station:
            url = self.eddbweb.getEDDBEditStationUrl(system, station)
        elif system and not station:
            url = self.eddbweb.getEDDBEditSystemUrl(system)

        if url:
            self.main.openUrl(url)

        
    def setCurentLocation(self):
        self.locationlineEdit.setText(self.main.location.getLocation())


    def saveOptions(self):
        self.mydb.setConfig('option_ds_maxSearchRange', self.searchRangeSpinBox.value())
        self.mydb.setConfig('option_ds_showOptions', self.showOptions.isChecked())
        self.mydb.setConfig('option_ds_infoAge', self.infoAgeSpinBox.value())
        self.mydb.setConfig('option_ds_priceWarning', self.priceWarning.isChecked())
        self.mydb.setConfig('option_ds_outfittingWarning', self.outfittingWarning.isChecked())
        self.mydb.setConfig('option_ds_shipyardWarning', self.shipyardWarning.isChecked())
        self.mydb.setConfig('option_ds_noStationWarning', self.noStationWarning.isChecked())

        if self.listView.header().count():
            sectionPosList = []
            for i in range(self.listView.header().count()):
                sectionPosList.append(self.listView.header().logicalIndex(i))
    
            sectionPos = ",".join(map(str, sectionPosList))
            self.mydb.setConfig('option_ds.header.sectionPos', sectionPos)


    def showStatus(self):

        firstrun = False
        if not self.listView.header().count():
            firstrun = True

        self.headerList = ["System", "Station", "StarDist", "Permit", "Distance", "Age", "Info"]

        model = QtGui.QStandardItemModel(0, len(self.headerList), self)
        for x, column in enumerate(self.headerList):
            model.setHeaderData(x, QtCore.Qt.Horizontal, column)

        location = self.locationlineEdit.text()
        systemID = self.mydb.getSystemIDbyName(location)

        if not systemID:
            return

        distance = self.searchRangeSpinBox.value()
            
        infoAge = datetime.utcnow() - timedelta(hours=self.infoAgeSpinBox.value())

        dataList = self.mydb.getSystemDeteilsInDistance(systemID, distance)

        for data in dataList:
            infoText = ""
            showEntry = False
            age = ""

            ''' StarDist AND missing Station'''

            if self.noStationWarning.isChecked() and not data["Station"]:
                showEntry = True
                if infoText:
                    infoText += ", "
                infoText = "No station in system?"
            elif data["Station"] and (not data["StarDist"] or data["StarDist"] < 1):
                showEntry = True
                if infoText:
                    infoText += ", "
                infoText = "No star dist for station"

            ''' Price '''
            if self.priceWarning.isChecked():
                if data["priceAge"] and data["priceAge"] < infoAge:
                    showEntry = True
                    if infoText:
                        infoText += ", "
                    infoText = "Old price data"
                    if age:
                        age += ", "
                    age = guitools.convertDateimeToAgeStr(data["priceAge"])
    
                elif not data["priceAge"] and data["market"]:
                    showEntry = True
                    if infoText:
                        infoText += ", "
                    infoText += "No price data"

            ''' Outfitting '''

            if self.outfittingWarning.isChecked() and data["outfitting"]:
                outfittingAge = self.mydb.getOutfittingDataAge(data["StationID"])
                if outfittingAge and outfittingAge < infoAge:
                    showEntry = True
                    if infoText:
                        infoText += ", "
                    infoText += "Old outfitting data"
    
                    if age:
                        age += ", "
                    age += guitools.convertDateimeToAgeStr(outfittingAge)
    
                elif not outfittingAge:
                    showEntry = True
                    if infoText:
                        infoText += ", "
                    infoText += "No outfitting data"

            ''' Shipyard '''

            if self.shipyardWarning.isChecked() and data["shipyard"]:
                shipyardAge = self.mydb.getShipyardDataAge(data["StationID"])
                if shipyardAge and shipyardAge < infoAge:
                    showEntry = True
                    if infoText:
                        infoText += ", "
                    infoText += "Old shipyard data"
    
                    if age:
                        age += ", "
                    age += guitools.convertDateimeToAgeStr(shipyardAge)
    
                elif not shipyardAge:
                    showEntry = True
                    if infoText:
                        infoText += ", "
                    infoText += "No shipyard data"


            if showEntry:
                model.insertRow(0)
                model.setData(model.index(0, self.headerList.index("System")), data["System"])
    
                model.setData(model.index(0, self.headerList.index("Station")), data["Station"])
    
                model.setData(model.index(0, self.headerList.index("StarDist")), data["StarDist"])
                model.item(0, self.headerList.index("StarDist")).setTextAlignment(QtCore.Qt.AlignRight)
    
    
                model.setData(model.index(0, self.headerList.index("Permit")), "No" if not data["permit"] else "Yes")
                model.item(0, self.headerList.index("Permit")).setTextAlignment(QtCore.Qt.AlignCenter)
    
                model.setData(model.index(0, self.headerList.index("Distance")), data["dist"])
                model.item(0, self.headerList.index("Distance")).setTextAlignment(QtCore.Qt.AlignRight)
    
                model.setData(model.index(0, self.headerList.index("Age")), age)
                model.item(0, self.headerList.index("Age")).setTextAlignment(QtCore.Qt.AlignCenter)

                model.setData(model.index(0, self.headerList.index("Info")), infoText)

        self.listView.setModel(model)

        if firstrun:
            sectionPos = self.mydb.getConfig('option_ds.header.sectionPos')
            if sectionPos:
                sectionPosList = sectionPos.strip().split(',')
                for i, pos in enumerate(sectionPosList):
                    self.listView.header().moveSection(self.listView.header().visualIndex(int(pos)), i)

            self.listView.sortByColumn(self.headerList.index("Distance"), QtCore.Qt.SortOrder.AscendingOrder)

        for i in range(0, len(self.headerList)):
            self.listView.resizeColumnToContents(i)
