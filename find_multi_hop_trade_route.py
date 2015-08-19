# -*- coding: UTF8

import timeit
import sys
import elite

start = timeit.default_timer()

mydb = elite.db()
location = elite.location(mydb)
route = elite.dealsroute(mydb)

route.setOption( "startSystem", location.getLocation() )
route.setOption( "tradingHops", 2 )
route.setOption( "maxJumpDistance", 16.3 )
route.setOption( "minStock", 10000 )
route.setOption( "maxDist", route.getOption("maxJumpDistance") * 3 )
route.setOption( "maxSearchRange", route.getOption("maxJumpDistance") * 6 )

route.calcDefaultOptions()

route.limitCalc("normal") #options (normal, fast, nice, slow, all)

route.calcRoute()

route.printList()

print(round(timeit.default_timer() - start, 3))
print(sys.version)
