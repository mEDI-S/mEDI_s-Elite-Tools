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
processCount = 0
processPos = 0
processMsg = None

class statusMsg(object):
    processCount = 0
    processPos = 0
    msg = None
    processMsg = None
    def __init__(self, msg=None, processPos=None, processCount=None):
        self.processCount = processCount
        self.processPos = processPos
        self.msg = msg
    
class _updateDBchild(QtCore.QThread):
    '''
    updatedb child job
    '''
    def sendMsg(self, newmsg):
        global statusbarMsg
        mutex.lock()
        statusbarMsg = newmsg
        mutex.unlock()
    
    def sendProcessMsg(self, newmsg, pos=None, count=None):
        global processMsg, processPos, processCount
        mutex.lock()

        processMsg = newmsg
        if pos: processPos = pos
        if count: processCount = count

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

        self.sendProcessMsg( "open db" ,0 ,0)

        starttime = timeit.default_timer()

        self.mydb = elite.db(guiMode=True)

        self.sendProcessMsg( "Start Update", 0, self.mydb.loaderCount )

        self.mydb.sendProcessMsg = self.sendProcessMsg

        self.mydb.updateData( )

        if self._active != True:
            self.close()
            return

        self.mydb.calcDealsInDistancesCacheQueue()

        if self._active != True:
            self.close()
            return

        self.mydb.sendProcessMsg = None
        self.sendProcessMsg( "%s finished %ss" % ( datetime.now().strftime("%H:%M:%S"), round(timeit.default_timer() - starttime, 2) ) )

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

        return True

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
        global statusbarMsg, processMsg, processPos, processCount
        msg = None

        mutex.lock()

        if processMsg:
            msg = statusMsg(processMsg, processPos, processCount)
            processMsg = None
        elif statusbarMsg:
            msg = statusbarMsg
            statusbarMsg = None
            
        mutex.unlock()

        return msg
    