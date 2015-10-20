# -*- coding: UTF8

'''
Created on 02.10.2015

@author: mEDI
'''
from PySide import QtCore, QtGui
import PySide

import gui.guitools as guitools
from sqlite3_functions import calcDistance

__toolname__ = "Bookmarks"
__internalName__ = "Bo"
__statusTip__ = "Open A %s Window" % __toolname__


class tool(QtGui.QWidget):
    main = None
    mydb = None
    route = None

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


        locationLabel = QtGui.QLabel("Location:")
        self.locationlineEdit = guitools.LineEdit()
        self.locationlineEdit.setText(self.main.location.getLocation())
        self.locationlineEdit.textChanged.connect(self.showBookmarks)



        self.searchbutton = QtGui.QPushButton("Search")
        self.searchbutton.clicked.connect(self.showBookmarks)


        layout = QtGui.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        layout.addWidget(locationLabel)
        layout.addWidget(locationButton)
        
        layout.addWidget(self.locationlineEdit)
        
        layout.addWidget(self.searchbutton)

        locationGroupBox = QtGui.QGroupBox()
        locationGroupBox.setFlat(True)
        locationGroupBox.setStyleSheet("""QGroupBox {border:0;margin:0;padding:0;}  margin:0;padding:0;""")

        # locationGroupBox.setFlat(True)
        locationGroupBox.setLayout(layout)



        self.listView = QtGui.QTreeView()

        self.listView.setAlternatingRowColors(True)
        self.listView.setSortingEnabled(False)
        self.listView.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.listView.setSelectionBehavior(QtGui.QAbstractItemView.SelectItems)
        self.listView.setRootIsDecorated(True)


        self.listView.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.listView.customContextMenuRequested.connect(self.myContextMenuEvent)




        vGroupBox = QtGui.QGroupBox()
        vGroupBox.setFlat(True)

        layout = QtGui.QVBoxLayout()
        layout.setContentsMargins(6, 6, 6, 6)

        layout.addWidget(locationGroupBox)
        layout.addWidget(self.listView)

        vGroupBox.setLayout(layout)

        self.guitools.setSystemComplete("", self.locationlineEdit)

        self.showBookmarks()

        return vGroupBox


    def myContextMenuEvent(self, event):
        menu = QtGui.QMenu(self)

        menu.addAction(self.copyAct)

        indexes = self.listView.selectionModel().selectedIndexes()
        if indexes and isinstance(indexes[0].internalPointer(), BookmarkTreeItem):
            menu.addAction(self.deleteBookmarkAct)

        menu.addAction(self.reloadAct)
        menu.exec_(self.listView.viewport().mapToGlobal(event))

    def setCurentLocation(self):
        self.locationlineEdit.setText(self.main.location.getLocation())

    def createActions(self):
        self.copyAct = QtGui.QAction("Copy", self, triggered=self.guitools.copyToClipboard, shortcut=QtGui.QKeySequence.Copy)

        self.deleteBookmarkAct = QtGui.QAction("Delete Bookmark", self, triggered=self.deleteBookmark)

        self.reloadAct = QtGui.QAction("Reload Bookmarks", self, triggered=self.showBookmarks)



    def deleteBookmark(self):
        indexes = self.listView.selectionModel().selectedIndexes()
 
        if isinstance(indexes[0].internalPointer(), BookmarkTreeItem):

            treeItem = indexes[0].internalPointer()
            bockmarkID = int(treeItem.data(0))

            msg = "Are you sure you want to delete the bookmark?"
    
            msgBox = QtGui.QMessageBox(QtGui.QMessageBox.Information,
                    "Delete Bookmark", msg,
                    QtGui.QMessageBox.NoButton, self)
    
            msgBox.addButton("Delete", QtGui.QMessageBox.AcceptRole)
            msgBox.addButton("Cancel", QtGui.QMessageBox.RejectRole)
    
            if msgBox.exec_() == QtGui.QMessageBox.AcceptRole:
                self.mydb.deleteBookmark( bockmarkID )
                self.showBookmarks()


    def showBookmarks(self):

        location = self.locationlineEdit.text()
        systemID = self.mydb.getSystemIDbyName(location)
        currentSystem = None
        if systemID:
            currentSystem = self.mydb.getSystemData(systemID)


        bookmarks = self.mydb.getBookmarks()

        self.bookmarkModel = BookmarkTreeModel(bookmarks, currentSystem)


        self.listView.setModel(self.bookmarkModel)

        self.bookmarkModel.dataChanged.connect(self.saveItemEdit)


    def saveItemEdit(self, item):

        changesSaved = None
        if isinstance(item.internalPointer(), BookmarkTreeItem) and item.column() == 1:
            print(type(item.internalPointer()) )
            boockmarkID = self.listView.model().index( item.row(), 0).data()

            changesSaved = self.mydb.updateBookmarkName(boockmarkID, item.data(0) )

        if changesSaved:
            self.main.setStatusBar("changes saved")


'''
Bookmark Tree Item Model
'''


class BookmarkRootTreeItem(object):
    def __init__(self, data, parent=None):
        self.parentItem = parent
        self.itemData = data
        self.childItems = []

    def appendChild(self, item):
        self.childItems.append(item)

    def child(self, row):
        return self.childItems[row]

    def childCount(self):
        return len(self.childItems)

    def columnCount(self):
        return len(self.itemData)

    def data(self, column):
        try:
            return self.itemData[column]
        except IndexError:
            return None

    def parent(self):
        return self.parentItem

    def row(self):
        if self.parentItem:
            return self.parentItem.childItems.index(self)
        return 0



class BookmarkTreeItem(object):
    def __init__(self, data, parent=None):
        self.parentItem = parent
        self.itemData = data
        self.childItems = []

    def appendChild(self, item):
        self.childItems.append(item)

    def child(self, row):
        return self.childItems[row]

    def childCount(self):
        return len(self.childItems)

    def columnCount(self):
        return len(self.itemData)

    def data(self, column):
        try:
            return self.itemData[column]
        except IndexError:
            return None

    def setData(self, column, value):
        if column < 0 or column >= len(self.itemData):
            return False

        self.itemData[column] = value

        return True


    def parent(self):
        return self.parentItem

    def row(self):
        if self.parentItem:
            return self.parentItem.childItems.index(self)
        return 0



class BookmarkChildTreeItem(object):
    def __init__(self, data, parent=None):
        self.parentItem = parent
        self.itemData = data
        self.childItems = []

    def appendChild(self, item):
        self.childItems.append(item)

    def child(self, row):
        return self.childItems[row]

    def childCount(self):
        return len(self.childItems)

    def columnCount(self):
        return len(self.itemData)

    def data(self, column):
        try:
            return self.itemData[column]
        except IndexError:
            return None

    def parent(self):
        return self.parentItem

    def row(self):
        if self.parentItem:
            return self.parentItem.childItems.index(self)

        return 0



class BookmarkTreeModel(QtCore.QAbstractItemModel):
    def __init__(self, data, currentSystem, parent=None):
        super(BookmarkTreeModel, self).__init__(parent)
        self.currentSystem = currentSystem

        self.rootItem = BookmarkRootTreeItem(("Id.", "Name", "System", "Distance", "Station", "Item", ""))
        self.setupModelData(data, self.rootItem)

    def columnCount(self, parent):
        if parent.isValid():
            return parent.internalPointer().columnCount()
        else:
            return self.rootItem.columnCount()

    def data(self, index, role):
        if not index.isValid():
            return None

           
        if role != QtCore.Qt.DisplayRole and role != QtCore.Qt.EditRole:
            return None

        item = index.internalPointer()

        return item.data(index.column())


    def setData(self, index, value, role=QtCore.Qt.EditRole):
        if role != QtCore.Qt.EditRole:
            return False

        item = self.getItem(index)
        result = item.setData(index.column(), value)

        if result:
            self.dataChanged.emit(index, index)

        return result

    def flags(self, index):
        if not index.isValid():
            return QtCore.Qt.NoItemFlags

        if index.column() == 1 and isinstance(index.internalPointer(), BookmarkTreeItem):  # Edit Name/ Comment
            return QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
        
        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

    def getItem(self, index):
        if index.isValid():
            item = index.internalPointer()
            if item:
                return item

        return self.rootItem

    def headerData(self, section, orientation, role):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return self.rootItem.data(section)

        return None

    def index(self, row, column, parent=QtCore.QModelIndex()):
        if not self.hasIndex(row, column, parent):
            return QtCore.QModelIndex()

        if not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()

        childItem = parentItem.child(row)
        if childItem:
            return self.createIndex(row, column, childItem)
        else:
            return QtCore.QModelIndex()

    def parent(self, index):
        if not index.isValid():
            return QtCore.QModelIndex()

        childItem = index.internalPointer()
        parentItem = childItem.parent()

        if parentItem == self.rootItem:
            return QtCore.QModelIndex()

        return self.createIndex(parentItem.row(), 0, parentItem)

    def rowCount(self, parent):
        if parent.column() > 0:
            return 0

        if not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()

        return parentItem.childCount()

    def setupModelData(self, bookmarks, parent):
        parents = [parent]

        for bookmark in bookmarks:

            if bookmark['childs'] and len(bookmark['childs']) >= 1:
                distance = None
                if self.currentSystem and self.currentSystem['posX'] and bookmark['childs'][0]['posX']:
                    distance = calcDistance(self.currentSystem["posX"], self.currentSystem["posY"], self.currentSystem["posZ"], bookmark['childs'][0]["posX"], bookmark['childs'][0]["posY"], bookmark['childs'][0]["posZ"])

            system = None
            if bookmark['Type'] == 1:
                system = bookmark['childs'][0]['System']

            data = [bookmark['id'], bookmark['Name'], system, distance, "", ""]

            parents[-1].appendChild(BookmarkTreeItem(data, parents[-1]))

            if bookmark['Type'] != 1:
            
                # follow is a child
                parents.append(parents[-1].child(parents[-1].childCount() - 1))
    
                for child in bookmark['childs']:
                    distance = None
                    if self.currentSystem and self.currentSystem['posX'] and child['posX']:
                        distance = calcDistance(self.currentSystem["posX"], self.currentSystem["posY"], self.currentSystem["posZ"], child["posX"], child["posY"], child["posZ"])
    
                    data = ["", "", child['System'], distance, child['Station'], child['name']]
    
                    parents[-1].appendChild(BookmarkChildTreeItem(data, parents[-1]))
    
                parents.pop()
