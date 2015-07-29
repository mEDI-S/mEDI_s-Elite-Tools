# -*- coding: UTF8

from elite.db import db as mydb
import timeit
import sys

start = timeit.default_timer()

db = mydb()

stop = timeit.default_timer()
print(round(stop - start, 3))
print(sys.version)
