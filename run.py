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
from RunNDown import RunNDown


# from checks import RunPreCheck
# import acc,essories as acc
# import pandas as pd
# from dateutil.relativedelta import relativedelta
# import shutil
import os
# import time


# 1) ------------- Configure the logger   ---------------------

# Get the working directory
cwd = pathlib.Path(os.getcwd())

# suffix = datetime.datetime.now().strftime("%m-%d_%H%M%S")
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

ndown = RunNDown(main)
ndown.start()
ndown.use_hydro()
#ndown.createRunDirectory()
#ndown.geogrid()

print(ndown.num_wrf_dom)
ndown.metgrid()
ndown.WRF_Ndown_TimePeriod()

# Create Run Directorys and start run
#--------------------------------------
#
# setup.createRunDirectory()

# # link the log file
# os.symlink(cwd.joinpath(logfile), setup.main_run_dirc.joinpath(logfile))

# # Begin WPS
#wps = RunWPS(main)

# wps.dataDownload()
# wps.geogrid()
# wps.ungrib()
# wps.metgrid()

# ## Begin WRF
#wrf = RunWRF(main)


# wrf.SetupRunFiles()
# wrf.WRF_TimePeriod()






