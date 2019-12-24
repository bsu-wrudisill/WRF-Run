import sys 
import logging, logging.config
import datetime 
import sys 
import pathlib
import argparse 
libPathList = ['./lib/']
for libPath in libPathList:
		sys.path.insert(0,libPath)

# import moduels from ./lib
from SetMeUp import SetMeUp
from RunWPS import RunWPS
from RunWRF import RunWRF
from checks import RunPreCheck


#--- logger stuff ---- 	
suffix = datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")
logging.config.fileConfig('./user_config/logger.ini', defaults={'date':suffix})
logger = logging.getLogger(__name__)
logger.info('Starting...')


# Begin Setup
main = pathlib.Path('user_config/main.yml')
setup = SetMeUp(main)

# Perform some preliminary checks 
#checks = RunPreCheck(main)
#checks.run_all()
#setup.createRunDirectory()

# Begin WPS
wps = RunWPS(main)
#wps.geogrid()
#wps.dataDownload()
wps.ungrib()
wps.metgrid()

# Begin WRF
wrf = RunWRF(main, wps=wps)
wrf.SetupRunFiles()
wrf.WRF_TimePeriod()
