# -*- coding: UTF8
'''
Created on 23.07.2015

@author: mEDI

only import old rares.csv

'''
import csv
from datetime import datetime, date, time, timedelta

class loader(object):
    '''
    this loader insert 
    '''

    mydb = None
    
    def __init__(self,mydb):
        '''
        Constructor
        '''
        self.mydb = mydb

    def importData(self,filename=None):
        if not filename: filename = 'db/rares.csv'
        
        with open(filename) as csvfile:

            simpelreader = csv.reader(csvfile, delimiter=',', quotechar="'")

            mylist = list(simpelreader)
            fields = mylist[0]

            cur = self.mydb.cursor()

        
            for row in mylist[1:]:
                id = row[fields.index("ID")]

                systemID = self.mydb.getSystemIDbyName( row[fields.index("System")] )

                stationID = self.mydb.getStationID(systemID, row[fields.index("Station")] )
                
                name = row[fields.index("Item")]
#                itemID = self.mydb.getItemID(item)

                price = row[fields.index("Price")]
                MaxAvail = row[fields.index("MaxAvail")]

                if row[fields.index("LastUpdated")]:
                    modifydate = datetime.strptime(row[fields.index("LastUpdated")][:19],"%Y-%m-%d %H:%M:%S")
                else:
                    modifydate =  datetime.now()

                illegal = row[fields.index("illegal")]
                offline = row[fields.index("offline")]
                comment = row[fields.index("comment")]

                if systemID and stationID:
#                    print(id,systemID,stationID, name, price, MaxAvail,modifydate, illegal , offline, comment)
                    cur.execute( "insert or IGNORE into rares (SystemID, StationID, Name, Price, MaxAvail, illegal, offline, modifydate, comment ) values (?,?,?,?,?,?,?,?,?) ",
                                                                (systemID, stationID, name, price, MaxAvail,illegal, offline, modifydate, comment  ) )


            self.mydb.con.commit()
            cur.close()
