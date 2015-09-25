'''
Created on 21.08.2015

@author: mEDI
'''

import elite
import timeit
from datetime import datetime
import sys
from PySide import QtCore
import threading
import traceback

databaseAccessWait = QtCore.QWaitCondition()
databaseLock = None
mutex = QtCore.QMutex()
statusbarMsg = None
processCount = 0
processPos = 0
processMsg = None
loaderCount = None

class statusMsg(object):
    processCount = 0
    processPos = 0
    msg = None
    processMsg = None

    
    def __init__(self, msg=None, processPos=None, processCount=None):
        self.processCount = processCount
        self.processPos = processPos
        self.msg = msg


class _updateDBchild(threading.Thread):
    '''
    updatedb child job
    '''
    name = "updateDBchild"
    
    def sendMsg(self, newmsg):
        global statusbarMsg
        mutex.lock()
        statusbarMsg = newmsg
        mutex.unlock()
    
    def sendProcessMsg(self, newmsg, pos=None, count=None):
        global processMsg, processPos, processCount
        mutex.lock()

        processMsg = newmsg
        if pos:
            processPos = pos
        if count:
            processCount = count

        mutex.unlock()
        
    def run(self):
        global databaseLock, loaderCount
        self._active = True

        mutex.lock()
        if databaseLock:
            mutex.unlock()
            print("databaseLock")
            return
        databaseLock = True
        mutex.unlock()

        self.sendProcessMsg("open db", 0, 0)

        starttime = timeit.default_timer()

        self.mydb = elite.db(guiMode=True)

        if not loaderCount:
            loaderCount = self.mydb.loaderCount
        else:
            self.mydb.loaderCount = loaderCount
 
        self.sendProcessMsg("Start Update", 0, loaderCount)

        self.mydb.sendProcessMsg = self.sendProcessMsg

        try:
            self.mydb.updateData()
            loaderCount = self.mydb.loaderCount
        except:
            traceback.print_exc()

            self.close()
            return

        if self._active is not True:
            self.close()
            return

        self.mydb.calcDealsInDistancesCacheQueue()

        if self._active is not True:
            self.close()
            return

        self.mydb.sendProcessMsg = None
        self.sendProcessMsg("%s finished %ss" % (datetime.now().strftime("%H:%M:%S"), round(timeit.default_timer() - starttime, 2)))

        self.close()


    def close(self):
        global databaseLock
        self.mydb.close()
        mutex.lock()
        databaseLock = None
        mutex.unlock()


    def stop(self):
        self._active = False
        self.mydb._active = False


class new(object):
    '''
    class to do long woking jobs in background
    '''
    _updatedb = None

    def __init__(self, newmain):

        self.main = newmain

    
    def start(self):
        if self._updatedb:
            self.waitQuit()

        if self.isLocked():
            return

        self._updatedb = _updateDBchild()
        self._updatedb.daemon = True
        self._updatedb.setName("updateDBchildThread")
        self._updatedb.start()

    def updateDB(self):

        if self._updatedb and self._updatedb.is_alive():
            return

        self.start()
        
        return True

    def stop(self):
        if self._updatedb and self._updatedb.is_alive():
            self._updatedb.stop()

    def waitQuit(self):

        if self._updatedb and self._updatedb.is_alive():

            self._updatedb.stop()

            while self._updatedb.is_alive():
                self._updatedb.join(0.10)

    def isLocked(self):
        global databaseLock

        mutex.lock()
        lock = databaseLock
        mutex.unlock()

        if lock:
            return True

    def lockDB(self):
        global databaseLock

        mutex.lock()
        databaseLock = True
        mutex.unlock()

    def unlockDB(self):
        global databaseLock

        mutex.lock()
        databaseLock = None
        mutex.unlock()

        databaseAccessWait.wakeOne()


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
