import logging
import logging.config
import datetime
import pathlib
import argparse
import sys
libPathList = ['./lib/']
for libPath in libPathList:
    sys.path.insert(0,libPath)
# import moduels from ./lib
from SetMeUp import SetMeUp
from RunWPS import RunWPS
from RunWRF import RunWRF
from checks import RunPreCheck
import accessories as acc
import pandas as pd 
from dateutil.relativedelta import relativedelta
import shutil
import os
import argparse
import time 


# 1) ------------- Configure the logger   ---------------------

# Get the working directory 
cwd = pathlib.Path(os.getcwd())

suffix = datetime.datetime.now().strftime("%m-%d_%H%M%S")
logfile= 'test.log' 
file_handler = logging.FileHandler(filename=logfile)
stdout_handler = logging.StreamHandler(sys.stdout)
logging.basicConfig(level=logging.INFO, 
		    format='%(asctime)s %(name)15s %(levelname)-8s %(message)s',
		    datefmt='%a, %d %b %Y %H:%M:%S',
		    handlers=[file_handler, stdout_handler]
		    )
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.info('Begin Main Program WRF Run')



main = pathlib.Path('user_config/main.yml')
setup = SetMeUp(main)
logger.info('Main run directory: {}'.format(setup.main_run_dirc))


# Perform some preliminary checks
checks = RunPreCheck(main)
passed = checks.run_all()
time.sleep(3)

# Run prelimnary checks. Fail if they do not pass 
if not passed:
    logger.error('Removing log file and exiting')
    os.remove(logfile)
    sys.exit()


#6) Create Run Directorys and start run
#--------------------------------------
#
setup.createRunDirectory()

# link the log file
#os.symlink(cwd.joinpath(logfile), setup.main_run_dirc.joinpath(logfile))

# Begin WPS
#wps = RunWPS(main)
#wps.geogrid()
wps.dataDownload()
wps.ungrib()
wps.metgrid()

## Begin WRF
wrf = RunWRF(main, wps=wps)
wrf.SetupRunFiles()
wrf.WRF_TimePeriod()

