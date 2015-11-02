'''
Created on 09.10.2015

@author: mEDI
'''


class outfitting(object):


    def __init__(self, mydb):
        self.mydb = mydb


    def getOutfittingCategoryID(self, category, addUnknown=None):
        if not category or category == "None":
            return

        cur = self.mydb.cursor()
        cur.execute("select id from outfitting_category where LOWER(category)=? limit 1", (category.lower(),))

        result = cur.fetchone()

        if not result and addUnknown:
            cur.execute("insert or IGNORE into outfitting_category (category) values (?) ", (category, ))
            cur.execute("select id from outfitting_category where category=? limit 1", (category, ))

            result = cur.fetchone()

        cur.close()
        if result:
            return result[0]


    def getOutfittingNameID(self, name, addUnknown=None):
        if not name:
            return

        cur = self.mydb.cursor()
        cur.execute("select id from outfitting_modulename where LOWER(modulname)=? limit 1", (name.lower(),))

        result = cur.fetchone()

        if not result and addUnknown:
            cur.execute("insert or IGNORE into outfitting_modulename (modulname) values (?) ", (name, ))
            cur.execute("select id from outfitting_modulename where modulname=? limit 1", (name, ))

            result = cur.fetchone()

        cur.close()
        if result:
            return result[0]


    def getOutfittingNameList(self):
        cur = self.mydb.cursor()

        cur.execute("select * from outfitting_modulename order by modulname")

        result = cur.fetchall()
        cur.close()
        return result


    def getRatingList(self):
        cur = self.mydb.cursor()

        cur.execute("select Rating from outfitting_modul group by Rating order by Rating")

        result = cur.fetchall()
        cur.close()
        return result


    def getMountList(self):
        cur = self.mydb.cursor()

        cur.execute("select * from outfitting_mount  order by mount")

        result = cur.fetchall()
        cur.close()
        return result


    def getOutfittingMountID(self, mount, addUnknown=None):
        if not mount:
            return

        cur = self.mydb.cursor()
        cur.execute("select id from outfitting_mount where LOWER(mount)=? limit 1", (mount.lower(),))

        result = cur.fetchone()

        if not result and addUnknown:
            cur.execute("insert or IGNORE into outfitting_mount (mount) values (?) ", (mount, ))
            cur.execute("select id from outfitting_mount where mount=? limit 1", (mount, ))

            result = cur.fetchone()

        cur.close()
        if result:
            return result[0]


    def getOutfittingGuidanceID(self, guidance, addUnknown=None):
        if not guidance:
            return

        cur = self.mydb.cursor()
        cur.execute("select id from outfitting_guidance where LOWER(guidance)=? limit 1", (guidance.lower(),))

        result = cur.fetchone()

        if not result and addUnknown:
            cur.execute("insert or IGNORE into outfitting_guidance (guidance) values (?) ", (guidance, ))
            cur.execute("select id from outfitting_guidance where guidance=? limit 1", (guidance, ))

            result = cur.fetchone()

        cur.close()
        if result:
            return result[0]


    def getOutfitting(self, nameID, distance, maxStarDist, maxAgeDate, systemID=None, classID=None, rating=None, mountID=None, shipID=None, allegiance=None, government=None):

        cur = self.mydb.cursor()


        if systemID:
            cur.execute("select posX, posY, posZ from systems  where id = ?  limit 1", (systemID, ))
            systemA = cur.fetchone()
        else:
            systemA = {"posX": 0.0, "posY": 0.0, "posZ": 0.0}


        allegianceFilter = ""
        if allegiance:
            allegianceFilter = "AND (systems.allegiance=%s OR stations.allegiance=%s)" % (allegiance, allegiance)

        governmentFilter = ""
        if government:
            governmentFilter = "AND ( systems.government=%s OR stations.government=%s)" % (government, government)

        classFilter = ""
        if classID >= 0:
            classFilter = "AND Class=%d" % classID

        ratingFilter = ""
        if rating:
            ratingFilter = "AND Rating='%s'" % rating

        mountFilter = ""
        if mountID:
            mountFilter = "AND MountID=%d" % mountID

        shipFilter = ""
        if shipID:
            shipFilter = "AND (shipID is NULL or shipID=%d)" % shipID

            
        cur.execute("""select *, calcDistance(?, ?, ?, posX, posY, posZ ) AS dist
                     FROM outfitting

                    left JOIN outfitting_modul ON outfitting_modul.id=outfitting.modulID


                    left JOIN outfitting_category ON outfitting_category.id=outfitting_modul.CategoryID
                    left JOIN outfitting_modulename ON outfitting_modulename.id=outfitting_modul.NameID
                    left JOIN outfitting_mount ON outfitting_mount.id=outfitting_modul.MountID
                    left JOIN outfitting_guidance ON outfitting_guidance.id=outfitting_modul.GuidanceID

                    left JOIN stations on stations.id = outfitting.StationID
                    left JOIN systems on systems.id = stations.SystemID

                    left JOIN ships on ships.id=outfitting_modul.ShipID

                where
                outfitting_modul.NameID=?
                AND dist <=?
                AND stations.StarDist <= ?
                AND outfitting.modifydate >= ?
                
                %s %s %s %s %s %s
                order by dist ASC
                limit 3000
                """ % (classFilter, governmentFilter, allegianceFilter, ratingFilter, mountFilter, shipFilter),
                 (systemA["posX"], systemA["posY"], systemA["posZ"], nameID, distance, maxStarDist, maxAgeDate))
        result = cur.fetchall()

        cur.close()
        return result


    def getOutfittingModulID(self, nameID, classID, mountID, categoryID, rating, guidanceID, shipID, addUnknown=None):
        cur = self.mydb.cursor()

        cur.execute("""select id FROM outfitting_modul
                            where
                            NameID=?
                            AND Class=?
                            AND MountID=?
                            AND CategoryID=?
                            AND Rating=?
                            AND GuidanceID=?
                            AND shipID=? limit 1""",
                    ( nameID, classID, mountID, categoryID, rating, guidanceID, shipID))

        result = cur.fetchone()
        if result:
            return result[0]

        if not result and addUnknown:
            cur.execute("insert  into outfitting_modul (NameID, Class, MountID, CategoryID, Rating, GuidanceID, shipID ) values (?, ?, ?, ?, ?, ?, ?)",
                        (nameID, classID, mountID, categoryID, rating, guidanceID, shipID) )
            newID = cur.lastrowid
            return newID
