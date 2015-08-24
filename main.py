# -*- coding: UTF8

'''
Created on 19.08.2015

@author: mEDI
'''

try:
    from _version import __buildid__ as v
    __buildid__ = v
    from _version import __version__ as v
    __version__ = v

    del v
except ImportError:
    __buildid__ = "UNKNOWN"
    __version__ = "UNKNOWN"

import logging
import sys


class StreamToLogger(object):
    def __init__(self, logger, log_level=logging.INFO):
        self.logger = logger
        self.log_level = log_level
        self.linebuf = ''
        self.logger.log(logging.INFO,"version: %s (%s)" % (__version__, __buildid__) )
 
    def write(self, buf):
        for line in buf.rstrip().splitlines():
            self.logger.log(self.log_level, line.rstrip())
 
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s:%(levelname)s:%(name)s:%(message)s', filename="out.log", filemode='w'
)


try:
    if __file__:
        pass
except:
    #sys.stdout = StreamToLogger( logging.getLogger('STDOUT'), logging.INFO)
    sys.stderr = StreamToLogger( logging.getLogger('STDERR'), logging.ERROR)


import elite
import gui

from PySide import QtCore, QtGui



class MainWindow(QtGui.QMainWindow):

    mydb = None
    dbworker = None
    location = None
    multiHopRouteWidget = []
    
    def __init__(self):
        super(MainWindow, self).__init__()


        self.guiMutex = QtCore.QMutex()


        self.setWindowTitle("mEDI's Elite Tools")

        self.mydb = elite.db(guiMode=True)
        self.dbworker =  gui.dbworker.new(self)
        
        self.location = elite.location(self.mydb)


        self.createActions()
        self.createMenus()
        self.createTimer()
        
        self.setStatusBar("Welcomme to mEDI's Elite Tools")

        self.setMinimumSize(640,400)

        windowsize = self.mydb.getConfig('mainwindow.size')
        if windowsize:
            windowsize = windowsize.split(",")
            self.resize(int(windowsize[0]), int(windowsize[1]))
        else:
            self.resize(640,480)


#    def contextMenuEvent(self, event):
#        menu = QtGui.QMenu(self)
#        menu.addAction(self.multiHopRouteAct)
#        menu.exec_(event.globalPos())

    def setStatusBar(self, msg):
        self.guiMutex.lock()
        self.statusBar().showMessage(msg)
        self.guiMutex.unlock()

    def multiHopRoute(self):

        mhr_widget = gui.multihoproute.Widget(self)

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
        QtGui.QMessageBox.about(self, "About",
                "Version: %s\n"
                "Build ID: %s\n"
                " " % (__version__, __buildid__))

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

        #self.mydb.updateData()
        self.dbworker.updateDB()

        self.updateDBtimer.start()

    def closeEvent( self, event ):
        if self.closeApp():
            event.accept()
        else:
            event.ignore()

    def closeApp( self ):
        self.saveOptions()
        QtGui.qApp.quit()

    def saveOptions( self ):
        size = self.size()
        
        self.mydb.setConfig( 'mainwindow.size', "%d,%d" % ( size.width(), size.height() ) )


if __name__ == '__main__':

    app = QtGui.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
