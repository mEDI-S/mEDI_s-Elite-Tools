# -*- coding: UTF8
'''
EDDN - Elite Dangerous Data Network. Client
https://github.com/jamesremuscat/EDDN
'''

from elite.loader.eddn import client

def newClient(mydb):
    eddnclinet = client.loader(mydb)
    eddnclinet.start()
    return eddnclinet
