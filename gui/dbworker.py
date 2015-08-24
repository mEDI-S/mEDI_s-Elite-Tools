'''
Created on 21.08.2015

@author: mEDI
'''

import elite
import timeit
from _datetime import datetime

from PySide import QtCore, QtGui

databaseAccessWait = QtCore.QWaitCondition()
databaseLock = None
mutex = QtCore.QMutex()
mainClass = None

class _updateDBchild(QtCore.QThread):
    '''
    updatedb child job
    '''
    
    def run(self):
        global databaseLock, mainClass

        mutex.lock()
        if databaseLock:
            databaseAccessWait.wait(mutex)
            databaseLock = True
        mutex.unlock()

        starttime = timeit.default_timer()

        mydb = elite.db(guiMode=True)
        mydb.updateData()

        mainClass.setStatusBar("Update database finished (%ss) rebuild cache now " % round(timeit.default_timer() - starttime, 2))
        starttime = timeit.default_timer()

        mydb.calcDealsInDistancesCacheQueue()

        mainClass.setStatusBar("rebuild cache finished (%ss) " % round(timeit.default_timer() - starttime, 2))

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
        mainClass.setStatusBar("Update database started (%s)" % datetime.now().strftime("%H:%M:%S"))


