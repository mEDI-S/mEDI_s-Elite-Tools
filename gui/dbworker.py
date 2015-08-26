'''
Created on 21.08.2015

@author: mEDI
'''

import elite
import timeit
from datetime import datetime

from PySide import QtCore, QtGui

databaseAccessWait = QtCore.QWaitCondition()
databaseLock = None
mutex = QtCore.QMutex()
mainClass = None
statusbarMsg = None

class _updateDBchild(QtCore.QThread):
    '''
    updatedb child job
    '''
    def sendMsg(self, newmsg):
        global statusbarMsg
        mutex.lock()
        statusbarMsg = newmsg
        mutex.unlock()
        
    def run(self):
        global databaseLock, mainClass

        mutex.lock()

        if databaseLock:
            mutex.unlock()
            return

        mutex.unlock()

        starttime = timeit.default_timer()

        mydb = elite.db(guiMode=True)
        mydb.updateData()

        self.sendMsg("Update database finished (%ss) rebuild cache now " % round(timeit.default_timer() - starttime, 2))
        starttime = timeit.default_timer()

        mydb.calcDealsInDistancesCacheQueue()

        self.sendMsg("rebuild cache finished (%ss) " % round(timeit.default_timer() - starttime, 2))

        mutex.lock()
        databaseLock = None
        databaseAccessWait.wakeOne()
        mutex.unlock()


class new(object):
    '''
    class to do long woking jobs in background
    '''
    _updatedb = None

    def __init__(self, main):
#        super(dbworker, self).__init__()
        '''
        Constructor
        '''
        global mainClass
        mainClass = main
        
        self._updatedb = _updateDBchild()

    def updateDB(self):


        if self._updatedb.isRunning():
            return

        self._updatedb.start()
        #self._updatedb.exec_()
        
        self._updatedb.setPriority(QtCore.QThread.LowPriority)

        mainClass.setStatusBar("Update database started (%s)" % datetime.now().strftime("%H:%M:%S"))


    def waitQuit(self):
        starttime = timeit.default_timer()

        if self._updatedb.isRunning():
            mainClass.setStatusBar("wait of updateDB")
        while self._updatedb.isRunning():
            #self._updatedb.terminate()
            print("wait of update %ss" % round(timeit.default_timer() - starttime, 2))
            self._updatedb.wait(1000)

    def lockDB(self):
        mutex.lock()
        databaseLock = True
        mutex.unlock()

    def unockDB(self):
        mutex.lock()

        databaseAccessWait.wakeOne()
        databaseLock = None

        mutex.unlock()

    def getStatusbarMsg(self):
        global statusbarMsg
        msg = None

        mutex.lock()

        if statusbarMsg:
            msg = statusbarMsg
            statusbarMsg = None

        mutex.unlock()

        return msg
    