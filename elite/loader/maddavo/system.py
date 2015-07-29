# -*- coding: UTF8
'''
Created on 23.07.2015

@author: mEDI

import or update db with system data from http://www.davek.com.au/td/System.csv

'''
import csv
from datetime import datetime, date, time

class loader(object):
    '''
    this loader insert or update
    '''

    mydb = None
    
    def __init__(self,mydb):
        '''
        Constructor
        '''
        self.mydb = mydb

    def importData(self,filename=None):
        if not filename: filename = 'db/System.csv'
        
        with open(filename) as csvfile:
#            reader = csv.DictReader(csvfile, quotechar="'",quoting=csv.QUOTE_NONE)
            simpelreader = csv.reader(csvfile, delimiter=',', quotechar="'")

            cur = self.mydb.cursor()


            #get all systems 
            cur.execute( "select id, modified from systems" )
            result = cur.fetchall()
            systemCache= {}
            for system in result:
                systemCache[system["id"]] = system["modified"]
            result= None
        
            for row in list(simpelreader)[1:]:
                #print(row)
                name = row[0].lower()
                posX = float(row[1])
                posY = float(row[2])
                posZ = float(row[3])
                modifydate = datetime.strptime(row[5],"%Y-%m-%d %H:%M:%S")
                #modifydate = None

                systemID = self.mydb.getSystemIDbyName(name)

                if not systemID:
                    cur.execute( "insert or IGNORE into systems (System, posX, posY, posZ, modified) values (?,?,?,?,?) ",
                                                                ( name, posX, posY, posZ, modifydate) )
                else:
                    # update
#                    systemData = self.mydb.getSystemData(systemID)
#                    if not systemData["modified"] or  systemData["modified"] < modifydate:
                    if systemCache[systemID] < modifydate:

                        cur.execute( "update systems SET posX=?, posY=?, posZ=?, modified=? where id is ?" ,
                                                    (  posX, posY, posZ, modifydate, systemID) )

            self.mydb.con.commit()
            cur.close()
