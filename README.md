# mEDI's Elite Tools

Tools for Elite:Dangerous
========
**This app is under Heavy developend and not finished!**

## Features: ##
* Live data update and import from many sources
* Fast search
* Fake Item Filter for not existig items (Pirate data entrys)
* Ignore Item temporarily (ignored items are hidden until application restart) `over route contextmenü`
* Multi Hop Route Finder
 * Clippord Helper (push next navi point to clipbord) `start over route contextmenü`
 * Current location and active route colored 
 * Connect To Deals From To Finder to view all other deals
* Deals From To Finder
 * Station To Station
 * Station To System
* Commodities Finder
* Shipyard Finder
* Power Control Finder
* Fly Log
 * Submit Distances Wizard for EDSM and EDSC (add easy and fast new systems) `only avalibel inside a new system in contextmenü over the unknow system`
* Rares Finder
* Profit Calculator
* Outfitting Finder

## Data Sources ##
* [Live Data from EDDN - Elite:Dangerous Data Network](https://github.com/jamesremuscat/EDDN/wiki)
* [Elite: Dangerous Market Connector (EDMC) `csv files`](https://github.com/Marginal/EDMarketConnector)
* [eddb - Elite: Dangerous Database](http://eddb.io)
* [Maddavo's Market Share](http://www.davek.com.au/td/)
* [Slopey's BPC Market Tool `local installation`](https://forums.frontier.co.uk/showthread.php?t=76081)
* [EDSM - Elite Dangerous Star Map](http://www.edsm.net)
* [EDSC - EDStarCoordinator](http://edstarcoordinator.com)
* [EDDN on DynamoDB](http://edcodex.info/?m=tools&entry=133)

## Screenshot's ##
![Deals And Mult Route screenshot](screenshots/dealsAndMultRoute.jpg)

### Multi Hop Route Finder
![Multi Hop Route screenshot](screenshots/eliteTools.jpg)

### Shipyard Finder
![Shipyard Finder screenshot](screenshots/shipyardFinder.jpg)

![Multi Window screenshot](screenshots/dockwidgetexample.jpg)
multiple open tools

![Commodities Finder](screenshots/CommoditiesFinder.jpg)
Commodities Finder

![Outfitting Finder](screenshots/OutfittingFinder.jpg)
Outfitting Finder

## Usage ##
1. Select in Tools menü ur wanted tool
2. Set Options and play with this
3. Search ;)
4. Right Mousebutton `contextmenü` have on some points usefull options


## Download ##

Windows Installer without DB [Download](http://tmp.medi.li/mEDIs Elite Tools-latest-win32.msi)
Windows alpa build with DB [Download](http://tmp.medi.li/mediselitetools.7z)

linux users get the sources and start it in console `python main.py`
requiered modules: PySide, py-dateutil, pyzmq



----------

# Required #

### VerboseLogging
to get the current location
enabel VerboseLogging

Open in a texteditor  like [notepad++](https://notepad-plus-plus.org/)

`c:\Program Files (x86)\Steam\SteamApps\common\Elite Dangerous\Products\FORC-FDEV-D-1010\AppConfig.xml`

search Network and set it to

        <Network
          VerboseLogging="1"
          Port="0"
          upnpenabled="1"
          LogFile="netLog"
          DatestampLog="1"
         >
       </Network>
and restart the game
