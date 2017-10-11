# -*- coding: UTF8

'''
Created on 17.08.2015

@author: mEDI
'''

import os
import re
from datetime import datetime


class location(object):
    '''
    location.getLocation() return the current system
    '''

    mydb = None
    location = None
    _lastCDate = None
    _lastFile = None
    _lastPos = None

    def __init__(self, mydb):
        '''
        Constructor
        '''
        self.mydb = mydb

    def getLocation(self):

        cDate, logfile = self.getLastLog()

        if logfile:
            if not self._lastCDate or cDate > self._lastCDate:
                self._lastCDate = cDate
                self.readLog(logfile)

        if not self.location:
            self.location = ""

        return self.location

    def getLastLog(self):
        eliteLogDir = self.mydb.getConfig('EliteLogDir')

        if not os.path.isdir(eliteLogDir):
            print("Warning: EliteLogDir:'%s' does not exist" % eliteLogDir)
            return (None, None)

        logfiles = []
        for f in os.listdir(eliteLogDir):
            if os.path.isfile(os.path.join(eliteLogDir, f)) and len(f) > 4 and re.match(r"^netLog.*\.log$", f):

                path = os.path.join(eliteLogDir, f)
                cDate = datetime.fromtimestamp(os.path.getmtime(path))

                logfiles.append([cDate, path])

    
        if logfiles:
            logfiles = sorted(logfiles, key=lambda f: f[0], reverse=True)
            return (logfiles[0][0], logfiles[0][1])
        else:
            return (None, None)

    def readLog(self, logfile):

        fh = open(logfile, 'rb')

        if self._lastFile == logfile and self._lastPos:
            fh.seek(self._lastPos, 0)
        else:
            self._lastFile = logfile

        for line in fh:
            locationma = re.search("^\{\d{2}:\d{2}:\d{2}.*?\} System\:\"(.*?)\" .*", line.decode(encoding='ascii', errors='replace'))


            if locationma:
                if locationma.group(1):
                    self.location = locationma.group(1)

        self._lastPos = fh.tell()
        fh.close()
