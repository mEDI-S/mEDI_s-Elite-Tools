# -*- coding: UTF8

from elite import db, elitetime

import timeit
import sys
import elite.loader.eddb
import elite.loader.edsc
import elite.loader.edsm



start = timeit.default_timer()

db = db(guiMode=True)
db.initDB()

etime = elitetime(db,23)

wA = etime.calcTimeFromTo(15039, 1608, 763)
wB = etime.calcTimeFromTo(3113, 669, 15039)

print( wA, wB, wA+wB )

#elite.loader.eddb.systems.loader(db).importData("db/systems.json")
#elite.loader.eddb.stations.loader(db).importData("db/stations.json")

edsc = elite.loader.edsc.edsc()
#edsc.getSystemCoords("LP 761-93")
print(edsc.getSystemCoords("34 Pegasi"))
#edsc.getSystemCoords("Eravate")

edsm = elite.loader.edsm.edsm()
#print(edsm.getSystemCoords("LP 761-93"))
print(edsm.getSystemCoords("34 Pegasi"))


stop = timeit.default_timer()
print(round(stop - start, 3))
print(sys.version)
