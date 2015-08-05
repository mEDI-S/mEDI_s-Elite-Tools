# -*- coding: UTF8

import sqlite3
import sys
import csv

from elite.system import system as elitesystem


dbPath = "db/ED4.db"

con = sqlite3.connect(dbPath)
con.row_factory = sqlite3.Row    
mysystem = elitesystem(con)

fromsys = "Laedla".lower()
tosys = "LTT 9810".lower()
print("cal from bpf data", mysystem.calcDistance(fromsys, tosys))


##csv test

with open('db/System.csv') as csvfile:
    reader = csv.DictReader(csvfile, quotechar="'",quoting=csv.QUOTE_NONE)
    simpelreader = csv.reader(csvfile, delimiter=',', quotechar="'")

    for row in list(simpelreader)[1:]:
#        print(row[0])
        # print(type( row['unq:name']) , type(fromsys))
        name = row[0].lower()
        # print(name,fromsys)
        if name == fromsys:
            fromData = row
            dataA = {"SystemX": float(row[1]),"SystemY": float(row[2]),"SystemZ": float(row[3])}
        if name == tosys:
            dataB = {"SystemX": float(row[1]),"SystemY": float(row[2]),"SystemZ": float(row[3])}
            toData = row
        #=======================================================================


print(fromData, toData)
print("cal from csv data", mysystem.calcDistanceFromData( dataA, dataB))

