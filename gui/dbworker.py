'''
Created on 21.08.2015

@author: mEDI
'''

import elite
import timeit
from datetime import datetime
import sys
from PySide import QtCore, QtGui

databaseAccessWait = QtCore.QWaitCondition()
databaseLock = None
mutex = QtCore.QMutex()
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
        global databaseLock
        self._active = True

        mutex.lock()
        if databaseLock:
            mutex.unlock()
            print("databaseLock")
            return
        databaseLock = True
        mutex.unlock()

        starttime = timeit.default_timer()

        self.mydb = elite.db(guiMode=True)
        self.mydb.updateData()

        if self._active != True:
            self.close()
            return

        self.sendMsg("Update database finished (%ss) rebuild cache now " % round(timeit.default_timer() - starttime, 2))
        starttime = timeit.default_timer()

        self.mydb.calcDealsInDistancesCacheQueue()

        if self._active != True:
            self.close()
            return

        self.sendMsg("rebuild cache finished (%ss) " % round(timeit.default_timer() - starttime, 2))

        self.close()

    def close(self):
        global databaseLock
        self.mydb.close()
        mutex.lock()
        databaseLock = None
        mutex.unlock()

    def terminate(self):
        self._active = False
        self.mydb._active = False
        
class new(object):
    '''
    class to do long woking jobs in background
    '''
    _updatedb = None

    def __init__(self, newmain):

        self.main = newmain
        self._updatedb = _updateDBchild()

    def updateDB(self):


        if self._updatedb.isRunning():
            return

        self._updatedb.start()
        
        self._updatedb.setPriority(QtCore.QThread.LowPriority)
        self._updatedb.setTerminationEnabled(True)
        self.main.setStatusBar("Update database started (%s)" % datetime.now().strftime("%H:%M:%S"))


    def waitQuit(self):
        starttime = timeit.default_timer()

        if self._updatedb.isRunning():
            self.main.setStatusBar("wait updateDB")

            self._updatedb.terminate()

            while self._updatedb.isRunning():
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
    