# -*- coding: UTF8

from elite import db, elitetime

import timeit
import sys

start = timeit.default_timer()

db = db()

etime = elitetime(db,23)

wA = etime.calcTimeFromTo(15039, 1608, 763)
wB = etime.calcTimeFromTo(3113, 669, 15039)

print( wA, wB, wA+wB )

stop = timeit.default_timer()
print(round(stop - start, 3))
print(sys.version)
