# -*- coding: UTF8

'''
Created on 19.08.2015

@author: mEDI
'''

import logging
import sys

try:
    from _version import __buildid__ , __version__, __builddate__, __toolname__, __useragent__
except ImportError:
    __buildid__ = "UNKNOWN"
    __version__ = "UNKNOWN"
    __builddate__ = "NONE"
    __toolname__ = "mEDI s Elite Tools"
    __useragent__ = '%s/%s (%s) %s(%s)' % (__toolname__.replace(" ", ""), __version__, sys.platform, __buildid__, __builddate__.replace(" ", "").replace("-", "").replace(":", "") ) 




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
    dealsFromToWidget = []
    
    def __init__(self):
        super(MainWindow, self).__init__()


        self.guiMutex = QtCore.QMutex()


        self.setWindowTitle("mEDI's Elite Tools")
        self.setDockOptions(QtGui.QMainWindow.AnimatedDocks | QtGui.QMainWindow.AllowNestedDocks)

        self.mydb = elite.db(guiMode=True)
        self.mydb.startStreamUpdater()
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

        self.clipboard = QtGui.QClipboard()


    def setStatusBar(self, msg):
        print("statusBar msg: %s" % msg)
        self.statusBar().showMessage(msg)

    def multiHopRoute(self):

        mhr_widget = gui.multihoproute.Widget(self)
        self.multiHopRouteWidget.append(mhr_widget)

        widget = mhr_widget.getWideget()

        pos = len(self.multiHopRouteWidget)
        dock = QtGui.QDockWidget("Multi Hop Route %d" % pos, self)
        dock.setAllowedAreas( QtCore.Qt.AllDockWidgetAreas)
        dock.DockWidgetFeature(QtGui.QDockWidget.AllDockWidgetFeatures )

        dock.setWidget(widget)

        self.addDockWidget(QtCore.Qt.RightDockWidgetArea , dock)

        self.viewMenu.addAction(dock.toggleViewAction())


    def dealsFromToDockWidget(self):

        mhr_widget = gui.deals_from_to.Widget(self)
        self.dealsFromToWidget.append(mhr_widget)

        widget = mhr_widget.getWideget()

        pos = len(self.dealsFromToWidget)
        dock = QtGui.QDockWidget("Deals From To %d" % pos, self)
        dock.setAllowedAreas( QtCore.Qt.AllDockWidgetAreas)
        dock.DockWidgetFeature(QtGui.QDockWidget.AllDockWidgetFeatures )

        dock.setWidget(widget)

        self.addDockWidget(QtCore.Qt.RightDockWidgetArea , dock)

        self.viewMenu.addAction(dock.toggleViewAction())


        
    def createActions(self):

        self.exitAct = QtGui.QAction("E&xit", self, shortcut="Ctrl+Q",
                statusTip="Exit", triggered=self.close)

        self.multiHopRouteAct = QtGui.QAction("Multi Hop Route", self,
                statusTip="Open A Multi Hop Route Window", triggered=self.multiHopRoute)

        self.dealsFromToDockWidgetAct = QtGui.QAction("Deals From To", self,
                statusTip="Open A Deals From to Window", triggered=self.dealsFromToDockWidget)

        self.aboutWebsideAct = QtGui.QAction("Webside", self,
                statusTip="Open Webside",
                triggered=self.aboutWebside)

        self.aboutChangelogAct = QtGui.QAction("Changelog", self,
                statusTip="Open Changelog on GitHub",
                triggered=self.aboutChangelog)

        self.aboutcheckUpdateAct = QtGui.QAction("Check for Updates", self,
                statusTip="Check for Updates",
                triggered=self.checkUpdate)

        self.aboutAct = QtGui.QAction("&About", self,
                statusTip="Show the application's About box",
                triggered=self.about)

        self.aboutQtAct = QtGui.QAction("About &Qt", self,
                statusTip="Show the Qt library's About box",
                triggered=QtGui.qApp.aboutQt)

       
    def createMenus(self):
        self.fileMenu = self.menuBar().addMenu("&File")
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.exitAct)

        self.toolsMenu = self.menuBar().addMenu("&Tools")
        self.toolsMenu.addAction(self.multiHopRouteAct)
        self.toolsMenu.addAction(self.dealsFromToDockWidgetAct)

        self.toolsMenu.addSeparator()

        self.viewMenu = self.menuBar().addMenu("&View")

        self.helpMenu = self.menuBar().addMenu("&Help")

        self.helpMenu.addAction(self.aboutWebsideAct)
        self.helpMenu.addAction(self.aboutChangelogAct)
        self.helpMenu.addSeparator()

        self.helpMenu.addAction(self.aboutcheckUpdateAct)
        self.helpMenu.addSeparator()
        
        self.helpMenu.addAction(self.aboutAct)
        self.helpMenu.addAction(self.aboutQtAct)

    def createTimer(self):
        self.updateDBtimer = QtCore.QTimer()
        self.updateDBtimer.start(1000*60)
        self.updateDBtimer.timeout.connect(self.updateDB)

        self.childMsgPullTimer = QtCore.QTimer()
        self.childMsgPullTimer.start(500)
        self.childMsgPullTimer.timeout.connect(self.childMsgPull)


    def childMsgPull(self):
        if self.dbworker:
            msg = self.dbworker.getStatusbarMsg()
            if msg:
                self.setStatusBar( msg )
        self.childMsgPullTimer.start()

    def updateDB(self):
        self.updateDBtimer.stop()

        self.dbworker.updateDB()

        self.updateDBtimer.start()

    def lockDB(self):
        self.dbworker.lockDB()
        self.dbworker.waitQuit()

    def unlockDB(self):
        self.dbworker.unockDB()

    def closeEvent( self, event ):
        if self.closeApp():
            event.accept()
        else:
            event.ignore()

    def closeApp( self ):
        self.saveOptions()
        self.mydb.close()
        QtGui.qApp.quit()

    def saveOptions( self ):
        size = self.size()
        
        self.mydb.setConfig( 'mainwindow.size', "%d,%d" % ( size.width(), size.height() ) )

        if self.dealsFromToWidget: # save only from last windows
            self.dealsFromToWidget[-1].saveOptions()

        if self.multiHopRouteWidget: # save only from last windows
            self.multiHopRouteWidget[-1].saveOptions()



    def openUrl(self, url):
        url = QtCore.QUrl(url, QtCore.QUrl.StrictMode)
        if not QtGui.QDesktopServices.openUrl(url):
            QtGui.QMessageBox.warning(self, 'Open Url', 'Could not open url:%s' % url)


    def about(self):
        QtGui.QMessageBox.about(self, "About",
                "Version: %s\n"
                "Build ID: %s\n"
                "Build Date: %s\n"
                " " % (__version__, __buildid__, __builddate__))


    def aboutWebside(self):
        self.openUrl('https://github.com/mEDI-S/mEDI_s-Elite-Tools')

    def aboutChangelog(self):
        self.openUrl('https://github.com/mEDI-S/mEDI_s-Elite-Tools/commits/master')

    def checkUpdate(self):
        try:
            import urllib2
        except ImportError:
            import urllib.request as urllib2

        version = None
        url_home = "http://tmp.medi.li"
        url_version = "%s/mediselitetools.version.txt" % url_home

        try:
            request = urllib2.Request(url_version)
            request.add_header('User-Agent', __useragent__)
            response = urllib2.urlopen(request)

            if response:
                version = response.read()
        except:
            QtGui.QMessageBox.warning(self, 'Open Url', 'Could not open url')

        if version:
            version = version.strip().decode("utf-8")
            version = dict(x.split('=') for x in version.split(';'))
            #print(version)
            if version["builddate"] != __builddate__:
                url_update = "%s/%s" % (url_home, version["file"])

                msg = "a newer version is available!\n"
                msg += "\nInstalled:\n\t Version: %s\n\t Buildid: %s\n\t Build Date: %s " % (__version__, __buildid__, __builddate__)
                msg += "\nNew Version:\n\t Version: %s\n\t Buildid: %s\n\t Build Date: %s " % (version["version"], version["buildid"], version["builddate"])

                msgBox = QtGui.QMessageBox(QtGui.QMessageBox.Information,
                        "Update Available", msg,
                        QtGui.QMessageBox.NoButton, self)

                msgBox.addButton("Download", QtGui.QMessageBox.AcceptRole)
                msgBox.addButton("no thanks", QtGui.QMessageBox.RejectRole)

                if msgBox.exec_() == QtGui.QMessageBox.AcceptRole:
                    self.openUrl(url_update)


if __name__ == '__main__':

    app = QtGui.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
