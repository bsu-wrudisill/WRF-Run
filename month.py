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

# usage:       
# python <YYYY> <DD>               (defaults to existing=False)
# python <YYYY> <DD> --existing     (becomes to existing=True)
parser = argparse.ArgumentParser()
parser.add_argument("wateryear", type=int, help="WaterYear (YYYY)")
parser.add_argument("month", type=int, help="Requested month (MM)")
parser.add_argument("--overwrite", action="store_false", help="Overwrite exixting directory")   

args = parser.parse_args()
#print(args)
#print(args.wateryear)
#print(args.month)
#print(args.overwrite)

# ----------------- Run Configuration ---------------# 
# Parse dates 
if args.month in [9,10,11, 12]:
    year = args.wateryear - 1
else:
    year = args.wateryear

start_date = pd.to_datetime('{}-{}-01'.format(year,args.month))
end_date = start_date + relativedelta(months=1)
month_double_pad = start_date.strftime("%m")

# Logger stuff
suffix = datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")
logname = 'WY{}_MO{}_{}'.format(args.wateryear, args.month, suffix)
logging.config.fileConfig('./user_config/logger.ini', defaults={'LogName': logname})
logger = logging.getLogger(__name__)
logger.info('Starting...')

# basename 
basename = 'WY{}/Month{}'.format(args.wateryear, month_double_pad)
# Find the correct folder to run WRF in 
run_folder = pathlib.Path('/home/rudiwill/rudiwill/')
run_folder = run_folder.joinpath(basename)

# Create a directory for all of the wrfout and restart links

# If the month is greater than 9... then there should be a restart 
if args.month == 9:
    restart = False
    logger.info('Spinup period. No restart requestd')
else:
    restart = True
    logger.info('Restart required')

logger.info('Begin Main Program WRF Run')
logger.info('Water Year: {}'.format(args.wateryear))
logger.info('month: {}'.format(args.month))
logger.info('i.e. {}->{}'.format(start_date, end_date))


# This is a 'patch' dictionary that modifies the static .yaml file
# somwehat confusing... 
update = {'main_run_dirc':run_folder, 
          'restart':restart,
          'start_date': start_date,
          'end_date': end_date}


# ----------------- Being Main WPS/WRF Run ---------------# 
main = pathlib.Path('user_config/main.yml')
setup = SetMeUp(main, update=update) 
logger.info('main run directory: {}'.format(setup.main_run_dirc))


# Perform some preliminary checks
# WHAT DO WE DO WITH THE CHECKS?? RIGHT NOW THEY ARE NOT CAUGHT
checks = RunPreCheck(main, update=update) 
passed = checks.run_all()




# Create hte direcory.... duh 
setup.createRunDirectory()
# update the setup files
setup._SetMeUp__update_yaml()

# Begin WPS
wps = RunWPS(main, update=update) 
#wps.geogrid()
#wps.dataDownload()
#wps.ungrib()
#wps.metgrid()
#
## Begin WRF
wrf = RunWRF(main, wps=wps, update=update) 
wrf.SetupRunFiles()
#wrf.WRF_TimePeriod()
#
#
##--------------------- WRF Post Processing (move files, etc) -------------------------# 
## Verify the success of the WRF run
#success = wrf.CheckOut()
#
## Create the directory to store the outputs in ...
#final_output_path = pathlib.Path('/home/rudiwill/bsu_wrf/INL_SIMS')
#final_output_folder = final_output_path.joinpath(basename)
#
#final_output_folder = final_output_path.joinpath('wrfout').mkdir(exist_ok=True, parents=True)
#final_restart_folder = pathlib.Path('/home/rudiwill/bsu_wrf/restarts')
#
#if success:
#    # create the storage space if it does not already exist 
#    if month==9:
#    # do not move any wrf files...
#        logger.info('On Spinup month. NOT moving wrfout files.') 
#    else:
#        logger.info('Moving wrfoutput files to storage space...')
#        for wrf_file in wrf.wrf_file_list:
#            src = self.wrf_run_dir.joinpath(wrf_file)
#            dst = final_output_folder
#            shutil.move(src, dst)
#            # now create links back to the originanl ...
#            os.symlink(dst.joinpath(wrf_file), run_wrfout)
#        for rst in self.final_rst_files:
#            src = self.wrf_run_dir.joinpath(rst)
#            dst = final_restart_folder 
#            # move the restart 
#            shutil.move(src, dst)
#            # create a link for the 
#            os.symlink(dst.joinpath(rst), run_restart)
#
#
