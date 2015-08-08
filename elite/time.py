'''
Created on 07.08.2015

@author: mEDI
'''
from elite import db 
import math

# import elite

class elitetime(object):
    '''
    Time Duration Calculator
    '''

    mydb = db()
    maxJumpDist = None  # max jump distance

    '''
    default times for calc
    '''
    landingTime_outpost = 70  # 1:10    time jump in system to landing
    landingTime_station = 130  # 2:10

    tradeTime = 90  # 1:30    ~ trading and navi time

    startTime = 45  # time from Start to FS jump
    
    fs_jumpTime = 34  # loading and jump time
    fs_cooldown = 15  # cooldown time after a jump is from 10-17 sek


    def __init__(self, mydb, maxJumpDist):
        '''
        Constructor
        '''
        self.mydb = mydb
        self.maxJumpDist = maxJumpDist

    def calcTimeFromTo(self, systemAID, stationBID=None, SystemBID=None):
        '''
        calc time cost for a trip
        '''
        jumpDist = None
        time = self.startTime + self.tradeTime

        if stationBID:
            stationB = self.mydb.getStationData(stationBID)
    
            if not SystemBID:
                SystemBID = stationB["SystemID"]

        # sum of jumps
        if systemAID and SystemBID:
            jumpDist = self.mydb.getDistanceFromTo(systemAID, SystemBID)

            jumps = int(math.ceil(float(jumpDist) / self.maxJumpDist))  # round up

            time += self.calcJumpTime(jumps)

        if stationB:
            if stationB["StarDist"] > 0:
                time += self.calcTimeForDistance(stationB["StarDist"])
            else:
                print("warning: %d %s have no StarDist" % (stationBID, stationB["Station"]))

            #docking time
            if stationB["max_pad_size"] == "L":
                time += self.landingTime_station
            else:
                time += self.landingTime_outpost

        else:
            print("warning: no station data!?", systemAID, stationBID, SystemBID)
            
        return  int(round(time, 0))

    def calcTimeForDistance(self, dist):
        t = None
        
        if dist < 200:
            t = 120
        elif dist < 10000:
            t = -0.0000029 * dist ** 2 + 0.052824 * dist + 110.3806227
        else:
            x100 = dist / 100
            t = -0.000026 * x100 ** 2 + 1.842221 * x100 + 151.7497694
        return t

    def calcJumpTime(self, jumps):
        t = self.fs_jumpTime * jumps
        if jumps > 1:
            t += self.fs_cooldown * (jumps - 1)

        return t
