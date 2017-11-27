# -*- coding: UTF8
'''
Created on 12.10.2017

@author: mEDI

https://eddb.io/api
loader for api V5
'''


import json
from datetime import datetime
from datetime import timedelta
import time
import gzip
import csv
#import zlib
import io, os, sys
import traceback
import elite

__DOWNLOADTMP__ = os.path.join("db", "eddbv5")
CHUNKSIZE = 16 * 1024

try:
	from _version import __buildid__, __version__, __builddate__, __toolname__, __useragent__
except ImportError:
	__buildid__ = "UNKNOWN"
	__version__ = "UNKNOWN"
	__builddate__ = "NONE"
	__toolname__ = "mEDI s Elite Tools"
	__useragent__ = '%s/%s (%s) %s(%s)' % (__toolname__.replace(" ", ""), __version__, sys.platform, __buildid__, __builddate__.replace(" ", "").replace("-", "").replace(":", ""))

try:
	''' python 2.7'''
	import urllib2
except ImportError:
	''' python 3.x'''
	import urllib.request as urllib2


_ships_ = {"Adder": 'Adder',
		   "Asp Explorer": 'Asp',
		   "Hauler": 'Hauler',
		   "Diamondback Scout": 'Diamondback Scout',
		   "Federal Dropship": 'Federal Dropship',
		   "Orca": 'Orca',
		   "Federal Gunship": 'Federal Gunship',
		   "Diamondback Explorer": 'Diamondback Explorer',
		   "Viper Mk III": 'Viper',
		   "Imperial Clipper": 'Imperial Clipper',
		   "Imperial Courier": 'Imperial Courier',
		   "Vulture": 'Vulture',
		   "Anaconda": 'Anaconda',
		   "Sidewinder Mk. I": 'Sidewinder',
		   "Federal Assault Ship": 'Federal Assault Ship',
		   "Imperial Eagle": 'Imperial Eagle',
		   "Cobra Mk. III": 'Cobra Mk III',
		   "Type-9 Heavy": 'Type-9 Heavy',
		   "Fer-de-Lance": 'Fer-de-Lance',
		   "Type-7 Transporter": 'Type-7 Transporter',
		   "Type-6 Transporter": 'Type-6 Transporter',
		   "Python": 'Python',
		   "Eagle Mk. II": 'Eagle',

		   "Cobra MK IV":'Cobra MK IV',
		   "Asp Scout": 'Asp Scout',
		   "Beluga Liner":'Beluga Liner',
		   "Dolphin": 'Dolphin',
		   "Keelback": 'Keelback',
		   "Imperial Cutter": 'Imperial Cutter',
		   "Federal Corvette": 'Federal Corvette',
		   "Viper MK IV": 'Viper MK IV'}

_category_ = {"Utility Mount": 'utility',
			  'Internal Compartment': 'internal',
			  'Essential Equipment': 'standard',
			  'Weapon Hardpoint': 'hardpoint',
			  'Bulkhead': None }

_mount_ = {'Fixed': 'Fixed', 'Gimbal': 'Gimballed', 'Turret': 'Turreted'}

_guidance_ = {32: 'Seeker', 16: 'Dumbfire' }

_powerState_ = {'Control': 1, 'Exploited': 2, 'Expansion': 3}


class loader(object):

	translateCommodities = {}
	translateSystemID = {}
	translateStationID = {}
	translatorShipsID = {}
	translatorModulID = {}
	forceImport = None
	
	def __init__(self, mydb):
		self.mydb = mydb

		self.outfitting = elite.outfitting(self.mydb)
		self.utcOffeset = datetime.now() - datetime.utcnow()


	def importData(self, forceImport=None):

		self.forceImport = forceImport
		''' 7 day update file '''

		systemsUrl = "https://eddb.io/archive/v5/systems.csv"
		systemsUrlSmal = "https://eddb.io/archive/v5/systems_recently.csv"

		lastImport = self.mydb.getConfig( 'lastEDDBimport' )
		longupdatetime = datetime.utcnow() - timedelta(days=6)

		lastImport = datetime.strptime(lastImport, "%Y-%m-%d %H:%M:%S")

		if lastImport > longupdatetime:
			systemsUrl = systemsUrlSmal

		filenameBig = os.path.join(__DOWNLOADTMP__, "systems.csv.gz")

		if os.path.isfile(filenameBig):
			if datetime.fromtimestamp(os.path.getmtime(filenameBig)) > longupdatetime:
				systemsUrl = systemsUrlSmal


		commoditiesFile = self.downloadFile("https://eddb.io/archive/v5/commodities.json")
		if commoditiesFile and commoditiesFile != False:
			commodities = self.readJosn(commoditiesFile)
			if not commodities:
				print("download error: commodities")
				return

			self.importCommodities(commodities)


		systemsFile = self.downloadFile(systemsUrl)
		if systemsFile and systemsFile != False:
			self.importSystems(systemsFile)

			
		modulesFile = self.downloadFile("https://eddb.io/archive/v5/modules.json")
		if modulesFile and modulesFile != False:
			modules = self.readJosn(modulesFile)
			if not modules:
				print("download error: modules")
				return

		stationsFile = self.downloadFile("https://eddb.io/archive/v5/stations.json")
		if stationsFile and stationsFile != False:
			stations = self.readJosn(stationsFile)

			self.importStations(stations)
			self.importOutfitting(stations, modules)
			self.importShipyard(stations)

		listingsFile = self.downloadFile("https://eddb.io/archive/v5/listings.csv")
		if listingsFile and listingsFile != False:
			self.importPrice(listingsFile)


		return






	def importPrice(self, listingsFile):
		if not os.path.isfile(listingsFile):
			return
		
		cur = self.mydb.cursor()

		# build itemPriceCache
		cur.execute(""" select price.id as id, stations.eddb_id as eddb_station_id , ItemID, price.modified from price
							left JOIN stations ON price.StationID=stations.id """)
		result = cur.fetchall()
		itemPriceCache = {}

		for item in result:
			cacheKey = "%d_%d" % (item["eddb_station_id"], item["ItemID"])
			itemPriceCache[cacheKey] = [item["id"], item["modified"]]
		result = None

		insertItemCount = 0
		insertItems = []
		updateItemCount = 0
		updateItems = []
		i = 0

		with gzip.open(listingsFile) as f:
			reader = csv.reader( f, delimiter=',', quotechar='"')
			# read the header line
			header = next(reader)
			print(header)

			for index, item in enumerate(header):
				if item == 'station_id':
					csv_station_id = index
				elif item == 'commodity_id':
					csv_commodity_id = index
				elif item == 'supply':
					csv_supply = index
				elif item == 'buy_price':
					csv_buy_price = index
				elif item == 'sell_price':
					csv_sell_price = index
				elif item == 'demand':
					csv_demand = index
				elif item == 'collected_at':
					csv_collected_at = index
					
			lastStation = 0
			for price in reader:
				i +=1

				#old id,station_id,commodity_id,supply,buy_price,sell_price,demand,collected_at,update_count
				#new id,station_id,commodity_id,supply,supply_bracket,buy_price,sell_price,demand,demand_bracket,collected_at
				itemID = self.translateCommodities[int(price[csv_commodity_id])]
				modified = datetime.fromtimestamp(int(price[csv_collected_at])) - self.utcOffeset

				itemPriceCacheKey = "%s_%d" % (price[csv_station_id], itemID)

				if itemPriceCacheKey not in itemPriceCache or itemPriceCache[itemPriceCacheKey][1] < modified:

					if lastStation != price[csv_station_id]:
						lastStation = price[csv_station_id]
						cur.execute("select id from stations where eddb_id=%s limit 1" % price[csv_station_id])
						systemresult = cur.fetchone()
						if systemresult:
							stationID = systemresult[0]

					stock = price[csv_supply]

					stationSell = price[csv_buy_price]
					stationBuy = price[csv_sell_price]
					demand = price[csv_demand]



					if itemPriceCacheKey not in itemPriceCache:
						insertItemCount += 1
						stationData = self.mydb.getStationData(stationID)
						insertItems.append([ stationData['SystemID'], stationID, itemID, stationBuy, stationSell, demand, stock, modified ])

					elif itemPriceCache[itemPriceCacheKey][1] < modified:
						updateItemCount += 1
						
						updateItems.append([ stationBuy, stationSell, demand, stock, modified, itemPriceCache[ itemPriceCacheKey][0] ])
				

		if insertItems:
			cur.executemany("insert or IGNORE into price (SystemID, StationID, ItemID, StationBuy, StationSell, Dammand, Stock, modified, source) values (?, ?, ?, ?, ?, ?, ?, ?, 4) ", insertItems)


		if updateItems:
			cur.executemany("UPDATE price SET StationBuy=?, StationSell=?, Dammand=?, Stock=?, modified=?, source=4 where id = ?", updateItems)

			
			
		if insertItemCount or updateItemCount:
			print("insert items", insertItemCount, "update items", updateItemCount, "total items", i)

		self.mydb.con.commit()
		cur.close()

			


	def importShipyard(self, stationsData):
		if not stationsData:
			return
	
		insertList = []

		cur = self.mydb.cursor()

		if not self.translatorShipsID:
			for ship in _ships_:
				self.translatorShipsID[ship] = self.mydb.getShipID(_ships_[ship], True)

		for station in stationsData:
			if station.get("shipyard_updated_at"):
				modified = datetime.fromtimestamp(station["shipyard_updated_at"]) - self.utcOffeset
			else:
				continue
			stationID = self.translateStationID[int(station["id"])]
			if not stationID:
				print("bug stationID", station["id"], "not found")
				continue
			if 'selling_ships' not in station or not station['selling_ships']:
				continue

			updateORInsert = None

			for ship in station['selling_ships']:
				shipID = self.translatorShipsID[ship]

				if shipID:

					if not updateORInsert:
						
						cur.execute("select modifydate FROM shipyard where StationID=? limit 1",
														(stationID,))
						result = cur.fetchone()
						if not result:
							updateORInsert = 1
						elif result and result['modifydate'] < modified:
							cur.execute("delete from shipyard where StationID=?", (stationID,))
							updateORInsert = 1
						else:
							updateORInsert = 2

					if updateORInsert == 1:
						cur.execute("select id from systems where eddb_id=%s limit 1" % station["system_id"])
						systemresult = cur.fetchone()
						if systemresult:
							systemID = systemresult[0]

							#systemID = self.translateSystemID[station["system_id"]]
							insertList.append([systemID, stationID, shipID, modified])

		if insertList:
			cur.executemany("insert	 into shipyard (SystemID, StationID, ShipID, modifydate ) values (?, ?, ?, ?) ", insertList)
			self.mydb.con.commit()
		cur.close()



	def importOutfitting(self, stationsData, modules):
		if not stationsData:
			return
	
		insertList = []

		cur = self.mydb.cursor()
		modulesPointer = {}


		for ship in _ships_:
			self.translatorShipsID[ship] = self.mydb.getShipID(_ships_[ship], True)

		for modul in modules:
			modulesPointer[int(modul['id'])] = modul

			shipID = 0
			if 'ship' in modul and modul['ship']:
				shipID = self.translatorShipsID[modul['ship']]

			nameID = self.outfitting.getOutfittingNameID(modul['group']['name'], True)

			mountID = 0
			if 'weapon_mode' in modul and modul['weapon_mode']:
				mount = _mount_[modul['weapon_mode']]
				mountID = self.outfitting.getOutfittingMountID(mount, True)


			if modul['group']['category'] not in _category_:
				print(modul['group']['category'])

			category = _category_[ modul['group']['category'] ]
			categoryID = 0
			if category:
				categoryID = self.outfitting.getOutfittingCategoryID( category, True)

			rating = modul['rating']

		   
			guidanceID = 0
			if 'missile_type' in modul and modul['missile_type']:
				guidance = _guidance_[ modul['missile_type'] ]
				guidanceID = self.outfitting.getOutfittingGuidanceID(guidance, True)

			classID = modul['class']


			modulID = self.outfitting.getOutfittingModulID(nameID, classID, mountID, categoryID, rating, guidanceID, shipID, True)
			self.translatorModulID[int(modul['id'])] = modulID


		for station in stationsData:
			if station.get("outfitting_updated_at"):
				modified = datetime.fromtimestamp(station["outfitting_updated_at"]) - self.utcOffeset
			else:
				continue
			stationID = self.translateStationID[int(station["id"])]
			if not stationID:
				print("bug stationID", station["id"], "not found")
				continue
			if 'selling_modules' not in station or not station['selling_modules']:
				continue

			updateORInsert = None
			for modulID in station['selling_modules']:
				modulID = self.translatorModulID[int(modulID)]

				if modulID:

					if not updateORInsert:
						
						cur.execute("select modifydate FROM outfitting where StationID=? limit 1",
														(stationID,))
						result = cur.fetchone()
						if not result:
							updateORInsert = 1
						elif result and result['modifydate'] < modified:
							cur.execute("delete from outfitting where StationID=?", (stationID,))
							updateORInsert = 1
						else:
							updateORInsert = 2

					if updateORInsert == 1:
						insertList.append([stationID, modulID, modified])

		if insertList:
			cur.executemany("insert or ignore into outfitting (StationID, modulID, modifydate ) values (?, ?, ?) ", insertList)

			self.mydb.con.commit()
		cur.close()



	def importStations(self, jsonData):
		if not jsonData:
			return
	
		cur = self.mydb.cursor()


		# build stationCache
		cur.execute("select id, Station, SystemID, modified from stations")
		result = cur.fetchall()
		stationCache = {}
		for stations in result:
			key = "%s_%s" % (stations["SystemID"], stations["Station"].lower())
			stationCache[key] = [stations["id"], stations["modified"]]
		result = None


		insertCount = 0
		updateCount = 0
		totalCount = 0
		
		updateStation = []
		testcount = 0

		for station in jsonData:
			totalCount += 1
			testcount += 1
			if testcount >= 1000:
				testcount = 0
				print(totalCount)

			modified = datetime.fromtimestamp(station["updated_at"]) - self.utcOffeset
			systemID = None
			stationID = None

			cur.execute("select id from systems where eddb_id=%s limit 1" % station["system_id"])
			systemresult = cur.fetchone()

			if systemresult:
				systemID = systemresult[0]
			else:
				print("bug in eddb Stations:system_id %s" % station["system_id"])
				continue  # this dataset is buged, drop it
			
			stationCacheKey = "%s_%s" % (systemID, station["name"].lower())

			allegianceID = self.mydb.getAllegianceID(station["allegiance"], True)

			governmentID = self.mydb.getGovernmentID(station["government"], True)

			if stationCacheKey in stationCache:
				stationID = stationCache[stationCacheKey][0]
				self.translateStationID[int(station["id"])] = stationID

			'''
			update or insert Stations
			'''
			if not stationID:
				''' add new system '''
				insertCount += 1

				cur.execute("insert or IGNORE into stations (SystemID, eddb_id, eddb_system_id, Station, StarDist, government, allegiance, blackmarket, max_pad_size, market, shipyard, outfitting, rearm, refuel, repair, modified) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ",
					(systemID, station["id"], station["system_id"], station["name"], station["distance_to_star"], governmentID, allegianceID, station["has_blackmarket"], station["max_landing_pad_size"], station["has_commodities"], station["has_shipyard"], station["has_outfitting"], station["has_rearm"], station["has_refuel"], station["has_repair"], modified))

				stationID = self.mydb.getStationID(systemID, station["name"])
				self.translateStationID[int(station["id"])] = stationID

			elif stationCache[stationCacheKey][1] < modified or self.forceImport:
				''' add new system '''
				updateCount += 1
				updateStation.append([station["name"], station["id"], station["system_id"], station["distance_to_star"], governmentID, allegianceID, station["has_blackmarket"], station["max_landing_pad_size"], station["has_commodities"], station["has_shipyard"], station["has_outfitting"], station["has_rearm"], station["has_refuel"], station["has_repair"], modified, stationID])


		if updateStation:
			cur.executemany("UPDATE stations SET Station=?, eddb_id=?, eddb_system_id=?, StarDist=?, government=?, allegiance=?, blackmarket=?, max_pad_size=?, market=?, shipyard=?, outfitting=?, rearm=?, refuel=?, repair=?, modified=? where id = ?", updateStation)

			
			
		if updateCount or insertCount:
			print("update stations:", updateCount, "insert stations:", insertCount, "from total:", totalCount)

		self.mydb.con.commit()
		cur.close()



	def importSystems(self, systemsFile):
		if not os.path.isfile(systemsFile):
			return
	
		cur = self.mydb.cursor()

		# build systemCache
		#cur.execute("select id, System, modified from systems")
		#result = cur.fetchall()
		systemCache = {}

		for system in cur.execute("select id, eddb_id, modified from systems"):
			systemCache[ system["eddb_id"] ] = [system["id"], system["modified"]]
		result = None
		#self.forceImport= 1
		insertCount = 0
		updateCount = 0
		totalCount = 0
		updateSystem = []
		with gzip.open(systemsFile) as f:
			reader = csv.reader( f, delimiter=',', quotechar='"')
			# read the header line
			header = next(reader)
			for index, item in enumerate(header):
				if item == 'name':
					csv_name = index
				elif item == 'updated_at':
					csv_updated_at = index
				elif item == 'x':
					csv_x = index
				elif item == 'y':
					csv_y = index
				elif item == 'z':
					csv_z = index
				elif item == 'needs_permit':
					csv_needs_permit = index
				elif item == 'government':
					csv_government = index
				elif item == 'allegiance':
					csv_allegiance = index
				elif item == 'power':
					csv_power = index
				elif item == 'power_state':
					csv_power_state = index
				elif item == 'id':
					csv_eddb_id = index
				elif item == 'edsm_id':
					csv_edsm_id = index

			testcount = 0
			for systemData in reader:
			
				#id,edsm_id,name,x,y,z,population,is_populated,government_id,government,allegiance_id,allegiance,state_id,state,security_id,security,primary_economy_id,primary_economy,power,power_state,power_state_id,needs_permit,updated_at,simbad_ref,controlling_minor_faction_id,controlling_minor_faction,reserve_type_id,reserve_type
				totalCount += 1
				testcount += 1
				if testcount >= 10000:
					testcount = 0
					print(totalCount)

				modified = datetime.fromtimestamp( float(systemData[csv_updated_at]) ) - self.utcOffeset
				powerID = None
				powerState = None
				
				if systemData[csv_power]:
					powerID = self.mydb.getPowerID(systemData[csv_power], True)
					powerState = _powerState_.get(systemData[csv_power_state])
					if not powerState:
						print(system["power_state"])

				allegianceID = self.mydb.getAllegianceID(systemData[csv_allegiance], True)

				governmentID = self.mydb.getGovernmentID(systemData[csv_government], True)

				''' add new system '''
				if systemData[csv_eddb_id] not in systemCache:
					insertCount += 1
					cur.execute("insert or IGNORE into systems (System, posX, posY, posZ, permit, power_control, power_state, government, allegiance, modified, eddb_id, edsm_id) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ",
											(systemData[csv_name], float(systemData[csv_x]), float(systemData[csv_y]), float(systemData[csv_z]), systemData[csv_needs_permit], powerID, powerState, governmentID, allegianceID, modified, systemData[csv_eddb_id], systemData[csv_edsm_id] ))

				
				elif systemData[csv_eddb_id] in systemCache and (not systemCache[ systemData[csv_eddb_id] ][1] or systemCache[ systemData[csv_eddb_id] ][1] < modified or self.forceImport):
					''' update system '''
					updateCount += 1
					updateSystem.append([ systemData[csv_eddb_id], systemData[csv_edsm_id], systemData[csv_name], float(systemData[csv_x]), float(systemData[csv_y]), float(systemData[csv_z]), systemData[csv_needs_permit], powerID, powerState, governmentID, allegianceID, modified, systemCache[ systemData[csv_eddb_id] ][0] ])
						
				

		if updateSystem:
			cur.executemany("update systems SET eddb_id=?, edsm_id=?, System=?, posX=?, posY=?, posZ=?, permit=?, power_control=?, power_state=?, government=?, allegiance=?, modified=? where id=?", updateSystem)

		if updateCount or insertCount:
			print("update", updateCount, "insert", insertCount, "from", totalCount, "systems")

		self.mydb.con.commit()
		cur.close()



				



	def importCommodities(self, jsonData):

		if not jsonData:
			return

		cur = self.mydb.cursor()

		for item in jsonData:

			itemID = self.mydb.getItemID(item["name"])
			averagePrice = item["average_price"]
			self.translateCommodities[ int(item["id"]) ] = itemID

			if not itemID:
				print("insert new item %s" % item["name"])

				category = item["category"]["name"]
				if category == "Unknown":
					category = None

				cur.execute("insert or IGNORE into items (name, category, average_price ) values (?, ?, ?) ",
															(item["name"], category, averagePrice))


			else:
				''' update average price '''
				cur.execute("UPDATE items SET average_price=? where id=? ", (averagePrice, itemID))

		self.mydb.con.commit()
		cur.close()


	def readJosn(self, filename):
		print("readJosn %s" % filename)

		with gzip.open(filename, "rb") as f:
			josnData = json.loads(f.read().decode("utf-8"))
			f.close()
			return josnData

	def downloadJson(self, url):
		print("download %s" % url)

		request = urllib2.Request(url)
		request.add_header('User-Agent', __useragent__)

		request.add_header('Accept-encoding', 'gzip')

		try:
			response = urllib2.urlopen(request)
		except:
			traceback.print_exc()
			return
		
		if response.info().get('Content-Encoding') == 'gzip':
			buf = io.BytesIO(response.read())
			f = gzip.GzipFile(fileobj=buf)
		else:
			f = response
		
		result = f.read()

		if result:
			try:
				josnData = json.loads(result.decode('utf-8'))
			except:
				traceback.print_exc()
				return

			return josnData


	def downloadFile(self, url):
		if not os.path.isdir(__DOWNLOADTMP__):
			print("Error: download dir '%s' not exists" % __DOWNLOADTMP__)
			return False

		print("download %s" % url)

		filename = url.rpartition('/')[2]


		request = urllib2.Request(url)
		request.add_header('User-Agent', __useragent__)

		request.add_header('Accept-encoding', 'gzip')

		try:
			response = urllib2.urlopen(request)
		except:
			traceback.print_exc()
			return

		filename = os.path.join(__DOWNLOADTMP__, filename)
		
		
		if response.info().get('Content-Encoding') == 'gzip':
			filename =  filename + ".gz"

		meta_modifiedtime = time.mktime(datetime.strptime(response.info().get('Last-Modified'), "%a, %d %b %Y %X GMT").timetuple())

		if os.path.isfile(filename) and os.path.getmtime(filename) > meta_modifiedtime:
			response.close()
			print("no new download avalibel")
			return filename

		with open(filename, 'wb') as df:
			while True:
				chunk = response.read(CHUNKSIZE)
				if not chunk:
					break
				df.write(chunk)
			'''result = ""
			z = zlib.decompressobj(zlib.MAX_WBITS|16)
			while True:
				buf = z.unconsumed_tail
				if buf == "":
					buf = response.read(8192)
					if buf == "":
						break
				got = z.decompress(buf)
				if got == "":
					break
				result = result + got
			#buf = io.BytesIO(response.read())
			#f = zlib.decompress(buf, zlib.MAX_WBITS|16)
			#f = gzip.GzipFile(fileobj=buf)'''
			df.close()
			return filename
		