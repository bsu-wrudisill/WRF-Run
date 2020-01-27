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


# Parse the input 
wateryear = int(sys.argv[1])  # WATER YEAR.... not year 
month = int(sys.argv[2])


# Parse dates 
if month in [9,10,11, 12]:
    year = wateryear - 1
else:
    print(month)
    print(type(month))
    year = wateryear

start_date = pd.to_datetime('{}-{}-01'.format(year,month))
end_date = start_date + relativedelta(months=1)
month_double_pad = start_date.strftime("%m")

# Logger stuff
suffix = datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")
logname = 'WY{}_MO{}_{}'.format(wateryear, month, suffix)
logging.config.fileConfig('./user_config/logger.ini', defaults={'LogName': logname})
logger = logging.getLogger(__name__)
logger.info('Starting...')

# Find the correct folder to run WRF in 
folder = pathlib.Path('/home/rudiwill/rudiwill/').joinpath('WY'+str(wateryear)).joinpath('Month'+month_double_pad)

# If the month is greater than 9... then there should be a restart 
if month == 9:
    restart = False
    logger.info('Starting Month. No Restart requestd')
else:
    restart = True
    logger.info('Starting Month. Restart requestd')

logger.info('Begin Main Program WRF Run')
logger.info('Water Year: {}'.format(wateryear))
logger.info('month: {}'.format(month))
logger.info('i.e. {}->{}'.format(start_date, end_date))


# Begin the WRF setup
update = {'main_run_dirc':folder, 
          'restart':False,
          'start_date': start_date,
          'end_date': end_date}


main = pathlib.Path('user_config/main.yml')
setup = SetMeUp(main, update=update) 
logger.info('main run directory: {}'.format(setup.main_run_dirc))


# Perform some preliminary checks
checks = RunPreCheck(main, update=update) 
checks.run_all()

# Create hte direcory.... duh 
setup.createRunDirectory()

# Begin WPS
wps = RunWPS(main, update=update) 
wps.geogrid()
wps.dataDownload()
wps.ungrib()
wps.metgrid()

# Begin WRF
wrf = RunWRF(main, wps=wps, update=update) 
wrf.SetupRunFiles()
wrf.WRF_TimePeriod()
