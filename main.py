# -*- coding: UTF8

'''
Created on 19.08.2015

@author: mEDI
'''
import elite
import timeit
from gui import multihoproute

from PySide import QtCore, QtGui
from _datetime import datetime


class MainWindow(QtGui.QMainWindow):

    mydb = None
    location = None
    multiHopRouteWidget = []
    
    def __init__(self):
        super(MainWindow, self).__init__()

        self.setWindowTitle("mEDI's Elite Tools")

        self.mydb = elite.db(guiMode=True)
        self.location = elite.location(self.mydb)


        self.createActions()
        self.createMenus()
        self.createTimer()
        
        message = "Welcomme to mEDI's Elite Tools"
        self.statusBar().showMessage(message)

        self.setMinimumSize(160,160)
        self.resize(640,480)

    def contextMenuEvent(self, event):
        menu = QtGui.QMenu(self)
        menu.addAction(self.cutAct)
        menu.addAction(self.copyAct)
        menu.addAction(self.pasteAct)
        menu.exec_(event.globalPos())


    def multiHopRoute(self):

        mhr_widget = multihoproute.Widget(self)

        self.multiHopRouteWidget.append(mhr_widget)
        pos = len(self.multiHopRouteWidget)
        widget = mhr_widget.getWideget()


        dock = QtGui.QDockWidget("Multi Hop Route %d" % pos, self)
        dock.setAllowedAreas( QtCore.Qt.AllDockWidgetAreas)
#        dock.setAllowedAreas(QtCore.Qt.LeftDockWidgetArea | QtCore.Qt.RightDockWidgetArea | QtCore.Qt.TopDockWidgetArea | QtCore.Qt.BottomDockWidgetArea | QtCore.Qt.AllDockWidgetAreas)
#        dock.setFloating(True)

        dock.setWidget(widget)

        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, dock)

        self.viewMenu.addAction(dock.toggleViewAction())

        


    def about(self):
        QtGui.QMessageBox.about(self, "About Menu",
                "The <b>Menu</b> example shows how to create menu-bar menus "
                "and context menus.")

    def aboutQt(self):
        pass

    def createActions(self):

        self.exitAct = QtGui.QAction("E&xit", self, shortcut="Ctrl+Q",
                statusTip="Exit", triggered=self.close)

        self.multiHopRouteAct = QtGui.QAction("Multi Hop Route", self,
                statusTip="Open A Multi Hop Route Window", triggered=self.multiHopRoute)

        self.aboutAct = QtGui.QAction("&About", self,
                statusTip="Show the application's About box",
                triggered=self.about)

        self.aboutQtAct = QtGui.QAction("About &Qt", self,
                statusTip="Show the Qt library's About box",
                triggered=self.aboutQt)
        self.aboutQtAct.triggered.connect(QtGui.qApp.aboutQt)


    def createMenus(self):
        self.fileMenu = self.menuBar().addMenu("&File")
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.exitAct)

        self.toolsMenu = self.menuBar().addMenu("&Tools")
        self.toolsMenu.addAction(self.multiHopRouteAct)
        self.toolsMenu.addSeparator()

        self.viewMenu = self.menuBar().addMenu("&View")

        self.helpMenu = self.menuBar().addMenu("&Help")
        self.helpMenu.addAction(self.aboutAct)
        self.helpMenu.addAction(self.aboutQtAct)

    def createTimer(self):
        self.updateDBtimer = QtCore.QTimer()
        self.updateDBtimer.start(1000*60)
        self.updateDBtimer.timeout.connect(self.updateDB)


    def updateDB(self):
        self.updateDBtimer.stop()

        self.statusBar().showMessage("Update database started (%s)" % datetime.now().strftime("%H:%M:%S"))
        starttime = timeit.default_timer()

        self.mydb.updateData()
        
        self.statusBar().showMessage("Update database finished (%ss)" % round(timeit.default_timer() - starttime, 2))

        self.updateDBtimer.start()
        #self.updateDBtimer.start(1000*2)
if __name__ == '__main__':

    import sys

    app = QtGui.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
