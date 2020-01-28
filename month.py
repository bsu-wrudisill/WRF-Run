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

# basename 
basename = 'WY{}/Month{}'.format(str(wateryear), month_double_pad)
# Find the correct folder to run WRF in 
run_folder = pathlib.Path('/home/rudiwill/rudiwill/')
run_folder = run_folder.joinpath(basename)
run_folder.mkdir(exist_ok=True, parents=True)
run_restart = run_folder.joinpath('restart').mkdir(exist_ok=True)
run_wrfout = run_folder.joinpath('wrfout').mkdir(exist_ok=True)


# Create the directory to store the outputs in ...
final_output_path = pathlib.Path('/home/rudiwill/bsu_wrf/INL_SIMS')
final_output_folder = final_output_path.joinpath(basename)

final_output_folder = final_output_path.joinpath('wrfout').mkdir(exist_ok=True, parents=True)
final_restart_folder = pathlib.Path('/home/rudiwill/bsu_wrf/restarts')

# Create a directory for all of the wrfout and restart links

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
update = {'main_run_dirc':run_folder, 
          'restart':restart,
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
# update the setup files
setup._SetMeUp__update_yaml()

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

# WRF should have completed 
success = wrf.CheckOut()
if success:
    # create the storage space if it does not already exist 
    if month==9:
    # do not move any wrf files...
        logger.info('On Spinup month. NOT moving wrfout files.') 
    else:
        logger.info('Moving wrfoutput files to storage space...')
        for wrf_file in wrf.wrf_file_list:
            src = self.wrf_run_dir.joinpath(wrf_file)
            dst = final_output_folder
            shutil.move(src, dst)
            # now create links back to the originanl ...
            os.symlink(dst.joinpath(wrf_file), run_wrfout)
        for rst in self.final_rst_files:
            src = self.wrf_run_dir.joinpath(rst)
            dst = final_restart_folder 
            # move the restart 
            shutil.move(src, dst)
            # create a link for the 
            os.symlink(dst.joinpath(rst), run_restart)


