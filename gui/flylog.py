# -*- coding: UTF8

'''
Created on 11.09.2015

@author: mEDI
'''
from PySide import QtCore, QtGui
from datetime import datetime

import gui.guitools as guitools
from sqlite3_functions import calcDistance
import elite.loader.edsc
import elite.loader.edsm
import random


__toolname__ = "Fly Log"
__internalName__ = "FlLo"
__statusTip__ = "Show ur Fly Log"
__defaultUpdateTime__ = 1000 * 15


class flyLogger(object):

    lastPos = None

    def __init__(self, main):
        self.main = main
        self.mydb = main.mydb
        self.edsc = elite.loader.edsc.edsc()
        self.edsm = elite.loader.edsm.edsm()

        self.lastPos = self.getLastPos()
        print("lastpos", self.lastPos)
        
    def getLastPos(self):
        cur = self.mydb.cursor()
        cur.execute("""select System, optionalSystemName from flylog
                    left join systems on flylog.SystemID=systems.id
                    order by flylog.id DESC limit 1""")

        result = cur.fetchone()
        cur.close()
        if result:
            if result[0]:
                return result[0]
            else:
                return result[1]

    def getLastPosWithKnowCords(self):
        cur = self.mydb.cursor()
        cur.execute("""select * from flylog
                    left join systems on flylog.SystemID=systems.id
                    where flylog.SystemID is not Null
                    order by flylog.id DESC limit 1""")

        result = cur.fetchone()
        cur.close()
        if result:
            return result

    def getLastLog(self):
        cur = self.mydb.cursor()
        
        cur.execute("""select flylog.id, System, optionalSystemName, DateTime, systems.posX, systems.posY, systems.posZ, Comment FROM flylog
                        left join systems on flylog.SystemID=systems.id
                        order by flylog.id ASC
                        limit 1000
                     """)

        result = cur.fetchall()

        cur.close()
        return result


    def getLogByLogID(self, logID):
        cur = self.mydb.cursor()
        
        cur.execute("""select * FROM flylog
                        left join systems on flylog.SystemID=systems.id
                        where flylog.id=?
                     """, (logID, ))

        result = cur.fetchone()

        cur.close()
        return result


    def insertSystemCoords(self, system, coords):
        if coords and system:
            self.main.lockDB()
            
            cur = self.mydb.cursor()
            print("update coord data from  %s" % system)

            cur.execute("insert or IGNORE into systems (System, posX, posY, posZ) values (?,?,?,?) ",
                                (system, float(coords['x']), float(coords['y']), float(coords['z'])))

            systemID = self.mydb.getSystemIDbyName(system)
            if systemID:
                cur.execute("UPDATE flylog SET  SystemID=?, optionalSystemName='' where optionalSystemName=? and SystemID is Null", (systemID, system))

            self.mydb.con.commit()
            cur.close()
            self.main.unlockDB()
#            self.reloadLogViews()
                
    def logCurrentPos(self):
        location = self.main.location.getLocation()

        if not location:
            print("no location avalibel!")
            return
        
        if self.lastPos != location:
            self.main.lockDB()
            cur = self.mydb.cursor()
            systemID = self.mydb.getSystemIDbyName(location)

            if not systemID:

                edsmCoords = None
                if self.mydb.getConfig("plugin_edsm") is not 0:
                    edsmCoords = self.edsm.getSystemCoords(location)
                    
                if edsmCoords:
                    print("update coord data from edsm for %s" % location)
                    cur.execute("insert or IGNORE into systems (System, posX, posY, posZ) values (?,?,?,?) ",
                                        (location, float(edsmCoords['x']), float(edsmCoords['y']), float(edsmCoords['z'])))
                    
                    systemID = self.mydb.getSystemIDbyName(location)
                elif self.mydb.getConfig("plugin_edsc") is not 0:
                    ''' ask edsc '''
                    edscSystem = self.edsc.getSystemCoords(location)
                    if edscSystem:
    
                        print("update coord data from edsc for %s" % location)
                        cur.execute("insert or IGNORE into systems (System, posX, posY, posZ) values (?,?,?,?) ",
                                            (location, float(edscSystem['coord'][0]), float(edscSystem['coord'][1]), float(edscSystem['coord'][2])))
    
                        systemID = self.mydb.getSystemIDbyName(location)

            self.lastPos = location
            print(location)
            # return
            if systemID:
                cur.execute("insert or replace into flylog (SystemID, DateTime) values (?,?)", (systemID, datetime.utcnow()))
            else:
                cur.execute("insert or replace into flylog (optionalSystemName, DateTime) values (?,?)", (location, datetime.utcnow()))
                print("unknow system %s" % location)

            self.mydb.con.commit()
            self.main.unlockDB()
            cur.close()
            self.reloadLogViews()

    def reloadLogViews(self):
            ''' update open logs '''
            if self.main.flyLogWidget:
                for flylog in range(1, len(self.main.flyLogWidget)):
                    self.main.flyLogWidget[flylog].showLog()


    def updateComment(self, logID, comment):
        if not logID:
            return

        cur = self.mydb.cursor()
        cur.execute("UPDATE flylog SET  Comment=? where id=?", (comment, logID) )
        cur.close()
        return True


def initRun(self):

    self.flyLogger = flyLogger(self)
    
    self.flyLogTimer = QtCore.QTimer()
    self.flyLogTimer.start(__defaultUpdateTime__)
    self.flyLogTimer.timeout.connect(self.flyLogger.logCurrentPos)


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



        locationButton = QtGui.QToolButton()
        locationButton.setIcon(self.guitools.getIconFromsvg("img/location.svg"))
        locationButton.clicked.connect(self.setCurentLocation)
        locationButton.setToolTip("Current Location")



        locationFilterLabel = QtGui.QLabel("Location Filter:")
        self.locationFilterlineEdit = QtGui.QLineEdit()
        self.locationFilterlineEdit.textChanged.connect(self.filterRegExpChanged)




        self.searchbutton = QtGui.QPushButton("Search")
        self.searchbutton.clicked.connect(self.showLog)



        layout = QtGui.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        layout.addWidget(locationFilterLabel)
        layout.addWidget(locationButton)
        
        layout.addWidget(self.locationFilterlineEdit)
        
        layout.addWidget(self.searchbutton)

        locationGroupBox = QtGui.QGroupBox()
        locationGroupBox.setFlat(True)
        locationGroupBox.setStyleSheet("""QGroupBox {border:0;margin:0;padding:0;}  margin:0;padding:0;""")
        locationGroupBox.setLayout(layout)

        self.proxyModel = QtGui.QSortFilterProxyModel()
        self.proxyModel.setDynamicSortFilter(True)


        self.listView = QtGui.QTreeView()


        self.listView.setRootIsDecorated(False)
        self.listView.setAlternatingRowColors(True)
        self.listView.setSortingEnabled(True)
        self.listView.setModel(self.proxyModel)

        self.listView.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.listView.setSelectionBehavior(QtGui.QAbstractItemView.SelectItems)

        self.listView.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.listView.customContextMenuRequested.connect(self.myContextMenuEvent)

        QtCore.QObject.connect(self.listView.selectionModel(), QtCore.SIGNAL('selectionChanged(QItemSelection, QItemSelection)'), self.calcSelected)

        distanceLabel = QtGui.QLabel("Distance:")
        self.distanceLineEdit = QtGui.QLineEdit()
        self.distanceLineEdit.setMaximumWidth(100)

        timeLabel = QtGui.QLabel("Time:")
        self.timeLineEdit = QtGui.QLineEdit()
        self.timeLineEdit.setMaximumWidth(100)

        spacer = QtGui.QSpacerItem(1, 1, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)

        layout = QtGui.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(distanceLabel)
        layout.addWidget(self.distanceLineEdit)
        layout.addWidget(timeLabel)
        layout.addWidget(self.timeLineEdit)

        layout.addItem(spacer)

        infosGroupBox = QtGui.QGroupBox()
        infosGroupBox.setFlat(True)
        # infosGroupBox.setStyleSheet("""border:0; margin:0;padding:0;""")
        infosGroupBox.setLayout(layout)


        vGroupBox = QtGui.QGroupBox()
        vGroupBox.setFlat(True)
        vGroupBox.setStyleSheet("""QGroupBox {border:0;margin:0;padding:0;}  margin:0;padding:0;""")

        layout = QtGui.QVBoxLayout()
        layout.setContentsMargins(6, 6, 6, 6)
        layout.addWidget(locationGroupBox)
        layout.addWidget(self.listView)
        layout.addWidget(infosGroupBox)



        vGroupBox.setLayout(layout)

        self.showLog()
        
        return vGroupBox

    def calcSelected(self):
        indexes = self.listView.selectionModel().selectedIndexes()
        ''' calc Distances '''
        if indexes[0].column() == self.headerList.index("Distance"):
            distSum = 0
            for index in indexes:
                item = self.proxyModel.sourceModel().item(index.row(), self.headerList.index("Distance"))
                if item:
                    dist = item.data(0)
                    if dist:
                        distSum += dist
            self.distanceLineEdit.setText(str(round(distSum, 2)))
        ''' calc Time '''
        if indexes[0].column() == self.headerList.index("Date"):
            minDate = None
            maxDate = None
            for index in indexes:
                item = self.proxyModel.sourceModel().item(index.row(), self.headerList.index("Date"))
                if item:
                    date = item.data(0)
                    if not minDate and not maxDate:
                        minDate = date
                        maxDate = date
                    elif minDate > date:
                        minDate = date
                    elif maxDate < date:
                        maxDate = date
            timeDiff = int(maxDate.toMSecsSinceEpoch() / 1000 - minDate.toMSecsSinceEpoch() / 1000)

            minutes, sekunds = divmod(timeDiff, 60)
            h, minutes = divmod(minutes, 60)
            time = "%02d:%02d:%02d" % (h, minutes, sekunds)
            self.timeLineEdit.setText(time)

    def myContextMenuEvent(self, event):
        menu = QtGui.QMenu(self)

        menu.addAction(self.copyAct)
        menu.addAction(self.saveBookmarkAct)
        
        indexes = self.listView.selectionModel().selectedIndexes()
        item = self.proxyModel.mapToSource( indexes[0] )
        system = self.proxyModel.sourceModel().item(item.row(), self.headerList.index("System")).data(0)


        if system and system == self.main.location.getLocation():
            ''' allow submit edsc only in same system '''
            systemID = self.mydb.getSystemIDbyName(system)
            if not systemID:
                self.selectedSystem = system
                menu.addAction(self.openSubmitDistancesWizardAct)

        menu.exec_(self.listView.viewport().mapToGlobal(event))

    def createActions(self):
        self.copyAct = QtGui.QAction("Copy", self, triggered=self.guitools.copyToClipboard, shortcut=QtGui.QKeySequence.Copy)

        self.openSubmitDistancesWizardAct = QtGui.QAction("SubmitDistances Wizard", self,
                statusTip="SubmitDistances Wizard", triggered=self.openSubmitDistancesWizard)

        self.saveBookmarkAct = QtGui.QAction("Bookmark System", self,
                statusTip="save a bookmark", triggered=self.saveBookmark)


    def setCurentLocation(self):
        self.locationFilterlineEdit.setText(self.main.location.getLocation())

    def filterRegExpChanged(self):

        regExp = QtCore.QRegExp(self.locationFilterlineEdit.text(), QtCore.Qt.CaseInsensitive, QtCore.QRegExp.RegExp)
        self.proxyModel.setFilterRegExp(regExp)


    def saveOptions(self):
        # save last options
        return
        self.mydb.setConfig('option_pcf_power', self.powerComboBox.currentIndex())
        self.mydb.setConfig('option_pcf_location', self.locationlineEdit.text())


    def openSubmitDistancesWizard(self):
        '''
        https://srinikom.github.io/pyside-docs/PySide/QtGui/QWizard.html#PySide.QtGui.PySide.QtGui.QWizard.WizardButton
        '''
        print("addSystemEDSCWizard")

        def createIntroPage():
            page = QtGui.QWizardPage()
            page.setTitle("Introduction")
        
            label = QtGui.QLabel("This wizard will help you Submit Distances "
                    "to http://edstarcoordinator.com and to http://www.edsm.net.")
            label.setWordWrap(True)

            gridLayout = QtGui.QGridLayout()
            
            nameLabel = QtGui.QLabel("Commander Name:")
            self.commanderNameLineEdit = QtGui.QLineEdit()
            if self.mydb.getConfig('option_commanderName'):
                self.commanderNameLineEdit.setText(self.mydb.getConfig('option_commanderName'))

            gridLayout.addWidget(nameLabel, 1, 0)
            gridLayout.addWidget(self.commanderNameLineEdit, 1, 1)

            nameLabel = QtGui.QLabel("New System:")
            self.systemNameLineEdit = QtGui.QLineEdit()
            self.systemNameLineEdit.setText(self.selectedSystem)
            gridLayout.addWidget(nameLabel, 2, 0)
            gridLayout.addWidget(self.systemNameLineEdit, 2, 1)

            GroupBox = QtGui.QGroupBox("")
            GroupBox.setLayout(gridLayout)


            layout = QtGui.QVBoxLayout()
            layout.addWidget(label)
            layout.addWidget(GroupBox)

            page.setLayout(layout)
        
            return page
        

        def createReferencPage():

            beforeSystem = self.main.flyLogger.getLastPosWithKnowCords()
            refSystems = self.mydb.getSystemsInDistance(beforeSystem['SystemID'], 50)
            excludeList = ['Sector', 'ICZ ']
            refsyslist = []
            # refsyslist.append(beforeSystem['System'])
            for i in range(1, 5):
                
                idx = random.randint(0, len(refSystems) - 1)

                while refSystems[idx]['System'] in refsyslist or [s for s in excludeList if refSystems[idx]['System'].find(s) > -1 ]:
                    idx = random.randint(0, len(refSystems) - 1)

                refsyslist.append(refSystems[idx]['System'])

            page = QtGui.QWizardPage()
            page.setTitle("Referenc Systems")
        
            label = QtGui.QLabel("Now enter the exact distance to ur referenc systems. (with 2 decimal places)\n"
                                 "It's important to use the Galaxy Map to optain distances, as the distances in the Nav Panel are not always correct for some reason. "
                                 "Copy ref. system, search it in ur navigation and enter the distance to u.")
            label.setWordWrap(True)

            gridLayout = QtGui.QGridLayout()


            self.refSyslist = []

            for i, system in enumerate(refsyslist):
            
                nameLabel = QtGui.QLabel("Ref. System %d:" % (i + 1))
                LineEdit = QtGui.QLineEdit()
                LineEdit.setText(system)
    
                DistSpinBox = QtGui.QDoubleSpinBox()
                DistSpinBox.setRange(0, 1000)
                DistSpinBox.setSuffix("ly")
                DistSpinBox.setSingleStep(1)
                DistSpinBox.setAlignment(QtCore.Qt.AlignRight)

                statusLabel = QtGui.QLabel("N/A")
                statusLabel.setAlignment(QtCore.Qt.AlignCenter)
               
                gridLayout.addWidget(nameLabel, i + 1, 0)
                gridLayout.addWidget(LineEdit, i + 1, 1, 1, 2)
                gridLayout.addWidget(DistSpinBox, i + 1, 3)
                gridLayout.addWidget(statusLabel, i + 1, 4)

                
                self.refSyslist.append([LineEdit, DistSpinBox, statusLabel])



            GroupBox = QtGui.QGroupBox("Referenc Systems")
            GroupBox.setLayout(gridLayout)


            layout = QtGui.QVBoxLayout()
            layout.addWidget(label)
            layout.addWidget(GroupBox)

            page.setLayout(layout)
        
            return page


        def createSubmitPage():
            page = QtGui.QWizardPage()
            page.setTitle("Submit")
        
            label = QtGui.QLabel("Press the Send button to submit the data "
                    "to http://edstarcoordinator.com and to http://www.edsm.net.")
            label.setWordWrap(True)

            submitEDSMButton = QtGui.QPushButton("Send to EDSM")
            submitEDSMButton.clicked.connect(self.submitDistancesEDSM)

            submitEDSCButton = QtGui.QPushButton("Send to EDSC")
            submitEDSCButton.clicked.connect(self.submitDistancesEDSC)
           
            layout = QtGui.QVBoxLayout()
            layout.addWidget(label)

            if self.mydb.getConfig("plugin_edsm") is not 0:
                layout.addWidget(submitEDSMButton)

            if self.mydb.getConfig("plugin_edsc") is not 0:
                layout.addWidget(submitEDSCButton)

            page.setLayout(layout)
        
            return page


        
        self.submitDistancesWizard = QtGui.QWizard()
        self.submitDistancesWizard.addPage(createIntroPage())
        self.submitDistancesWizard.addPage(createReferencPage())
        self.submitDistancesWizard.addPage(createSubmitPage())
        
        self.submitDistancesWizard.setWindowTitle("EDSC Submit Distances")
        self.submitDistancesWizard.setWindowFlags(QtCore.Qt.Drawer | QtCore.Qt.WindowStaysOnTopHint)
#        submitDistancesWizard.setOptions(QtGui.QWizard.NoBackButtonOnStartPage)
        self.submitDistancesWizard.show()

        res = self.submitDistancesWizard.exec_()

        if res == QtGui.QWizard.NextButton or res == QtGui.QWizard.FinishButton:
            self.mydb.setConfig('option_commanderName', self.commanderNameLineEdit.text())
            self.showLog()

    def removeOnTopFromWizard(self):
        self.submitDistancesWizard.setWindowFlags( QtCore.Qt.Drawer )
        pos = self.submitDistancesWizard.pos()

        if pos.x() < 0:
            pos.setX(0)

        if pos.y() < 0:
            pos.setY(0)

        self.submitDistancesWizard.move(pos)
        self.submitDistancesWizard.show()
        self.submitDistancesWizard.activateWindow()


    def submitDistancesEDSM(self):
        print("submitDistancesEDSM")

        self.removeOnTopFromWizard()

        refList = []
        fail = ""
        if self.systemNameLineEdit.text():
            for system in self.refSyslist:
                if system[1].value() <= 1.0:
                    fail = "distance from <= 1 is not allowed"
                    break
                elif system[0].text() == "":
                    fail = "System name emty"
                    break
    
                refList.append({'name': system[0].text(), 'dist': system[1].value() })
                print(system[0].text(), system[1].value())
        else:
            fail = "No Target System Name"

        if fail:
            msgBox = QtGui.QMessageBox(QtGui.QMessageBox.Warning,
                        "Send Failed", fail,
                        QtGui.QMessageBox.NoButton, self)
            msgBox.setWindowFlags(msgBox.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)
            msgBox.exec_()
            return

        status = self.main.flyLogger.edsm.submitDistances(self.systemNameLineEdit.text(), self.commanderNameLineEdit.text(), refList)

        errorMsg = None
        if status and 'distances' in status:

            print(status)

            if status['distances']:
                for distStatus in status['distances']:
                    if distStatus['msg']:
                        newStatus = distStatus['msg']

                    for ref in self.refSyslist:
                        if ref[0].text() == distStatus['name']:
                            ref[2].setText(newStatus)
                        
            
            self.submitDistancesWizard.back()
            msg = None

            if 'basesystem' in status:
                if 'msg' in status['basesystem'] and status['basesystem']['msg']:
                    msg = status['basesystem']['msg']

            if not msg:
                msg = status

            msgBox = QtGui.QMessageBox(QtGui.QMessageBox.Information,
                        "New data Send", str(msg),
                        QtGui.QMessageBox.NoButton, self)
            msgBox.setWindowFlags(msgBox.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)
            msgBox.exec_()

            if 'coords' in status['basesystem']:
                self.main.flyLogger.insertSystemCoords(self.systemNameLineEdit.text(), status['basesystem']['coords'])
            return
        elif status and "error" in status:
            errorMsg = str(status["error"][1])
        else:
            errorMsg = "Unknown Error"

        if errorMsg:
            msgBox = QtGui.QMessageBox(QtGui.QMessageBox.Warning,
                        "Send Error", errorMsg,
                        QtGui.QMessageBox.NoButton, self)
            msgBox.setWindowFlags(msgBox.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)
            msgBox.exec_()

            

    def submitDistancesEDSC(self):
        print("submitDistancesEDSC")

        self.removeOnTopFromWizard()

        refList = []
        fail = ""
        if self.systemNameLineEdit.text():
            for system in self.refSyslist:  # .append([LineEdit, DistSpinBox])
                if system[1].value() <= 0.0:
                    fail = "distance from 0 is not allowed"
                    break
                elif system[0].text() == "":
                    fail = "System name emty"
                    break
    
                refList.append({'name': system[0].text(), 'dist': system[1].value() })
                print(system[0].text(), system[1].value())
        else:
            fail = "No Target System Name"

        if fail:
            msgBox = QtGui.QMessageBox(QtGui.QMessageBox.Warning,
                        "Send Failed", fail,
                        QtGui.QMessageBox.NoButton, self)
            msgBox.setWindowFlags(msgBox.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)
            msgBox.exec_()
            return

        status = self.main.flyLogger.edsc.submitDistances(self.systemNameLineEdit.text(), self.commanderNameLineEdit.text(), refList)
        errorMsg = None
        if status and 'status' in status:
            print(status)
            if status['status']['dist']:
                for distStatus in status['status']['dist']:
                    if distStatus['status']['msg']:
                        newStatus = distStatus['status']['msg']

                    for ref in self.refSyslist:
                        if ref[0].text() == distStatus['system2']:
                            ref[2].setText(newStatus)
                        
            
            self.submitDistancesWizard.back()
            msg = None

            if 'input' in status['status'] and status['status']['input'][0]['status']['msg']:
                    msg = status['status']['input'][0]['status']['msg']

            if not msg:
                msg = status

            msgBox = QtGui.QMessageBox(QtGui.QMessageBox.Information,
                        "New data Send", str(msg),
            
                        QtGui.QMessageBox.NoButton, self)
            msgBox.setWindowFlags(msgBox.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)
            msgBox.exec_()

            if 'trilat' in status['status'] and len(status['status']['trilat']) and status['status']['trilat'][0]['system'] == self.systemNameLineEdit.text() and status['status']['trilat'][0]['coord']:
                self.main.flyLogger.insertSystemCoords(self.systemNameLineEdit.text(), status['status']['trilat'][0]['coord'])
            else:
                self.main.flyLogger.insertSystemCoords(self.systemNameLineEdit.text(), self.main.flyLogger.edsc.getSystemCoords(self.systemNameLineEdit.text()))
            return
        elif status and "error" in status:
            errorMsg = str(status["error"][1])
        else:
            errorMsg = "Unknown Error"

        if errorMsg:
            msgBox = QtGui.QMessageBox(QtGui.QMessageBox.Warning,
                        "Send Error", errorMsg,
                        QtGui.QMessageBox.NoButton, self)
            msgBox.setWindowFlags(msgBox.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)
            msgBox.exec_()


    def showLog(self):

        firstrun = False
        if not self.listView.header().count():
            firstrun = True

        self.headerList = ["Id", "System", "Distance", "Date", "Comment", ""]

        model = QtGui.QStandardItemModel(0, len(self.headerList), self)
        for x, column in enumerate(self.headerList):
            model.setHeaderData(x, QtCore.Qt.Horizontal, column)


        lastLog = self.main.flyLogger.getLastLog()

        lastSystem = None

        utcDelta = datetime.now() - datetime.utcnow()

        for entry in lastLog:
            model.insertRow(0)
            model.setData(model.index(0, self.headerList.index("Id")), entry["id"])
            model.item(0, self.headerList.index("Id")).setTextAlignment(QtCore.Qt.AlignRight)
            model.item(0, self.headerList.index("Id")).setEditable(False)

            if entry["System"]:
                model.setData(model.index(0, self.headerList.index("System")), entry["System"])
            else:
                model.setData(model.index(0, self.headerList.index("System")), entry["optionalSystemName"])
                model.item(0, self.headerList.index("System")).setBackground(QtGui.QColor(255, 0, 0, 128))

            model.item(0, self.headerList.index("System")).setEditable(False)

            if entry["System"]:
                if lastSystem:
                    distance = calcDistance(lastSystem["posX"], lastSystem["posY"], lastSystem["posZ"], entry["posX"], entry["posY"], entry["posZ"])
                    model.setData(model.index(0, self.headerList.index("Distance")), distance)
                    model.item(0, self.headerList.index("Distance")).setTextAlignment(QtCore.Qt.AlignRight)
                    model.item(0, self.headerList.index("Distance")).setEditable(False)

                lastSystem = entry
            else:
                lastSystem = None

            model.setData(model.index(0, self.headerList.index("Date")), QtCore.QDateTime(entry["DateTime"] + utcDelta))
            model.item(0, self.headerList.index("Date")).setEditable(False)

            model.setData(model.index(0, self.headerList.index("Comment")), entry["Comment"])
            model.item(0, self.headerList.index("Comment")).setEditable(True)

        model.itemChanged.connect(self.saveItemEdit)

        self.proxyModel.setSourceModel(model)
        self.proxyModel.setFilterKeyColumn(self.headerList.index("System"))

        if firstrun:
            self.listView.sortByColumn(self.headerList.index("Id"), QtCore.Qt.SortOrder.DescendingOrder)

        for i in range(0, len(self.headerList)):
            self.listView.resizeColumnToContents(i)


    def saveItemEdit(self, item):

        changesSaved = None
        logID = self.proxyModel.sourceModel().item(item.row(), self.headerList.index("Id")).data(0)

        print(logID, item.data(0), item.column())

        if self.headerList.index("Comment") == item.column() and item.data(0) is not None:
            print("save new Comment")
            changesSaved = self.main.flyLogger.updateComment(logID, item.data(0) )

        if changesSaved:
            self.main.setStatusBar("changes saved")


    def saveBookmark(self):

        indexes = self.listView.selectionModel().selectedIndexes()
        item = self.proxyModel.mapToSource( indexes[0] )
        logID = self.proxyModel.sourceModel().item(item.row(), self.headerList.index("Id")).data(0)

        logEntry = self.main.flyLogger.getLogByLogID(logID)

        if not logEntry['SystemID']:
            return


        defName = "System:%s" % (logEntry['System'])
        if logEntry['Comment']:
            defName += " (%s)" % logEntry['Comment']

        text, ok = QtGui.QInputDialog.getText(self, "Bockmark Name",
                "Bockmark Name:", QtGui.QLineEdit.Normal, defName)

        if ok and text != '':
            routeData = []

            routeData.append(   {
                                'SystemID': logEntry['SystemID'],
                                'StationID': None,
                                'ItemID': None
                                })
            self.main.lockDB()
            self.mydb.saveBookmark(text, routeData, 1)
            self.main.unlockDB()
