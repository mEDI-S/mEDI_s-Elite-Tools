# -*- coding: UTF8

'''
Created on 19.08.2015

@author: mEDI
'''

__defaultUpdateTime__ = 1000 * 30

import logging
import sys

try:
    from _version import __buildid__, __version__, __builddate__, __toolname__, __useragent__
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
        self.logger.log(logging.INFO, "version: %s (%s)" % (__version__, __buildid__) )
 
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
    sys.stdout = StreamToLogger( logging.getLogger('STDOUT'), logging.INFO)
    sys.stderr = StreamToLogger( logging.getLogger('STDERR'), logging.ERROR)

import elite
import gui
from PySide import QtCore, QtGui
import base64


class MainWindow(QtGui.QMainWindow):

    mydb = None
    dbworker = None
    location = None
    multiHopRouteWidget = []
    dealsFromToWidget = []
    commoditiesFinderWidget = []
    shipyardFinderWidget = []
    powerControlFinderWidget = []
    flyLogWidget = []
    BookmarksWidget = []
    
    def __init__(self):
        super(MainWindow, self).__init__()


        self.guiMutex = QtCore.QMutex()


        self.setWindowTitle("mEDI's Elite Tools")
        self.setDockOptions(QtGui.QMainWindow.AnimatedDocks | QtGui.QMainWindow.AllowNestedDocks | QtGui.QMainWindow.AllowTabbedDocks)

        self.setStatusBar("Welcome to mEDI's Elite Tools")
        self.setMinimumSize(600, 400)

        self.setWindowIcon(QtGui.QIcon(QtGui.QPixmap("img/logo.png")))

        self.addProgressBarStatusBar()

        self.clipboard = QtGui.QClipboard()

        self.mydb = elite.db(guiMode=True)
        self.mydb.cleanIgnorePriceTemp()
        self.mydb.startStreamUpdater()

        self.dbworker = gui.dbworker.new(self)

        self.location = elite.location(self.mydb)


        self.createActions()
        self.createMenus()
        self.createTimer()


        self.myPlugins = [gui.multihoproute, gui.deals_from_to, gui.commodities_finder, gui.shipyard_finder, gui.power_control_finder, gui.flylog, gui.bookmarks]
        
        self.addTool( gui.multihoproute, self.multiHopRouteWidget)
        self.addTool( gui.deals_from_to, self.dealsFromToWidget)
        self.addTool( gui.commodities_finder, self.commoditiesFinderWidget)
        self.addTool( gui.shipyard_finder, self.shipyardFinderWidget)
        self.addTool( gui.power_control_finder, self.powerControlFinderWidget)
        self.addTool( gui.flylog, self.flyLogWidget)
        self.addTool( gui.bookmarks, self.BookmarksWidget)

        self.show()

        self.loadLastWindowsOptions()

    def loadLastWindowsOptions(self):
        
        windowgeometry = self.mydb.getConfig('mainwindow.geometry')
        if windowgeometry:
            self.restoreGeometry( base64.b64decode(windowgeometry) )

        ''' restore open Widgets'''
        openWidgets = self.mydb.getConfig('mainwindow.openWidgets')
        if openWidgets:
            openWidgetsList = openWidgets.split(",")
            openWidgets = {}
            for item in openWidgetsList:
                widget = item.split(":")
                for tool in self.myPlugins:
                    count = int(widget[1])
                    if widget[0] == tool.__internalName__:
                        while count:
                            count -= 1
                            tool._openDockWidget()
        
        winState = self.mydb.getConfig('mainwindow.State')
        if winState:
            self.restoreState(  base64.b64decode(winState)  )

        
    def setStatusBar(self, msg):
        print("statusBar msg: %s" % msg)
        self.statusBar().showMessage(msg)

    def addTool(self, tool, toolsList):
    
        def createDockWidget():
        
            myWidget = tool.tool(self)
    
            toolsList.append(myWidget)
        
            widget = myWidget.getWideget()
    
            pos = len(toolsList) - 1
            title = "%s %d" % (tool.__toolname__, pos)
            self.addMyDockWidget( widget, title)

        tool._openDockWidget = createDockWidget
        toolsList.append(createDockWidget)
    
        ''' tool to tools menu '''
        myAct = QtGui.QAction(tool.__toolname__, self,
                statusTip=tool.__statusTip__, triggered=createDockWidget)
    
        self.toolsMenu.addAction(myAct)

        ''' run initRun from tool/plugin '''
        if hasattr(tool, "initRun"):
            tool.initRun(self)



    def addProgressBarStatusBar(self):
        DEFAULT_STYLE = """
                        QProgressBar{
                            border: 2px solid grey;
                            border-radius: 5px;
                            text-align: center;
                            height: 5px;
                        }
                        
                        QProgressBar::chunk {
                            background-color: lightblue;
                            width: 10px;
                            margin: 1px;
                        }
                        """

        self.statusBarProgressBar = QtGui.QProgressBar()
        self.statusBarProgressBar.setStyleSheet(DEFAULT_STYLE)
#        self.statusBarProgressBar.setRange(0, 1)
        self.statusBarProgressBar.setFormat("%v/%m")
#        self.statusBarProgressBar.setValue(5)

        self.statusBarProgressBarLabel = QtGui.QLabel("                      ")
        gridLayout = QtGui.QGridLayout()
        gridLayout.setContentsMargins(0, 0, 0, 0)
        gridLayout.addWidget(self.statusBarProgressBarLabel, 0, 0)
        gridLayout.addWidget(self.statusBarProgressBar, 0, 1, 0, 2)

        GroupBox = QtGui.QGroupBox()
        GroupBox.setStyleSheet("border:0;margin:0;padding:0")
        GroupBox.setLayout(gridLayout)

        self.statusBar().addPermanentWidget(GroupBox)

    def addMyDockWidget(self, widget, title):

        dock = QtGui.QDockWidget(title, self)
        dock.setObjectName(title)

        dock.setAllowedAreas( QtCore.Qt.AllDockWidgetAreas)
        dock.DockWidgetFeature(QtGui.QDockWidget.AllDockWidgetFeatures )
        dock.setWidget(widget)


        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, dock)
    
        self.viewMenu.addAction(dock.toggleViewAction())

        
    def createActions(self):

        self.exitAct = QtGui.QAction("E&xit", self, shortcut="Ctrl+Q",
                statusTip="Exit", triggered=self.close)

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

        #maintenance
        self.rebuildFullCacheAct = QtGui.QAction("Rebuild Full Distances Cache", self,
                statusTip="recalculate the cache can be time consuming",
                triggered=self.rebuildFullDistancesCache)

        self.deleteDistancesCacheAct = QtGui.QAction("Delete Distances Cache", self,
                statusTip="clearing the cache will slow down the search the first time, but the update speed",
                triggered=self.deleteDistancesCache)

        self.preferenceAct = QtGui.QAction("Preference", self,
                triggered=self.openConfig)

        self.forceOptimizeAct = QtGui.QAction("Force Optimize DB", self,
                statusTip="Force Optimize DB after next Update",
                triggered=self.forceOptimize)

       
    def createMenus(self):
        self.menuBar().clear()
        self.fileMenu = self.menuBar().addMenu("File")
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.exitAct)

        self.editMenu = self.menuBar().addMenu("Edit")
        self.editMenu.addSeparator()

        self.maintenanceMenu = self.editMenu.addMenu("Maintenance")
        self.maintenanceMenu.addSeparator()
        self.maintenanceMenu.addAction(self.rebuildFullCacheAct)
        self.maintenanceMenu.addAction(self.deleteDistancesCacheAct)
        self.maintenanceMenu.addAction(self.forceOptimizeAct)

        self.editMenu.addAction(self.preferenceAct)

        self.toolsMenu = self.menuBar().addMenu("Tools")
        self.toolsMenu.addSeparator()

        self.viewMenu = self.menuBar().addMenu("View")
        self.viewMenu.addSeparator()

        self.helpMenu = self.menuBar().addMenu("Help")
        self.toolsMenu.addSeparator()

        self.helpMenu.addAction(self.aboutWebsideAct)
        self.helpMenu.addAction(self.aboutChangelogAct)
        self.helpMenu.addSeparator()

        self.helpMenu.addAction(self.aboutcheckUpdateAct)
        self.helpMenu.addSeparator()
        
        self.helpMenu.addAction(self.aboutAct)
        self.helpMenu.addAction(self.aboutQtAct)

    def createTimer(self):
        self.updateDBtimer = QtCore.QTimer()
        self.updateDBtimer.start(__defaultUpdateTime__)
        self.updateDBtimer.timeout.connect(self.updateDB)

        self.childMsgPullTimer = QtCore.QTimer()
        self.childMsgPullTimer.start(500)
        self.childMsgPullTimer.timeout.connect(self.childMsgPull)


    def childMsgPull(self):
        if self.dbworker:
            msg = self.dbworker.getStatusbarMsg()
            if msg:
                if isinstance(msg, gui.dbworker.statusMsg):
                    self.statusBarProgressBarLabel.setText(msg.msg)
                    if msg.processCount:
                        self.statusBarProgressBar.setRange(0, msg.processCount)
                    if msg.processPos:
                        self.statusBarProgressBar.setValue(msg.processPos)

                else:
                    self.setStatusBar( msg )

        self.childMsgPullTimer.start()

    def updateDB(self):
        self.updateDBtimer.stop()

        status = self.dbworker.updateDB()
        if status:
            self.updateDBtimer.start(__defaultUpdateTime__)
        else:
            self.updateDBtimer.start(__defaultUpdateTime__ * 4)

    def lockDB(self):
        self.dbworker.lockDB()
        self.dbworker.waitQuit()

    def unlockDB(self):
        self.dbworker.unlockDB()

    def closeEvent( self, event ):
        if self.closeApp():
            event.accept()
        else:
            event.ignore()

    def closeApp( self ):
        self.dbworker.stop()
        self.saveOptions()
        self.mydb.stopStreamUpdater()
        self.mydb.close()
        QtGui.qApp.quit()

    def saveOptions( self ):

        self.mydb.setConfig( 'mainwindow.geometry', str( self.saveGeometry().toBase64() ) )

        self.mydb.setConfig( 'mainwindow.State', str( self.saveState().toBase64() ) )


        ''' save open Widgets'''
        openWidgets = {}

        for dock in self.findChildren(QtGui.QDockWidget):
            if not dock.isHidden():
                for tool in self.myPlugins:
                    if dock.objectName()[:len(tool.__toolname__)] == tool.__toolname__:
                        if tool.__internalName__ not in openWidgets:
                            openWidgets[tool.__internalName__] = 1
                        else:
                            openWidgets[tool.__internalName__] += 1

        openWidgetsList = []
        for dock in openWidgets:
            openWidgetsList.append( "%s:%s" % (dock, openWidgets[dock]) )

        self.mydb.setConfig( 'mainwindow.openWidgets', ",".join(openWidgetsList) )
        
        if len(self.dealsFromToWidget) > 1:  # save only from first windows
            self.dealsFromToWidget[1].saveOptions()

        if len(self.multiHopRouteWidget) > 1:  # save only from first windows
            self.multiHopRouteWidget[1].saveOptions()

        if len(self.powerControlFinderWidget) > 1:  # save only from first windows
            self.powerControlFinderWidget[1].saveOptions()

        if len(self.commoditiesFinderWidget) > 1:  # save only from first windows
            self.commoditiesFinderWidget[1].saveOptions()



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
            else:
                QtGui.QMessageBox.information(self,
                        "No new version available", "Congratulation, you are already using the latest version")


    def rebuildFullDistancesCache(self):
        msg = "Are you sure you want to delete the Cache and recalculate? recalculate the cache can be time consuming.\n"
        msg += "After the delete, the normal update process is the new cache Precalculating"

        msgBox = QtGui.QMessageBox(QtGui.QMessageBox.Information,
                "Rebuild Full Distances Cache", msg,
                QtGui.QMessageBox.NoButton, self)

        msgBox.addButton("Rebuild", QtGui.QMessageBox.AcceptRole)
        msgBox.addButton("Cancel", QtGui.QMessageBox.RejectRole)

        if msgBox.exec_() == QtGui.QMessageBox.AcceptRole:
            self.lockDB()
            self.mydb.rebuildFullDistancesCache()
            self.unlockDB()

    def deleteDistancesCache(self):
        msg = "Are you sure you want to delete the Cache?\n"
        msg += "clearing the cache will slow down the search the first time, but the update speed"

        msgBox = QtGui.QMessageBox(QtGui.QMessageBox.Information,
                "Delete Distances Cache", msg,
                QtGui.QMessageBox.NoButton, self)

        msgBox.addButton("Delete", QtGui.QMessageBox.AcceptRole)
        msgBox.addButton("Cancel", QtGui.QMessageBox.RejectRole)

        if msgBox.exec_() == QtGui.QMessageBox.AcceptRole:
            self.lockDB()
            self.mydb.rebuildFullDistancesCache()
            self.mydb.deleteDealsInDistancesSystems_queue()
            self.unlockDB()

    def openConfig(self):
        self.configWindows = gui.config.ConfigDialog(self)

        self.lockDB()
        self.configWindows.exec_()
        self.unlockDB()

    def forceOptimize(self):
        msg = "do you really want to force an optimization?"

        msgBox = QtGui.QMessageBox(QtGui.QMessageBox.Information,
                "Force Optimize", msg,
                QtGui.QMessageBox.NoButton, self)

        msgBox.addButton("Optimize", QtGui.QMessageBox.AcceptRole)
        msgBox.addButton("Cancel", QtGui.QMessageBox.RejectRole)

        if msgBox.exec_() == QtGui.QMessageBox.AcceptRole:
            self.lockDB()
            self.mydb.setConfig("lastOptimizeDatabase", None)
            self.unlockDB()
        
if __name__ == '__main__':

    app = QtGui.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
