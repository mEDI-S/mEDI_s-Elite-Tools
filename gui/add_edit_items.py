'''
Created on 22.10.2015

@author: mEDI
'''

from PySide import QtCore, QtGui
import gui.guitools as guitools
from functools import partial
from datetime import datetime


def initRun(parent):


    def openWindow():
        parent.myWindow = Window(parent)
        parent.myWindow.openWindow()

    
    parent.addOrEditItemAct = QtGui.QAction("Add or Edit Items", parent,
            statusTip="add items manually or edit existing",
            triggered=openWindow)

    parent.editMenu.addAction(parent.addOrEditItemAct)



class Window(QtGui.QDialog):

    def __init__(self, parent):
        super(Window, self).__init__(parent)

        self.parent = parent
        self.mydb = parent.mydb
        self.mainLayout = None
        self.guitools = guitools.guitools(self)

        self.headerList = ["Item", "Sell", "Buy", "Stock", "Blackmarket", "Ignore", "Fake"]


        self.itemList = []
        self.itemIdList = []

        for item in self.mydb.getAllItemNames():
            self.itemIdList.append(item["id"])
            self.itemList.append(item["name"])

    def openWindow(self):


        self.setWindowTitle("Add or Edit Items")
        self.setMinimumSize(700, 300)


        locationButton = QtGui.QToolButton()
        locationButton.setIcon(self.guitools.getIconFromsvg("img/location.svg"))
        locationButton.clicked.connect(self.setCurentLocation)
        locationButton.setToolTip("Current Location")


        systemlabel = QtGui.QLabel("System:")
        self.systemLineEdit = guitools.LineEdit()
        self.systemLineEdit.textChanged.connect(self.triggerSystemChanged)


        stationlabel = QtGui.QLabel("Station:")
        self.stationLineEdit = guitools.LineEdit()
        self.stationLineEdit.textChanged.connect(self.triggerStationChanged)


        locationLayout = QtGui.QHBoxLayout()
        locationLayout.setContentsMargins(6, 12, 6, 6)

        locationLayout.addWidget(systemlabel)
        locationLayout.addWidget(locationButton)
        locationLayout.addWidget(self.systemLineEdit)
        locationLayout.addWidget(stationlabel)
        locationLayout.addWidget(self.stationLineEdit)


        locationGroup = QtGui.QGroupBox("Location")
        locationGroup.setContentsMargins(6, 6, 6, 6)

        locationGroup.setLayout(locationLayout)



        addItemlabel = QtGui.QLabel("Add Item:")
        addItemButton = QtGui.QToolButton()
        addItemButton.setIcon(self.guitools.getIconFromsvg("img/addItem.svg"))
        addItemButton.clicked.connect(self.addItem)


        addItemLayout = QtGui.QHBoxLayout()
        addItemLayout.setContentsMargins(0, 0, 0, 0)

        addItemLayout.addWidget(addItemlabel)
        addItemLayout.addWidget(addItemButton)
        addItemLayout.addStretch(1)


        addItemGroup = QtGui.QGroupBox()
        addItemGroup.setFlat(True)
        addItemGroup.setContentsMargins(0, 0, 0, 0)
        addItemGroup.setStyleSheet("""QGroupBox {border:0;margin:0;padding:0;}""")

        addItemGroup.setLayout(addItemLayout)


        self.tableWidget = QtGui.QTableWidget(0, len(self.headerList))
        self.tableWidget.setHorizontalHeaderLabels(self.headerList)
        self.tableWidget.horizontalHeader().setResizeMode( self.headerList.index("Item"), QtGui.QHeaderView.Stretch)
        self.tableWidget.horizontalHeader().setResizeMode( self.headerList.index("Blackmarket"), QtGui.QHeaderView.ResizeToContents)
        self.tableWidget.horizontalHeader().setResizeMode( self.headerList.index("Ignore"), QtGui.QHeaderView.ResizeToContents)
        self.tableWidget.horizontalHeader().setResizeMode( self.headerList.index("Fake"), QtGui.QHeaderView.ResizeToContents)

        self.tableWidget.setShowGrid(True)


        closeButton = QtGui.QPushButton("Close")
        closeButton.clicked.connect(self.close)
        saveButton = QtGui.QPushButton("Save")
        saveButton.clicked.connect(self.saveItems)

        buttonsLayout = QtGui.QHBoxLayout()
        buttonsLayout.addStretch(1)
        buttonsLayout.addWidget(saveButton)
        buttonsLayout.addWidget(closeButton)


        self.mainLayout = QtGui.QVBoxLayout()
        self.mainLayout.addWidget(locationGroup)
        self.mainLayout.addWidget(addItemGroup)
        
        self.mainLayout.addWidget(self.tableWidget)
        self.mainLayout.addSpacing(12)

        self.mainLayout.addLayout(buttonsLayout)


        self.setLayout(self.mainLayout)

        self.triggerSystemChanged()
        self.triggerStationChanged()
       

        self.setCurentLocation()

        self.show()
        

    def addItem(self):

        row = self.tableWidget.rowCount()
        self.tableWidget.insertRow(row)

        ''' item '''
        itemComboBox = QtGui.QComboBox()

        for item in self.itemList:
            itemComboBox.addItem(item)
        
        self.tableWidget.setCellWidget(row, self.headerList.index("Item"), itemComboBox)
        itemComboBox.currentIndexChanged.connect( partial(self.triggerItemChanged, row) )

        ''' price '''
        priceItem = QtGui.QTableWidgetItem( "0" )
        priceItem.setTextAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight)
        self.tableWidget.setItem(row, self.headerList.index("Sell"), priceItem )

        priceItem = QtGui.QTableWidgetItem( "0" )
        priceItem.setTextAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight)
        self.tableWidget.setItem(row, self.headerList.index("Buy"), priceItem )

        ''' stock '''
        priceItem = QtGui.QTableWidgetItem( "0" )
        priceItem.setTextAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight)
        self.tableWidget.setItem(row, self.headerList.index("Stock"), priceItem )

        ''' '''

        blackmarkedCheckBox = QtGui.QCheckBox()
        self.tableWidget.setCellWidget(row, self.headerList.index("Blackmarket"), guitools.createCenteredWidget(blackmarkedCheckBox) )

        ignoreCheckBox = QtGui.QCheckBox()
        self.tableWidget.setCellWidget(row, self.headerList.index("Ignore"), guitools.createCenteredWidget(ignoreCheckBox) )

        fakeCheckBox = QtGui.QCheckBox()
        self.tableWidget.setCellWidget(row, self.headerList.index("Fake"), guitools.createCenteredWidget(fakeCheckBox) )

        self.triggerItemChanged(row, 0)


    def triggerItemChanged(self, row, boxIndex):

        self.setCurrentItemSettings(row)


    def setCurrentItemSettings(self, row):
        itemID = self.getSelectedItemId(row)
        system = self.systemLineEdit.text()
        systemID = self.mydb.getSystemIDbyName(system)
    
        station = self.stationLineEdit.text()
        stationID = self.mydb.getStationID(systemID, station)
        if not stationID:
            return
        
        price = self.mydb.getFullPriceData( stationID, itemID)
        if price:
            #print(price.keys())
            self.tableWidget.item(row, self.headerList.index("Sell")).setText( str(price['StationBuy']) )
            self.tableWidget.item(row, self.headerList.index("Buy")).setText( str(price['StationSell']) )
            self.tableWidget.item(row, self.headerList.index("Stock")).setText( str(price['Stock']) )
            
            checkBox = guitools.getChildByType(self.tableWidget.cellWidget(row, self.headerList.index("Blackmarket")), QtGui.QCheckBox)
            if checkBox:
                if price['blackmarket']:
                    checkBox.setChecked(True)
                else:
                    checkBox.setChecked(False)

            checkBox = guitools.getChildByType(self.tableWidget.cellWidget(row, self.headerList.index("Ignore")), QtGui.QCheckBox)
            if checkBox:
                if price['ignore']:
                    checkBox.setChecked(True)
                else:
                    checkBox.setChecked(False)

            checkBox = guitools.getChildByType(self.tableWidget.cellWidget(row, self.headerList.index("Fake")), QtGui.QCheckBox)
            if checkBox:
                if price['fake']:
                    checkBox.setChecked(True)
                else:
                    checkBox.setChecked(False)

        else:
            ''' no price? reset all fields'''
            self.tableWidget.item(row, self.headerList.index("Sell")).setText( "0" )
            self.tableWidget.item(row, self.headerList.index("Buy")).setText( "0" )
            self.tableWidget.item(row, self.headerList.index("Stock")).setText( "0" )
            checkBox = guitools.getChildByType(self.tableWidget.cellWidget(row, self.headerList.index("Blackmarket")), QtGui.QCheckBox)
            checkBox.setChecked(False)
            checkBox = guitools.getChildByType(self.tableWidget.cellWidget(row, self.headerList.index("Ignore")), QtGui.QCheckBox)
            checkBox.setChecked(False)
            checkBox = guitools.getChildByType(self.tableWidget.cellWidget(row, self.headerList.index("Fake")), QtGui.QCheckBox)
            checkBox.setChecked(False)


    def saveItems(self):
        self.parent.lockDB()
        failColor = QtGui.QColor(255, 0, 0, 180)
        system = self.systemLineEdit.text()
        systemID = self.mydb.getSystemIDbyName(system)
    
        station = self.stationLineEdit.text()
        stationID = self.mydb.getStationID(systemID, station)
        if not stationID:
            self.parent.unlockDB()
            return
        cur = self.mydb.cursor()
        modifiedDate = datetime.utcnow()
        
        for row in range(0, self.tableWidget.rowCount()):
            itemID = self.getSelectedItemId(row)
            stationBuy = self.tableWidget.item(row, self.headerList.index("Sell")).text()
            stationSell = self.tableWidget.item(row, self.headerList.index("Buy")).text()
            stock = self.tableWidget.item(row, self.headerList.index("Stock")).text()

            if not itemID or not guitools.isInt( stationBuy ) or not guitools.isInt( stationSell ) or not guitools.isInt( stock ):
                #print("fail", stationBuy, stationSell, stock)
                if not guitools.isInt( stationBuy ):
                    self.tableWidget.item(row, self.headerList.index("Sell")).setBackground( failColor )
                if not guitools.isInt( stationSell ):
                    self.tableWidget.item(row, self.headerList.index("Buy")).setBackground( failColor )
                if not guitools.isInt( stock ):
                    self.tableWidget.item(row, self.headerList.index("Stock")).setBackground( failColor )

                self.tableWidget.dataChanged(self.tableWidget.indexFromItem(self.tableWidget.item(row, 0)),
                                             self.tableWidget.indexFromItem(self.tableWidget.item(row, len(self.headerList))))

                msg = "Save Fail"
                msgBox = QtGui.QMessageBox(QtGui.QMessageBox.Information, "Error", msg,
                        QtGui.QMessageBox.NoButton, self)
        
                msgBox.exec_()
                self.parent.unlockDB()
                return

            else:

                cur.execute( "UPDATE price SET StationBuy=?, StationSell=?, Stock=?, modified=?, source=6 where StationID=? AND ItemID=?",
                                            (stationBuy, stationSell, stock, modifiedDate, stationID, itemID))

                if cur.rowcount <= 0:
                    print("no update, insert")
                    cur.execute("insert or IGNORE into price (SystemID, StationID, ItemID, StationBuy, StationSell, Stock, modified, source) values (?,?,?,?,?,?,?,6) ",
                                                            (systemID, stationID, itemID, stationBuy, stationSell, stock, modifiedDate))
            
                cur.execute("select id from price where StationID = ? AND ItemID = ? limit 1", ( stationID, itemID))
                priceID = cur.fetchone()[0]

                ''' blackmarket '''
                blackmarkedCheckBox = guitools.getChildByType(self.tableWidget.cellWidget(row, self.headerList.index("Blackmarket")), QtGui.QCheckBox)
                if blackmarkedCheckBox.isChecked():
                    self.mydb.setBlackmarketPrice(priceID)
                else:
                    self.mydb.removeBlackmarketPrice(priceID)

                ''' ignore '''
                ignoreCheckBox = guitools.getChildByType(self.tableWidget.cellWidget(row, self.headerList.index("Ignore")), QtGui.QCheckBox)
                if ignoreCheckBox.isChecked():
                    self.mydb.setIgnorePriceTemp(priceID)
                else:
                    self.mydb.removeIgnorePrice(priceID)

                ''' fake '''
                fakeCheckBox = guitools.getChildByType(self.tableWidget.cellWidget(row, self.headerList.index("Fake")), QtGui.QCheckBox)
                if fakeCheckBox.isChecked():
                    self.mydb.setFakePrice(priceID)
                else:
                    self.mydb.removeFakePrice(priceID)

                self.mydb.addSystemsInDistanceToDealsInDistancesCacheQueue(systemID, itemID)

        self.mydb.addSystemToDealsInDistancesCacheQueue( [{'id': systemID}] )
                
        self.mydb.con.commit()
        cur.close()
        self.parent.unlockDB()
        
        
    def getSelectedItemId(self, row):
        return self.itemIdList[ self.tableWidget.cellWidget(row, self.headerList.index("Item")).currentIndex() ]

    
    def triggerSystemChanged(self):
        system = self.systemLineEdit.text()
        self.guitools.setStationComplete(system, self.stationLineEdit)


    def triggerStationChanged(self):
        station = self.stationLineEdit.text()
        self.guitools.setSystemComplete(station, self.systemLineEdit)


    def setCurentLocation(self):
        newSystem = self.parent.location.getLocation()
        if self.systemLineEdit.text() != newSystem:
            self.systemLineEdit.setText(newSystem)
            self.stationLineEdit.setText("")
