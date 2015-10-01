# -*- coding: UTF8
'''
Created on 29.08.2015

@author: mEDI

update price and insert Shipyard data from  EDDN = Elite:Dangerous Data Network

EDDN very uncertain source
anyone can upload data, does not allow inserts only updates

'''
__sourceID__ = 5

import zlib
import zmq

import sys
import time

import random
import threading
import queue
from elite.loader.eddn.EDDNimport import EDDNimport


class _child(threading.Thread):
    """
        Options
    """
    __relayEDDNList = ['tcp://eddn-relay.elite-markets.net:9500', 'tcp://eddn-relay.ed-td.space:9500']
    __relayEDDNLast = random.randint(-1, len(__relayEDDNList) - 1)

    __relayEDDN = None
    __timeoutEDDN = 600000


    def __init__(self, data):
        threading.Thread.__init__(self)
        self.data = data
        self._active = True

    def getNextEDDNrelay(self):
        self.__relayEDDNLast += 1
        
        if self.__relayEDDNLast > len(self.__relayEDDNList) - 1:
            self.__relayEDDNLast = 0

        return self.__relayEDDNList[self.__relayEDDNLast]


    def run(self):
    
        context = zmq.Context()
        subscriber = context.socket(zmq.SUB)
        
        subscriber.setsockopt(zmq.SUBSCRIBE, b"")
        subscriber.setsockopt(zmq.RCVTIMEO, self.__timeoutEDDN)
        __message = None

        while self._active:
            try:
                self.__relayEDDN = self.getNextEDDNrelay()
                print("EDDN connect to: %s" % self.__relayEDDN)
                subscriber.connect(self.__relayEDDN)
                
                while self._active:
                    __message = subscriber.recv()
                    
                    if __message is False:
                        subscriber.disconnect(self.__relayEDDN)
                        break
                    
                    __message = zlib.decompress(__message)
                    
                    self.data.put(__message)

                    
            except zmq.ZMQError as e:
                print('ZMQSocketException: ' + str(e))
                sys.stdout.flush()
                subscriber.disconnect(self.__relayEDDN)
                time.sleep(5)

            except Exception as e:
                print(type(e))
                print(e.args)
                print(e)
            except:
                print("Unexpected error:"), sys.exc_info()

        print("child exit", self._active)

    def stop(self):
        self._active = False



class loader(object):

    def __init__(self, mydb=None):
        self.__childTask = None
        self.data = queue.Queue()
        
        self.mydb = mydb

        self.EDDNimport = EDDNimport(self.mydb)


    def start(self):
        if self.__childTask:
            self.__childTask.stop()

        self.__childTask = _child(self.data)
        self.__childTask.daemon = True
        self.__childTask.setName("EDDNchildThread")
        self.__childTask.start()

    def stop(self):
        if self.__childTask:
            self.__childTask.stop()
            
    def isRunning(self):
        if self.__childTask:
            return self.__childTask.is_alive()

    def get(self):
        return self.data.get()

    def update(self):
        if not self.data.empty():
            while not self.data.empty():
                data = self.data.get()
                if data:
                    data = data.decode(encoding='utf-8', errors='replace')
                    #print("import", data)
                    self.EDDNimport.importData(data)

            self.mydb.con.commit()

        if self.__childTask and self.isRunning() == False:
            print("restart child")
            self.start()
