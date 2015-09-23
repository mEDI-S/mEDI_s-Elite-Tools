# -*- coding: UTF8

import math


def calcDistance(AposX, AposY, AposZ, BposX, BposY, BposZ ):
    # #sqrt( (xA-xB)2 + (yA-yB)2 + (zA-zB)2 )
    return round(math.sqrt((AposX - BposX) ** 2 + (AposY - BposY) ** 2 + (AposZ - BposZ) ** 2), 2)


def registerSQLiteFunktions(con):
    con.create_function("calcDistance", 6, calcDistance)
