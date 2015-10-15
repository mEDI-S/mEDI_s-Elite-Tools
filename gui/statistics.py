'''
Created on 14.10.2015

@author: mEDI
'''

from PySide import QtCore, QtGui


def initRun(self):


    def openWindow():
        self.statistikWindow = Window(self)
        self.statistikWindow.openWindow()

    
    self.openStatisticsAct = QtGui.QAction("Statistics", self,
            statusTip="Statistics",
            triggered=openWindow)

    self.helpMenu.addAction(self.openStatisticsAct)



class Window(QtGui.QDialog):

    def __init__(self, parent):
        super(Window, self).__init__(parent)

        self.mydb = parent.mydb
        self.mainLayout = None


    def openWindow(self):

        labels = []
        values = []
        systemsWith = []
        stationsWith = []
        
        self.setStyleSheet("""

                                QLabel {  color: rgb(50, 50, 50);
                                    font-size: 11px;
                                    background-color: rgba(223, 217, 188, 250);
                                    border: 1px solid rgba(188, 188, 155, 250);
                                    margin: 0 0 0 0;
                                    padding: 2px 2px 2px 2px;
                                }
                                QLabel[labelClass='title'] {
                                    font-size: 150%;
                                    font-weight: bold;
                                    background-color: rgba(180, 237, 251, 250);
                                }
                                QLabel[labelClass='label'] {
                                    font-size: 150%;
                                    font-weight: normal;
                                    background-color: rgba(180, 237, 251, 250);
                                }
                                QGroupBox {
                                    border: 3px ridge rgba(188, 188, 155, 250);
                                    margin:0;
                                    padding:6px;
                                }
                            """)

        gridLayout = QtGui.QGridLayout()

        label = QtGui.QLabel("Total")
        label.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)
        label.setProperty('labelClass', 'title')
        gridLayout.addWidget(label, 0, 1)

        label = QtGui.QLabel("Systems with")
        label.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)
        label.setProperty('labelClass', 'title')
        gridLayout.addWidget(label, 0, 2)

        label = QtGui.QLabel("Stations with")
        label.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)
        label.setProperty('labelClass', 'title')
        gridLayout.addWidget(label, 0, 3)


        label = "Systems:"
        count = self.countTable('systems')
        labels.append(label)
        values.append(count)
        systemsWith.append(None)
        stationsWith.append(None)

        label = "Stations:"
        count = self.countTable('stations')
        countsystems = self.countTable('stations', 'SystemID')
        labels.append(label)
        values.append(count)
        systemsWith.append(countsystems)
        stationsWith.append(None)


        label = "Prices:"
        count = self.countTable('price')
        countsystems = self.countTable('price', "SystemID")
        countstations = self.countTable('price', "StationID")
        labels.append(label)
        values.append(count)
        systemsWith.append(countsystems)
        stationsWith.append(countstations)

        label = "Prices last 24h:"
        count = self.countTable('price', None, "", "where modified >= date('now','-1 day')")
        countsystems = self.countTable('price', "SystemID", "", "where modified >= date('now','-1 day')")
        countstations = self.countTable('price', "StationID", "", "where modified >= date('now','-1 day')")
        labels.append(label)
        values.append(count)
        systemsWith.append(countsystems)
        stationsWith.append(countstations)

        label = "Prices last 14Days:"
        count = self.countTable('price', None, "", "where modified >= date('now','-14 day')")
        countsystems = self.countTable('price', "SystemID", "", "where modified >= date('now','-14 day')")
        countstations = self.countTable('price', "StationID", "", "where modified >= date('now','-14 day')")
        labels.append(label)
        values.append(count)
        systemsWith.append(countsystems)
        stationsWith.append(countstations)


        label = "Prices from MMS:"
        count = self.countTable('price', None, "", "where source=1")
        countsystems = self.countTable('price', "SystemID", "", "where source=1")
        countstations = self.countTable('price', "StationID", "", "where source=1")
        labels.append(label)
        values.append(count)
        systemsWith.append(countsystems)
        stationsWith.append(countstations)


        label = "Prices from BPC:"
        count = self.countTable('price', None, "", "where source=2")
        countsystems = self.countTable('price', "SystemID", "", "where source=2")
        countstations = self.countTable('price', "StationID", "", "where source=2")
        labels.append(label)
        values.append(count)
        systemsWith.append(countsystems)
        stationsWith.append(countstations)

        label = "Prices from EDMC:"
        count = self.countTable('price', None, "", "where source=3")
        countsystems = self.countTable('price', "SystemID", "", "where source=3")
        countstations = self.countTable('price', "StationID", "", "where source=3")
        labels.append(label)
        values.append(count)
        systemsWith.append(countsystems)
        stationsWith.append(countstations)

        label = "Prices from EDDB:"
        count = self.countTable('price', None, "", "where source=4")
        countsystems = self.countTable('price', "SystemID", "", "where source=4")
        countstations = self.countTable('price', "StationID", "", "where source=4")
        labels.append(label)
        values.append(count)
        systemsWith.append(countsystems)
        stationsWith.append(countstations)

        label = "Prices from EDDN:"
        count = self.countTable('price', None, "", "where source=5")
        countsystems = self.countTable('price', "SystemID", "", "where source=5")
        countstations = self.countTable('price', "StationID", "", "where source=5")
        labels.append(label)
        values.append(count)
        systemsWith.append(countsystems)
        stationsWith.append(countstations)


        label = "Outfittings:"
        count = self.countTable('outfitting')
        countsystems = self.countTable('outfitting', "stations.SystemID", 'LEFT JOIN stations ON stations.id=StationID')
        countstations = self.countTable('outfitting', "StationID")
        labels.append(label)
        values.append(count)
        systemsWith.append(countsystems)
        stationsWith.append(countstations)



        label = "Shipyards:"
        count = self.countTable('shipyard')
        countsystems = self.countTable('shipyard', "SystemID")
        countstations = self.countTable('shipyard', "StationID")
        labels.append(label)
        values.append(count)
        systemsWith.append(countsystems)
        stationsWith.append(countstations)



        label = "Distance Cache:"
        count = self.countTable('dealsInDistances')
        countsystems = self.countTable('dealsInDistances', 'price.SystemID', 'LEFT JOIN price ON price.id=priceAID')
        countstations = self.countTable('dealsInDistances', 'price.StationID', 'LEFT JOIN price ON price.id=priceAID')
        labels.append(label)
        values.append(count)
        systemsWith.append(countsystems)
        stationsWith.append(countstations)



        label = "Prices with Distance:"
        count = self.countTable('dealsInDistances', 'priceAID')
        labels.append(label)
        values.append(count)
        systemsWith.append(None)
        stationsWith.append(None)






        for i in range(0, len(labels)):

            label = QtGui.QLabel(labels[i])
            label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
            label.setProperty('labelClass', 'label')

            gridLayout.addWidget(label, i + 1, 0)

            label = QtGui.QLabel(values[i])
            label.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)

            gridLayout.addWidget(label, i + 1, 1)

            if systemsWith[i]:
                label = QtGui.QLabel(systemsWith[i])
                label.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)

                gridLayout.addWidget(label, i + 1, 2)

            if stationsWith[i]:
                label = QtGui.QLabel(stationsWith[i])
                label.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)
                gridLayout.addWidget(label, i + 1, 3)



        mainGroup = QtGui.QGroupBox()
        mainGroup.setContentsMargins(0, 0, 0, 0)

        mainGroup.setLayout(gridLayout)


        self.mainLayout = QtGui.QVBoxLayout()
        self.mainLayout.addWidget(mainGroup)


        self.setLayout(self.mainLayout)

        self.setWindowTitle("Statistics")
        self.show()



    def countTable(self, table, DISTINCT=None, leftjoin="", withstr=""):

        if DISTINCT:
            result = self.mydb.con.execute("SELECT COUNT(DISTINCT %s) FROM %s %s %s" % (DISTINCT, table, leftjoin, withstr) )
        else:
            result = self.mydb.con.execute("SELECT COUNT(*) FROM %s %s" % (table, withstr) )
        if result:
            return str(result.fetchone()[0])
