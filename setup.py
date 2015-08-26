from cx_Freeze import setup, Executable
import os
import sys
import shutil
import subprocess
import elite

__version__ = "0.1"
__buildid__ = ""

'''
usage:
c:\Python34_32\python.exe setup.py build

http://cx-freeze.readthedocs.org/en/latest/distutils.html
'''

VERSION_PY = """
# This file is originally generated from Git information by running 'setup.py
__buildid__ = '%s'
__version__ = '%s'
"""



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
    f.write(VERSION_PY % (__buildid__, __version__))
    f.close()
    print("_version.py to '%s'" % __buildid__)

update_version_py()

# Dependencies are automatically detected, but it might need
# fine tuning.
buildOptions = dict(
#                    packages = ["PySide"],
                    packages = [],
                    excludes = [],
#                    includes = ["PySide"],
                    includes = [],
                    optimize = 2,
                    compressed =  True,
                    replace_paths = "*=",
                    #bundle_files = 1
                    include_files = [["db/my.db","db/my.db"],["db/rares.csv","db/rares.csv"]],
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


''' manipulate db clone '''
clonedDBpath = os.path.join(buildpath, "db/my.db" )

if os.path.isfile(clonedDBpath):
    db = elite.db(guiMode=True, DBPATH=clonedDBpath)

    db.setConfig('initRun', 1)

    db.close()





outputfile = "build/mediselitetools.7z"
zipexepath = r"c:\Program Files\7-Zip\7z.exe"

if os.path.isfile(outputfile):
    os.remove(outputfile)

#compress
options = "-y -t7z -mx9"
os.spawnl(os.P_WAIT, zipexepath,"7z","a",outputfile , "./build/exe.win32-3.4/*",  options)
