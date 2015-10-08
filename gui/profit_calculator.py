# -*- coding: UTF8

'''
Created on 08.10.2015

@author: mEDI
'''

from PySide import QtCore, QtGui
from datetime import datetime, timedelta

import gui.guitools as guitools

__toolname__ = "Profit Calculator"
__internalName__ = "PrCa"
__statusTip__ = "Open A %s Window" % __toolname__


class tool(QtGui.QWidget):
    main = None
    mydb = None
    route = None
    calcTimeStart = None
    
    def __init__(self, main):
        super(tool, self).__init__(main)

        self.main = main
        self.mydb = main.mydb
        self.guitools = guitools.guitools(self)
        self.createActions()
        self.createTimer()

    def getWideget(self):


        gridLayout = QtGui.QGridLayout()
        gridLayout.setContentsMargins(0, 0, 0, 0)

        label = QtGui.QLabel("Start Balance:")
        self.startBalance = QtGui.QLineEdit()
        self.startBalance.textChanged.connect(self.calc)
        self.startBalance.setAlignment(QtCore.Qt.AlignRight)

        gridLayout.addWidget(label, 1, 1)
        gridLayout.addWidget(self.startBalance, 1, 2)



        label = QtGui.QLabel("Current Balance:")
        self.currentBalance = QtGui.QLineEdit()
        self.currentBalance.setAlignment(QtCore.Qt.AlignRight)
        self.currentBalance.textChanged.connect(self.calc)
        gridLayout.addWidget(label, 1, 3)
        gridLayout.addWidget(self.currentBalance, 1, 4)


        label = QtGui.QLabel("Cargo Space.:")
        self.cargoSpace = QtGui.QLineEdit()
        self.cargoSpace.textChanged.connect(self.calc)
        self.cargoSpace.setAlignment(QtCore.Qt.AlignRight)
        if self.mydb.getConfig("option_cargoSpace"):
            self.cargoSpace.setText( self.mydb.getConfig("option_cargoSpace") )
        
        gridLayout.addWidget(label, 2, 1)
        gridLayout.addWidget(self.cargoSpace, 2, 2)



        label = QtGui.QLabel("Profit Total:")
        self.totalProfit = QtGui.QLineEdit()
        self.totalProfit.setAlignment(QtCore.Qt.AlignRight)
        gridLayout.addWidget(label, 3, 1)
        gridLayout.addWidget(self.totalProfit, 3, 2)


        label = QtGui.QLabel("Profit / h:")
        self.hourProfit = QtGui.QLineEdit()
        self.hourProfit.setAlignment(QtCore.Qt.AlignRight)
        gridLayout.addWidget(label, 3, 3)
        gridLayout.addWidget(self.hourProfit, 3, 4)



        label = QtGui.QLabel("Profit / t:")
        self.tonProfit = QtGui.QLineEdit()
        self.tonProfit.setAlignment(QtCore.Qt.AlignRight)
        gridLayout.addWidget(label, 4, 1)
        gridLayout.addWidget(self.tonProfit, 4, 2)


        label = QtGui.QLabel("Profit t/h:")
        self.tonHourProfit = QtGui.QLineEdit()
        self.tonHourProfit.setAlignment(QtCore.Qt.AlignRight)
        gridLayout.addWidget(label, 4, 3)
        gridLayout.addWidget(self.tonHourProfit, 4, 4)




        label = QtGui.QLabel("Time:")
        self.startCalcTimerButton = QtGui.QPushButton("Start")
        self.startCalcTimerButton.clicked.connect(self.startCalcTimer)

        resetCalcTimerButton = QtGui.QPushButton("Reset")
        resetCalcTimerButton.clicked.connect(self.resetCalcTimer)

        self.timeEdit = QtGui.QTimeEdit()
        self.timeEdit.timeChanged.connect(self.timeChanged)



        gridLayout.addWidget(label, 5, 1)
        gridLayout.addWidget(self.startCalcTimerButton, 5, 2)
        gridLayout.addWidget(resetCalcTimerButton, 5, 3)
        gridLayout.addWidget(self.timeEdit, 5, 4)


        self.calcGroupBox = QtGui.QGroupBox()
        self.calcGroupBox.setFlat(True)
        self.calcGroupBox.setLayout(gridLayout)
        self.calcGroupBox.setStyleSheet("""QGroupBox {border:0;margin:0;padding:0;}  margin:0;padding:0;""")



        vGroupBox = QtGui.QGroupBox()
        vGroupBox.setFlat(True)

        layout = QtGui.QVBoxLayout()
        layout.setContentsMargins(6, 6, 6, 6)

        layout.addWidget(self.calcGroupBox)
        layout.addStretch(1)



        vGroupBox.setLayout(layout)
        self.resetCalcTimer()

        return vGroupBox


    def timeChanged(self):
#        print("timeChanged")
        if not self.autoUpdateTimer.isActive():
            self.resetCalcTimer(False)
            myTime = self.timeEdit.time().toPython()
            self.calcTimeSum = timedelta(hours=myTime.hour, minutes=myTime.minute, seconds=myTime.second)
            self.calc()
            return


    def startCalcTimer(self):
        if self.autoUpdateTimer.isActive():
            self.pauseCalcTimer()
            self.startCalcTimerButton.setText("Start")
        else:
            self.calcTimeStart = datetime.now()
            self.autoUpdateTimer.start()
            self.startCalcTimerButton.setText("Pause")


    def pauseCalcTimer(self):
        self.autoUpdateTimer.stop()
        self.calcTimeSum = self.calcTimeSum + datetime.now() - self.calcTimeStart


    def resetCalcTimer(self, setGui=True):
        self.calcTimeSum = timedelta(0)
        self.calcTimeStart = datetime.now()
        if setGui:
            self.timeEdit.setTime( QtCore.QTime(0, 0, 0) )


    def createTimer(self):
        self.autoUpdateTimer = QtCore.QTimer()
        self.autoUpdateTimer.start(1000 * 1)
        self.autoUpdateTimer.stop()
        self.autoUpdateTimer.timeout.connect(self.calc)

    def createActions(self):
        pass


    def timedelta2qtime(self, td):
        return QtCore.QTime().addSecs(td.total_seconds())

    def calc(self):
        if not self.calcTimeStart:
            return

        tdelta = datetime.now() - self.calcTimeStart
        timeSum = self.calcTimeSum + tdelta
        self.timeEdit.setTime( self.timedelta2qtime(timeSum) )

        if guitools.isInt(self.startBalance.text()):
            startBalance = int(self.startBalance.text())
        else:
            return

        if guitools.isInt(self.currentBalance.text()):
            currentBalance = int(self.currentBalance.text())
        else:
            return

        totalProfit = currentBalance - startBalance
        self.totalProfit.setText( str(totalProfit) )

        if timeSum.total_seconds() <= 0:
            return
        hourProfit = ( totalProfit / timeSum.total_seconds() ) * 60 * 60
        hourProfit = int(round(hourProfit, 0))

        self.hourProfit.setText( str(hourProfit) )

        if guitools.isInt(self.cargoSpace.text()):
            cargoSpace = int(self.cargoSpace.text())
        else:
            return
        cargoProfit = totalProfit / cargoSpace
        self.tonProfit.setText( str( int(round(cargoProfit, 0)) ) )

        cargoHourProfit = ( cargoProfit / timeSum.total_seconds() ) * 60 * 60
        self.tonHourProfit.setText( str(int(round(cargoHourProfit, 0))) )

    def saveOptions(self):
        self.mydb.setConfig('option_cargoSpace', self.cargoSpace.text())
