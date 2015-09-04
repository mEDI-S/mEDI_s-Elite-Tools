# -*- coding: UTF8

'''
usage:
c:\Python34_32\python.exe setup.py build

http://cx-freeze.readthedocs.org/en/latest/distutils.html
'''


from cx_Freeze import setup, Executable
import os
import sys
import shutil
import subprocess
import elite
from datetime import datetime, timedelta


__version__ = "0.1"
__buildid__ = ""
__builddate__ = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
__ZIPFILE__ = "mediselitetools.7z"
__toolname__ = "mEDI s Elite Tools"


VERSION_PY = """# This file is originally generated from Git information by running 'setup.py
__buildid__ = '%s'
__version__ = '%s'
__builddate__ = '%s'
__toolname__ = '%s'

import sys

__useragent__ = '%%s/%%s (%%s) %%s(%%s)' %% (__toolname__.replace(' ', ''), __version__, sys.platform, __buildid__, __builddate__.replace(' ', '').replace('-', '').replace(':', '') ) 

"""

VERSION_HOMEPAGE = """buildid=%s;version=%s;file=%s;builddate=%s"""


buildpath = r"build\exe.win32-3.4/"
if os.path.isdir(buildpath):
    shutil.rmtree(buildpath)
    pass



def update_version_py():
    if not os.path.isdir(".git"):
        print("This does not appear to be a Git repository.")
        return
    try:
        p = subprocess.Popen(["git", "describe",
                              "--tags", "--dirty", "--always"],
                             stdout=subprocess.PIPE)
    except EnvironmentError:
        print("unable to run git, leaving _version.py alone")
        return
    stdout = p.communicate()[0]
    if p.returncode != 0:
        print("unable to run git, leaving _version.py alone")
        return

    __buildid__ = stdout.strip().decode("utf-8")

    f = open("_version.py", "w")
    f.write(VERSION_PY % (__buildid__, __version__, __builddate__, __toolname__))
    f.close()
    print("_version.py to '%s'" % __buildid__)

    ''' create versions file '''

    f = open("build/mediselitetools.version.txt", "w")
    f.write(VERSION_HOMEPAGE % (__buildid__, __version__, __ZIPFILE__, __builddate__))
    f.close()


update_version_py()
imgPath = "img"
includeFilesList = [["db/my.db","db/my.db"],["db/rares.csv","db/rares.csv"]]

#add img
for f in os.listdir(imgPath):
    includeFilesList.append( [os.path.join(imgPath,f), os.path.join(imgPath,f) ] )


buildOptions = dict(
#                    packages = ["PySide"],
                    packages = [],
                    excludes = [],
#                    includes = ["PySide"],
                    includes = ['zmq.backend.cython'],
#                    includes = [],
                    optimize = 2,
                    compressed =  True,
                    icon = "img/logo.ico",
                    replace_paths = "*=",
                    #bundle_files = 1
                    include_files = includeFilesList,
                    silent = True,
                    )

base = 'Win32GUI' if sys.platform=='win32' else None


executables = [
    Executable(
               'main.py',
               base=base,
               targetName = 'mEDIsEliteTools.exe',
               compress=True,
               )
]

setup(name='mEDIs Elite Tools',
      version = "%s (%s)" % (__version__, __buildid__),
      author="René Wunderlich",
      description = 'Elite Tools',
      options = dict(build_exe = buildOptions),
      executables = executables)

# TODO: bad hoax https://github.com/pyinstaller/pyinstaller/issues/1404
if os.path.isfile(os.path.join(buildpath,"zmq.libzmq.pyd")):
    os.renames(os.path.join(buildpath,"zmq.libzmq.pyd"),os.path.join(buildpath,"libzmq.pyd"))

''' manipulate db clone '''
clonedDBpath = os.path.join(buildpath, "db/my.db" )

if os.path.isfile(clonedDBpath):
    db = elite.db(guiMode=True, DBPATH=clonedDBpath)

    db.setConfig('initRun', 1)
    
    lastOptimize = db.getConfig( 'lastOptimizeDatabase' )
    if lastOptimize:
        lastOptimize = datetime.strptime(lastOptimize , "%Y-%m-%d %H:%M:%S")
        if lastOptimize + timedelta(days=1) < datetime.now():
            db.optimizeDatabase()

    db.close()




outputfile = os.path.join("build", __ZIPFILE__)
zipexepath = r"c:\Program Files\7-Zip\7z.exe"

if os.path.isfile(outputfile):
    os.remove(outputfile)

#compress
options = "-y -t7z -mx9"
os.spawnl(os.P_WAIT, zipexepath,"7z","a",outputfile , "./build/exe.win32-3.4/*",  options)

