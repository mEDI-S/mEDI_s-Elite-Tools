# -*- coding: UTF8

'''
usage:
c:\Python34_32\python.exe setup.py build

http://cx-freeze.readthedocs.org/en/latest/distutils.html
'''
_buildZip = True

from cx_Freeze import setup, Executable
import os
import sys
import shutil
import subprocess
import elite
from datetime import datetime, timedelta
import platform
import time
import zmq.libzmq

__version__ = "0.1"
__buildid__ = ""
__builddate__ = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
__ZIPFILE__ = "mediselitetools.7z"
__sourceDB__ = "db/my.db"
__toolname__ = "mEDI's Elite Tools"
__toolnameSave__ = __toolname__.replace("'", "")
__exeName__ = 'mEDIsEliteTools.exe'
__destDisr__ = "dist"
__GUID__ = "{af43636e-d873-4f8d-b8d8-252a45e7cd91}"

__forceupdateFile__ = "updatetrigger.txt"
__OptimizeDB__ = False

VERSION_PY = """# This file is originally generated from Git information by running 'setup.py
__buildid__ = '%s'
__version__ = '%s'
__builddate__ = '%s'
__toolname__ = '%s'

import sys

__useragent__ = '%%s/%%s (%%s) %%s(%%s)' %% (__toolname__.replace(' ', ''), __version__, sys.platform, __buildid__, __builddate__.replace(' ', '').replace('-', '').replace(':', '') )

"""

VERSION_HOMEPAGE = """buildid=%s;version=%s;file=%s;builddate=%s"""


if sys.platform == 'win32':
    # platform.architecture()[0]
    base = 'Win32GUI'
    mybuild_dir = 'build\exe.win32-3.4'
else:
    base = None




if os.path.isdir(mybuild_dir):
    shutil.rmtree(mybuild_dir)
    pass


def isInt(s):
    try:
        int(s)
        return True
    except ValueError:
        return False


def update_version_py():
    global __buildid__, __version__
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

    ver = __buildid__.split("-")
    if isInt(ver[1]):
        __version__ = "%s.%s" % (ver[0], ver[1])
    else:
        __version__ = "%s.%s" % (ver[0], 0)
        
    f = open("_version.py", "w")
    f.write(VERSION_PY % (__buildid__, __version__, __builddate__, __toolnameSave__))
    f.close()
    print("_version.py to '%s'" % __buildid__)




update_version_py()


__msiFile__ = "%s-%s-%s.msi" % (__toolnameSave__, __version__, sys.platform)

''' create versions file '''
f = open(os.path.join(__destDisr__, "mediselitetools.version.txt"), "w")
f.write(VERSION_HOMEPAGE % (__buildid__, __version__, __msiFile__, __builddate__))
f.close()

''' add trigger file to force update on private databases '''
f = open(__forceupdateFile__, "w")
f.write("1")
f.close()


imgPath = "img"
# includeFilesList = [["db/my.db","db/my.db"],["db/rares.csv","db/rares.csv"]]
includeFilesList = [["db/rares.csv", "db/rares.csv"], [zmq.libzmq.__file__, "libzmq.pyd" ], [__forceupdateFile__, __forceupdateFile__]]

# add img
for f in os.listdir(imgPath):
    includeFilesList.append([os.path.join(imgPath, f), os.path.join(imgPath, f) ])


shortcut_table = [
                    (
                         "DesktopShortcut",  # Shortcut
                         "DesktopFolder",  # Directory_
                         __toolname__,  # Name
                         "TARGETDIR",  # Component_
                         "[TARGETDIR]%s" % __exeName__,  # Target
                         None,  # Arguments
                         None,  # Description
                         None,  # Hotkey
                         None,  # Icon
                         None,  # IconIndex
                         None,  # ShowCmd
                         "TARGETDIR",  # WkDir
                    ),
                    (
                         "Shortcut",  # Shortcut
                         "ProgramMenuFolder",  # Directory_
                         __toolname__,  # Name
                         "TARGETDIR",  # Component_
                         "[TARGETDIR]%s" % __exeName__,  # Target
                         None,  # Arguments
                         None,  # Description
                         None,  # Hotkey
                         None,  # Icon
                         None,  # IconIndex
                         None,  # ShowCmd
                         "TARGETDIR",  # WkDir
                    ),
                  ]

msi_data = {"Shortcut": shortcut_table}

msiOptions = dict(
                   upgrade_code=__GUID__,
                   data=msi_data,
                 )

buildOptions = dict(
                        # build_exe = mybuild_dir,
                        packages=[],
                        excludes=[],
    
                        includes=['zmq.backend.cython'],
                        optimize=2,
                        compressed=True,
                        icon="img/logo.ico",
                        replace_paths="*=",
                        include_files=includeFilesList,
                        silent=True,
                    )

installOptions = dict(
                        force=True,
                        skip_build=False,
                    )



executables = [
    Executable(
               'main.py',
               base=base,
               targetName=__exeName__,
               compress=True,
               shortcutName=__toolname__,
               shortcutDir=None,
            )
]


setup(name=__toolnameSave__,
      version=__version__,
      author="René Wunderlich",
      description='Elite Tools',
      options=dict(
                    build_exe=buildOptions,
                    # install_exe = installOptions,
                    bdist_msi=msiOptions,
                ),
      executables=executables)


''' remove trigger file '''
if os.path.isfile(__forceupdateFile__):
    os.remove(__forceupdateFile__)

''' only for the zip fallback'''
if _buildZip:

    ''' manipulate db clone '''
    clonedDBpath = os.path.join(mybuild_dir, __sourceDB__)
    
    shutil.copyfile(__sourceDB__, clonedDBpath)
    
    
    if os.path.isfile(clonedDBpath):
        db = elite.db(guiMode=True, DBPATH=clonedDBpath)
        cur = db.cursor()
        db.setConfig('initRun', 1)
    
        db.setConfig('option_dft_fromSystem', '')
        db.setConfig('option_dft_fromStation', '')
        db.setConfig('option_dft_toSystem', '')
        db.setConfig('option_dft_toStation', '')
    
        db.setConfig('option_pcf_power', '')
        db.setConfig('option_pcf_location', '')

        db.setConfig('option_commanderName', '')

        db.setConfig('mainwindow.geometry', '')
        db.setConfig('mainwindow.State', '')
        db.setConfig('mainwindow.openWidgets', '')


        ''' drop private tables '''
        cur.execute("DROP TABLE flylog")

        db.con.commit()
        cur.close()

        lastOptimize = db.getConfig('lastOptimizeDatabase')
        if __OptimizeDB__ and lastOptimize:
            lastOptimize = datetime.strptime(lastOptimize, "%Y-%m-%d %H:%M:%S")
            if lastOptimize + timedelta(days=1) < datetime.now():
                db.optimizeDatabase()
    
        db.close()
    
    
    
    
    outputfile = os.path.join(__destDisr__, __ZIPFILE__)
    zipexepath = r"c:\Program Files\7-Zip\7z.exe"
    
    if os.path.isfile(outputfile):
        os.remove(outputfile)

    # compress
    options = "-y -t7z -mx9"
    os.spawnl(os.P_WAIT, zipexepath, "7z", "a", outputfile, "./%s/*" % mybuild_dir, options)
