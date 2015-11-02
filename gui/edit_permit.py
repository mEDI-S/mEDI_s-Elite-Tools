# -*- coding: UTF8

'''
Created on 02.11.2015

@author: mEDI
'''
from PySide import QtCore, QtGui
import gui.guitools as guitools


def initRun(parent):

    def openWindow():
        parent.myWindow = Window(parent)
        parent.myWindow.openWindow()

    
    parent.editPermitAct = QtGui.QAction("Edit Permit Systems", parent,
            statusTip="add or remove systems from ur permit list",
            triggered=openWindow)

    parent.editMenu.addAction(parent.editPermitAct)



class Window(QtGui.QDialog):

    def __init__(self, parent):
        super(Window, self).__init__(parent)

        self.parent = parent
        self.mydb = parent.mydb
        self.mainLayout = None
        self.guitools = guitools.guitools(self)

        self.headerList = ["Id", "System", "Authorization", ""]


    def openWindow(self):


        self.setWindowTitle("Edit Permit Systems")
        self.setMinimumSize(300, 500)

        self.listView = QtGui.QTreeView()

        self.listView.setRootIsDecorated(False)
        self.listView.setAlternatingRowColors(True)
        self.listView.setSortingEnabled(True)



        self.mainLayout = QtGui.QVBoxLayout()
        self.mainLayout.addWidget(self.listView)
        
#        self.mainLayout.addSpacing(12)



        self.setLayout(self.mainLayout)

        self.loadSystems()
        self.show()


    def triggerItemChanged(self, item):

        systemID = self.listView.model().item(item.row(), self.headerList.index("Id")).data(0)

        self.parent.lockDB()

        if item.checkState() == QtCore.Qt.CheckState.Checked:
            print("Add", systemID)
            self.mydb.addPermitSystem(systemID)
        else:
            print("Remove", systemID)
            self.mydb.removePermitSystem(systemID)

        self.parent.unlockDB()


    def loadSystems(self):

        model = QtGui.QStandardItemModel(0, len(self.headerList), self)
        for x, column in enumerate(self.headerList):
            model.setHeaderData(x, QtCore.Qt.Horizontal, column)


        systems = self.mydb.getPermitSystems()


        for system in systems:
            model.insertRow(0)
            model.setData(model.index(0, self.headerList.index("Id")), system["id"])

            model.setData(model.index(0, self.headerList.index("System")), system["System"])
            model.item(0, self.headerList.index("System")).setEditable(False)


            item = QtGui.QStandardItem('')
            if system["authorizationSystem"]:
                item.setCheckState(QtCore.Qt.Checked)
            else:
                item.setCheckState(QtCore.Qt.Unchecked)
            
            item.setCheckable(True)
            
            
            model.setItem(0, self.headerList.index("Authorization"), item)
            model.item(0, self.headerList.index("Authorization")).setEditable(False)



        self.listView.setModel(model)

        self.listView.sortByColumn(self.headerList.index("System"), QtCore.Qt.SortOrder.AscendingOrder)

        for i in range(0, len(self.headerList)):
            self.listView.resizeColumnToContents(i)

        self.listView.hideColumn(self.headerList.index("Id"))

        model.itemChanged.connect( self.triggerItemChanged )
