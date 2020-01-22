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
from dateutil.relativedelta import relativedelta
import pandas as pd 

month = sys.argv[1]
wateryear = sys.argv[2]   # WATER YEAR.... not year 

if month in [9,10,11, 12]:
    year = wateryear - 1 
else:
    year = wateryear

# parse dates 
start_date = pd.to_datetime('{}-{}-01'.format(year,month))
end_date = start_date + relativedelta(months=1)


# logger stuff
suffix = datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")
logging.config.fileConfig('./user_config/logger.ini', defaults={'date': suffix})
logger = logging.getLogger(__name__)
logger.info('Starting...')

# Begin Setup
main = pathlib.Path('user_config/main.yml')
setup = SetMeUp(main)

# modify stuff here
logger.info('updating start/end dates....') 
setup.start_date = start_date 
setup.end_date = end_date

# new run loc 
run_loc_append = setup.main_run_dirc.joinpath('WaterYear_{}'.format(wateryear))
run_loc_append = run_loc_append.joinpath('Month_{}'.format(month))
setup.main_run_dirc = run_loc_append

setup.final_init()
print(setup.wrf_run_dirc)


# Perform some preliminary checks
checks = RunPreCheck(main)
checks.run_all()
setup.createRunDirectory()

# Begin WPS
#wps = RunWPS(main)
#wps.geogrid()
#wps.dataDownload()
#wps.ungrib()
#wps.metgrid()

# Begin WRF
#wrf = RunWRF(main, wps=wps)
#wrf.SetupRunFiles()
#wrf.WRF_TimePeriod()
