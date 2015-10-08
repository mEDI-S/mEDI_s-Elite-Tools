'''
Created on 30.08.2015

@author: mEDI
'''
from PySide import QtCore, QtGui, QtSvg
from datetime import datetime


class guitools(object):


    def __init__(self, parent):
        self.parent = parent

    def getPixmapFromSvg(self, svgfile, w=48, h=48):
        svg_renderer = QtSvg.QSvgRenderer(svgfile)
        image = QtGui.QImage(w, h, QtGui.QImage.Format_ARGB32)
        image.fill(0x00000000)
        svg_renderer.render(QtGui.QPainter(image))
        pixmap = QtGui.QPixmap.fromImage(image)
        return pixmap
    
    def getIconFromsvg(self, svgfile, w=48, h=48):
        pixmap = self.getPixmapFromSvg(svgfile, w, h)
        icon = QtGui.QIcon(pixmap)
        return icon

    def setSystemComplete(self, station, editor):

        rawSysList = self.parent.mydb.getSystemsWithStationName(station)

        mylist = []
        for system in rawSysList:
            mylist.append(system["System"])

        completer = QtGui.QCompleter(mylist)
        completer.ModelSorting(QtGui.QCompleter.CaseSensitivelySortedModel)
        completer.setMaxVisibleItems(20)
        completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        editor.setCompleter(completer)


    def setStationComplete(self, system, editor):
        rawsystemlist = self.parent.mydb.getStationsFromSystem(system)

        mylist = []
        for system in rawsystemlist:
            mylist.append(system[1])

        completer = QtGui.QCompleter(mylist)
        completer.ModelSorting(QtGui.QCompleter.CaseSensitivelySortedModel)
        completer.setMaxVisibleItems(20)
        completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        completer.setCompletionMode(QtGui.QCompleter.UnfilteredPopupCompletion)
        editor.setCompleter(completer)

    def copyToClipboard(self):
        ''' copy a multi select column/row to clipboard'''
        indexes = self.parent.listView.selectedIndexes()
        clip = []
        lastRowCount = None
        for item in indexes:
            if lastRowCount is None:
                lastRowCount = item.row()
            elif lastRowCount != item.row():
                lastRowCount = item.row()
                clip.append( "\n" )
    
            if item.data():
                if isinstance( item.data(), str):
                    clip.append( item.data() )
                elif isinstance( item.data(), QtCore.QDateTime):
                    clip.append( item.data().toString("dd.MM.yyyy hh:mm:ss") )
                else:
                    #print(type(item.data()))
                    clip.append( str(item.data()) )
#                    print(type(item.data()))
        if clip:
            string = ", ".join(clip)
            self.parent.main.clipboard.setText( string.replace(", \n, ", "\n") )


class LineEdit(QtGui.QLineEdit):
    def __init__(self, parent=None):
        QtGui.QLineEdit.__init__(self, parent)

    def focusInEvent(self, event):
        QtGui.QLineEdit.focusInEvent(self, event)
        self.completer().complete()


def convertDateimeToAgeStr(dt=datetime.utcnow() ):
    age = datetime.utcnow() - dt

    if age.days >= 1:
        return "%dd" % age.days
    elif age.seconds / 60 / 60 >= 1:
        return "%dh" % (age.seconds / 60 / 60)
    else:
        return "%dm" % (age.seconds / 60)


def isInt(s):
    try:
        int(s)
        return True
    except ValueError:
        return False
