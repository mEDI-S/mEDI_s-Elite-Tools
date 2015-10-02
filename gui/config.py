# -*- coding: UTF8

'''
Created on 24.09.2015

@author: mEDI
'''

from PySide import QtCore, QtGui
import gui.guitools as guitools


__iconSize__ = [84, 64]


class ConfigurationPage_Path(QtGui.QWidget):
    def __init__(self, parent=None):
        super(ConfigurationPage_Path, self).__init__(parent)

        if parent and hasattr(parent, "mydb"):
            self.mydb = parent.mydb

        self.guitools = guitools.guitools(self)


        gridLayout = QtGui.QGridLayout()


        label = QtGui.QLabel("Elite Log Dir:")
        self.logPathLineEdit = QtGui.QLineEdit()
        if self.mydb.getConfig("EliteLogDir"):
            self.logPathLineEdit.setText( self.mydb.getConfig("EliteLogDir") )
        pathButton = QtGui.QToolButton()
        pathButton.setIcon(self.guitools.getIconFromsvg("img/directory.svg"))
        pathButton.clicked.connect(self.getEliteLogPath)

        gridLayout.addWidget(label, 1, 1)
        gridLayout.addWidget(self.logPathLineEdit, 1, 2)
        gridLayout.addWidget(pathButton, 1, 3)



        label = QtGui.QLabel("E:D Marked Connector dir:")
        self.EDMarkedConPathLineEdit = QtGui.QLineEdit()
        if self.mydb.getConfig("EDMarkedConnector_cvsDir"):
            self.EDMarkedConPathLineEdit.setText( self.mydb.getConfig("EDMarkedConnector_cvsDir") )
        pathButton = QtGui.QToolButton()
        pathButton.setIcon(self.guitools.getIconFromsvg("img/directory.svg"))
        pathButton.clicked.connect(self.getEDMarkedConPath)

        gridLayout.addWidget(label, 2, 1)
        gridLayout.addWidget(self.EDMarkedConPathLineEdit, 2, 2)
        gridLayout.addWidget(pathButton, 2, 3)


        label = QtGui.QLabel("Slopey's ED BPC DB:")
        self.BPCdbPathLineEdit = QtGui.QLineEdit()
        if self.mydb.getConfig("BPC_db_path"):
            self.BPCdbPathLineEdit.setText( self.mydb.getConfig("BPC_db_path") )
        pathButton = QtGui.QToolButton()
        pathButton.setIcon(self.guitools.getIconFromsvg("img/directory.svg"))
        pathButton.clicked.connect(self.getBPCdbPath)

        gridLayout.addWidget(label, 3, 1)
        gridLayout.addWidget(self.BPCdbPathLineEdit, 3, 2)
        gridLayout.addWidget(pathButton, 3, 3)



        configGroup = QtGui.QGroupBox("Path Configuration")
        configGroup.setLayout(gridLayout)


        mainLayout = QtGui.QVBoxLayout()
        mainLayout.addWidget(configGroup)
        mainLayout.addStretch(1)

        self.setLayout(mainLayout)

    def saveOptions(self):
        print("path saveOptions")
        if self.logPathLineEdit.text():
            self.mydb.setConfig('EliteLogDir', self.logPathLineEdit.text())

        if self.EDMarkedConPathLineEdit.text():
            self.mydb.setConfig('EDMarkedConnector_cvsDir', self.EDMarkedConPathLineEdit.text())

        if self.BPCdbPathLineEdit.text():
            self.mydb.setConfig('BPC_db_path', self.BPCdbPathLineEdit.text())

    def getEliteLogPath(self):
        directory = QtGui.QFileDialog.getExistingDirectory(self, "Elite Log Dir", self.logPathLineEdit.text() )

        if directory:
            self.logPathLineEdit.setText(directory)

    def getEDMarkedConPath(self):
        directory = QtGui.QFileDialog.getExistingDirectory(self, "E:D Marked Connector dir", self.EDMarkedConPathLineEdit.text() )

        if directory:
            self.EDMarkedConPathLineEdit.setText(directory)


    def getBPCdbPath(self):
        file, selFilter = QtGui.QFileDialog.getOpenFileName(self, "Slopey's ED BPC DB", self.BPCdbPathLineEdit.text(), "*.db" )

        if file:
            self.BPCdbPathLineEdit.setText(file)


class ConfigurationPage_Source(QtGui.QWidget):
    def __init__(self, parent=None):
        super(ConfigurationPage_Source, self).__init__(parent)

        if parent and hasattr(parent, "mydb"):
            self.mydb = parent.mydb

        
        self.eddnOptions = QtGui.QCheckBox("EDDN - Elite:Dangerous Data Network")
        if self.mydb.getConfig("plugin_eddn") is not 0:
            self.eddnOptions.setChecked(True)

        self.eddndynamoDBOptions = QtGui.QCheckBox("EDDN on DynamoDB")
        if self.mydb.getConfig("plugin_eddndynamoDB") is not 0:
            self.eddndynamoDBOptions.setChecked(True)

        self.eddbOptions = QtGui.QCheckBox("EDDB - Elite:Dangerous Database")
        if self.mydb.getConfig("plugin_eddb") is not 0:
            self.eddbOptions.setChecked(True)

        self.mmsOptions = QtGui.QCheckBox("Maddavo's Market Share")
        if self.mydb.getConfig("plugin_mms") is not 0:
            self.mmsOptions.setChecked(True)

        self.edmcOptions = QtGui.QCheckBox("EDMC - Elite:Dangerous Market Connector")
        if self.mydb.getConfig("plugin_edmc") is not 0:
            self.edmcOptions.setChecked(True)

        self.bpcOptions = QtGui.QCheckBox("Local Slopey's BPC Market Tool db")
        if self.mydb.getConfig("plugin_bpc") is not 0:
            self.bpcOptions.setChecked(True)

        ''' coord sources '''
        self.edsmOptions = QtGui.QCheckBox("EDSM - Elite Dangerous Star Map")
        if self.mydb.getConfig("plugin_edsm") is not 0:
            self.edsmOptions.setChecked(True)

        self.edscOptions = QtGui.QCheckBox("EDSC - Elite:Dangerous Star Coordinator")
        if self.mydb.getConfig("plugin_edsc") is not 0:
            self.edscOptions.setChecked(True)


        tradingLayout = QtGui.QVBoxLayout()
        tradingLayout.addWidget(self.eddnOptions)
        tradingLayout.addWidget(self.eddndynamoDBOptions)
        tradingLayout.addWidget(self.eddbOptions)
        tradingLayout.addWidget(self.mmsOptions)
        tradingLayout.addWidget(self.edmcOptions)
        tradingLayout.addWidget(self.bpcOptions)

        tradingDataconfigGroup = QtGui.QGroupBox("Trading Data Sources")
        tradingDataconfigGroup.setLayout(tradingLayout)


        coordsLayout = QtGui.QVBoxLayout()
        coordsLayout.addWidget(self.edsmOptions)
        coordsLayout.addWidget(self.edscOptions)

        coordsDataconfigGroup = QtGui.QGroupBox("Coordinates Sources")
        coordsDataconfigGroup.setLayout(coordsLayout)


        mainLayout = QtGui.QVBoxLayout()
        mainLayout.addWidget(tradingDataconfigGroup)
        mainLayout.addWidget(coordsDataconfigGroup)
        mainLayout.addStretch(1)

        self.setLayout(mainLayout)

    def saveOptions(self):
        print("source saveOptions")
        restartStreamer = None
        
        
        if (self.eddnOptions.isChecked() and self.mydb.getConfig("plugin_eddn") is not 1) or (not self.eddnOptions.isChecked() and self.mydb.getConfig("plugin_eddn") is not 0 ):
            restartStreamer = True
            
        self.mydb.setConfig('plugin_eddn', self.eddnOptions.isChecked())
        self.mydb.setConfig('plugin_eddndynamoDB', self.eddndynamoDBOptions.isChecked())
        self.mydb.setConfig('plugin_eddb', self.eddbOptions.isChecked())
        self.mydb.setConfig('plugin_mms', self.mmsOptions.isChecked())
        self.mydb.setConfig('plugin_edmc', self.edmcOptions.isChecked())
        self.mydb.setConfig('plugin_bpc', self.bpcOptions.isChecked())

        self.mydb.setConfig('plugin_edsm', self.edsmOptions.isChecked())
        self.mydb.setConfig('plugin_edsc', self.edscOptions.isChecked())

        if restartStreamer:
            print("restartStreamer")
            self.mydb.stopStreamUpdater()
            self.mydb.startStreamUpdater()


class ConfigurationPage_Search(QtGui.QWidget):
    def __init__(self, parent=None):
        super(ConfigurationPage_Search, self).__init__(parent)

        if parent and hasattr(parent, "mydb"):
            self.mydb = parent.mydb

        self.guitools = guitools.guitools(self)


        gridLayout = QtGui.QGridLayout()

        calcDistanceOptionsList = ["when searching", "After searching in the background"]

        label = QtGui.QLabel("calculate missing Distances:")
        self.calcDistanceOption = QtGui.QComboBox()
        for option in calcDistanceOptionsList:
            self.calcDistanceOption.addItem(option)

        if self.mydb.getConfig("option_calcDistance"):
            self.calcDistanceOption.setCurrentIndex(self.mydb.getConfig("option_calcDistance"))

        gridLayout.addWidget(label, 1, 1)
        gridLayout.addWidget(self.calcDistanceOption, 1, 2)


        configGroup = QtGui.QGroupBox("Search Configuration")
        configGroup.setLayout(gridLayout)


        mainLayout = QtGui.QVBoxLayout()
        mainLayout.addWidget(configGroup)
        mainLayout.addStretch(1)

        self.setLayout(mainLayout)

    def saveOptions(self):
        print("search saveOptions")
        self.mydb.setConfig('option_calcDistance', self.calcDistanceOption.currentIndex())


class ConfigDialog(QtGui.QDialog):
    def __init__(self, parent=None):
        super(ConfigDialog, self).__init__(parent)

        if parent and hasattr(parent, "mydb"):
            self.mydb = parent.mydb

        self.setMinimumSize(800, 400)

        self.guitools = guitools.guitools(self)

        self.contentsWidget = QtGui.QListWidget()
        self.contentsWidget.setViewMode(QtGui.QListView.IconMode)
        self.contentsWidget.setIconSize(QtCore.QSize(__iconSize__[0], __iconSize__[1]))
        self.contentsWidget.setMovement(QtGui.QListView.Static)
        self.contentsWidget.setMaximumWidth(__iconSize__[0] + 12 * 2)
        self.contentsWidget.setSpacing(6)

        self.pagesWidget = QtGui.QStackedWidget()

        self.pagesWidget.addWidget(ConfigurationPage_Path(self))
        self.pagesWidget.addWidget(ConfigurationPage_Source(self))
        self.pagesWidget.addWidget(ConfigurationPage_Search(self))
        

        closeButton = QtGui.QPushButton("Close")
        saveButton = QtGui.QPushButton("Save")

        self.createIcons()
        self.contentsWidget.setCurrentRow(0)

        closeButton.clicked.connect(self.close)
        saveButton.clicked.connect(self.saveOptions)

        horizontalLayout = QtGui.QHBoxLayout()
        horizontalLayout.addWidget(self.contentsWidget)
        horizontalLayout.addWidget(self.pagesWidget, 1)

        buttonsLayout = QtGui.QHBoxLayout()
        buttonsLayout.addStretch(1)
        buttonsLayout.addWidget(saveButton)
        buttonsLayout.addWidget(closeButton)

        mainLayout = QtGui.QVBoxLayout()
        mainLayout.addLayout(horizontalLayout)
#        mainLayout.addStretch(1)
        mainLayout.addSpacing(12)
        mainLayout.addLayout(buttonsLayout)

        self.setLayout(mainLayout)

        self.setWindowTitle("Config")

    def saveOptions(self):
        print("main saveOptions")

        for configWidget in self.pagesWidget.findChildren(QtGui.QWidget):
            if hasattr(configWidget, "saveOptions" ):
                configWidget.saveOptions()





    def changePage(self, current, previous):
        if not current:
            current = previous

        self.pagesWidget.setCurrentIndex(self.contentsWidget.row(current))

    def createIcons(self):
        configButton_Path = QtGui.QListWidgetItem(self.contentsWidget)
        configButton_Path.setIcon( self.guitools.getIconFromsvg("img/pathConfig.svg", __iconSize__[0], __iconSize__[1]))
        configButton_Path.setText("Path")
        configButton_Path.setTextAlignment(QtCore.Qt.AlignHCenter)
        configButton_Path.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)


        configButton_Source = QtGui.QListWidgetItem(self.contentsWidget)
        configButton_Source.setIcon( self.guitools.getIconFromsvg("img/Datasources.svg", __iconSize__[0], __iconSize__[1]))
        configButton_Source.setText("Source")
        configButton_Source.setTextAlignment(QtCore.Qt.AlignHCenter)
        configButton_Source.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)

        configButton_Source = QtGui.QListWidgetItem(self.contentsWidget)
        configButton_Source.setIcon( self.guitools.getIconFromsvg("img/searchOptions.svg", __iconSize__[0], __iconSize__[1]))
        configButton_Source.setText("Search")
        configButton_Source.setTextAlignment(QtCore.Qt.AlignHCenter)
        configButton_Source.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)


        self.contentsWidget.currentItemChanged.connect(self.changePage)

if __name__ == '__main__':

    import sys

    app = QtGui.QApplication(sys.argv)
    configWindows = ConfigDialog()
    sys.exit(configWindows.exec_())
