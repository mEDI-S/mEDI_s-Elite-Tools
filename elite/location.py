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
        self.eliteLogDir = self.mydb.getConfig( 'EliteLogDir' )

    def getLocation(self):

        cDate, logfile = self.getLastLog()

        if logfile:
            if not self._lastCDate or cDate > self._lastCDate:
                self._lastCDate = cDate
                self.readLog(logfile)

        if not self.location:
            self.location =  ""

        return self.location

    def getLastLog(self):
        if not os.path.isdir( self.eliteLogDir ):
            print("Warning: EliteLogDir:'%s' does not exist" % self.eliteLogDir)
            return (None,None)

        logfiles = []
        for f in os.listdir(self.eliteLogDir):
            if os.path.isfile( os.path.join(self.eliteLogDir, f) ) and len(f) > 4 and re.match(r"^netLog.*\.log$" ,f):

                path = os.path.join(self.eliteLogDir, f)
                cDate = datetime.fromtimestamp( os.path.getmtime(path) )

                logfiles.append( [cDate, path] )

    
        logfiles = sorted(logfiles , key=lambda f: f[0], reverse=True)

        return (logfiles[0][0],logfiles[0][1] )

    def readLog(self, logfile ):

        fh = open(logfile, 'rb')

        if self._lastFile == logfile and self._lastPos:
            fh.seek(self._lastPos,0)
        else:
            self._lastFile = logfile

        for line in fh:
            locationma = re.search("^\{\d{2}:\d{2}:\d{2}\} System\:\d+\((.*?)\) .*", line.decode(encoding='ascii',errors='replace') )


            if locationma:
                if locationma.group(1):
                    self.location = locationma.group(1)

        self._lastPos = fh.tell()
        fh.close()
