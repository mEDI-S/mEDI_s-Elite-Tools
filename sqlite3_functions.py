# -*- coding: UTF8

import math

def registerSQLiteFunktions(con):
    
    def calcDistance(AposX, AposY, AposZ, BposX, BposY, BposZ ):
        # #sqrt( (xA-xB)2 + (yA-yB)2 + (zA-zB)2 )

        return math.sqrt((AposX - BposX) ** 2 + (AposY - BposY) ** 2 + (AposZ - BposZ) ** 2)


    con.create_function("calcDistance", 6, calcDistance)