# -*- coding: UTF8

'''
Created on 02.10.2015

@author: mEDI
'''
from PySide import QtCore, QtGui
import PySide

import gui.guitools as guitools

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

        layout.addWidget(self.listView)

        vGroupBox.setLayout(layout)

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

        bookmarks = self.mydb.getBookmarks()

        self.bookmarkModel = BookmarkTreeModel(bookmarks)


        self.listView.setModel(self.bookmarkModel)




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
    def __init__(self, data, parent=None):
        super(BookmarkTreeModel, self).__init__(parent)

        self.rootItem = BookmarkRootTreeItem(("Id.", "System", "Station", "Item", ""))
        self.setupModelData(data, self.rootItem)

    def columnCount(self, parent):
        if parent.isValid():
            return parent.internalPointer().columnCount()
        else:
            return self.rootItem.columnCount()

    def data(self, index, role):
        if not index.isValid():
            return None

        if role != QtCore.Qt.DisplayRole:
            return None

        item = index.internalPointer()

        return item.data(index.column())

    def flags(self, index):
        if not index.isValid():
            return QtCore.Qt.NoItemFlags

        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

    def headerData(self, section, orientation, role):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return self.rootItem.data(section)

        return None

    def index(self, row, column, parent):
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

            data = [bookmark['id'], bookmark['Name'], "", ""]
            parents[-1].appendChild(BookmarkTreeItem(data, parents[-1]))

            # follow is a child
            parents.append(parents[-1].child(parents[-1].childCount() - 1))

            for child in bookmark['childs']:
                data = ["", child['System'], child['Station'], child['name']]
                parents[-1].appendChild(BookmarkChildTreeItem(data, parents[-1]))

            parents.pop()
