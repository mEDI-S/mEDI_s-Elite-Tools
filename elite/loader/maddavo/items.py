# -*- coding: UTF8
'''
Created on 23.07.2015

@author: mEDI

import or update db with system data from http://www.davek.com.au/td/Item.csv

'''
import csv

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
        if not filename: filename = 'db/Item.csv'
        
        with open(filename) as csvfile:

            simpelreader = csv.reader(csvfile, delimiter=',', quotechar="'")

            cur = self.mydb.cursor()

        
            for row in list(simpelreader)[1:]:
                #print(row)
                category = row[0]
                name = row[1]
                ui_sort = int(row[2])

                itemID = self.mydb.getItemID(name)

                if not itemID:
                    cur.execute( "insert or IGNORE into items (name, category, ui_sort ) values (?,?,?) ",
                                                                ( name,category, ui_sort) )

            self.mydb.con.commit()
            cur.close()
