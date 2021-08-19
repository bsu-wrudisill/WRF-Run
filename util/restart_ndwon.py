import logging
import logging.config
import datetime
import pathlib
import argparse
import sys
libPathList = ['/home/rudiwill/WRF-Run/lib/']
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

# Parse the input 
suffix = datetime.datetime.now().strftime("%m-%d_%H%M%S")
logfile= 'restart_{}.log'.format(suffix)
file_handler = logging.FileHandler(filename=logfile)
stdout_handler = logging.StreamHandler(sys.stdout)
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s %(name)15s %(levelname)-8s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S',
                    handlers=[file_handler, stdout_handler]
                    )


update = {'restart':True}

# Perform some preliminary checks
main = pathlib.Path('user_config/main.yml')
setup = SetMeUp(main, update=update)

# Begin WPS
wps = RunWPS(main, update)
#wps.metgrid()

# Begin WRF
wrf = RunWRF(main, wps=wps)
#wrf.SetupRunFiles()

# look for WRF restart files in the directory ...
found_rst = list(wrf.wrf_run_dirc.glob('wrfrst*'))
found_hydro_rst = list(wrf.wrf_run_dirc.glob('HYDRO_RST*'))

last_restart = found_rst[-1]
last_hydro_restart = found_hydro_rst[-1]
timelist = []

# Get the timesamp from the last restart file
for rstp in found_rst:
    rst = rstp.name
    timelist.append(pd.to_datetime(rst[11:], format=setup.time_format))


logging.info('\n\n\n------------- Restart Run Called. Finding latest restart point -------------------\n\n\n')

# get the latest wrf restart 
last_restart = max(timelist)
logging.info('last restart point: {}'.format(last_restart))

ndown = RunNDown(main)
ndown.start()
ndown.use_hydro()

#ndown.createRunDirectory()
#ndown.geogrid()
#ndown.metgrid()
#ndown.WRF_Ndown_TimePeriod(skip_first_real_ndown=True)


ndown.start_date_string = last_restart
print(ndown.start_date)


#ndown.WRF_Ndown_TimePeriod()

#logging.info('-------------- Complete -----------------------')
#logging.info('Moving files...')

# since this is a restart... go back to the orig start/end times 

#wrfdst = pathlib.Path("/home/rudiwill/bsu_wrf/INL_SIMS").joinpath('WY2012','Month03')

#wps = RunWPS(main)
#wrf = RunWRF(main, wps=wps)
#wrf.CheckOut(wrfdst=wrfdst)

