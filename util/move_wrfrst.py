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



# usage:       
# python <YYYY> <DD>               (defaults to existing=False)
# python <YYYY> <DD> --existing     (becomes to existing=True)


# 1) ------------------ Parse the Command Line Inputs------------# 
 
parser = argparse.ArgumentParser()
parser.add_argument("wateryear", type=int, help="WaterYear (YYYY)")
parser.add_argument("month", type=int, help="Requested month (MM)")
parser.add_argument("--overwrite", action="store_true", help="Overwrite exixting directory")   
parser.add_argument("--start_date", default=None)
parser.add_argument("--end_date", default=None)
parser.add_argument("--lbc", default=None)

#parser.add_argument("-ed", action='store_const') 
 
args = parser.parse_args()


# 2) ----------------- Run Configuration ---------------# 

if args.month in [9,10,11, 12]:
    year = args.wateryear - 1
else:
    year = args.wateryear

# read dates ...
if args.start_date:
    start_date = pd.to_datetime(args.start_date)
else:
    start_date = pd.to_datetime('{}-{}-01'.format(year,args.month))

if args.end_date:
    end_date = pd.to_datetime(args.end_date)
else:
    end_date = start_date + relativedelta(months=1)

month_double_pad = start_date.strftime("%m")

# figure out the lbc type
if year >= 2011:
    lbc = 'cfsrv2'
if year < 2011:
    lbc = 'cfsr'


# 2) ------------- Configure the logger   ---------------------

# Get the working directory 
cwd = pathlib.Path(os.getcwd())

suffix = datetime.datetime.now().strftime("%m-%d_%H%M%S")
logfile= '{}{}log_{}.log'.format(args.wateryear, month_double_pad, suffix)
stdout_handler = logging.StreamHandler(sys.stdout)
logging.basicConfig(level=logging.INFO, 
		    format='%(asctime)s %(name)15s %(levelname)-8s %(message)s',
		    datefmt='%a, %d %b %Y %H:%M:%S',
		    handlers=[stdout_handler]
		    )
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.info('Begin Main Program WRF Run')
logger.info('Water Year: {}'.format(args.wateryear))
logger.info('month: {}'.format(args.month))
logger.info('i.e. {}->{}'.format(start_date, end_date))

## create a link in the parent directory 
#
logger.info('LBC type: {}'.format(lbc))

# 3) -------------- Manage the Run Directory and Output Directories ----------# 

# Folder to create 
baseyear = "WY{}".format(args.wateryear)
basemonth= "Month{}".format(month_double_pad)

run_folder = pathlib.Path('/home/rudiwill/rudiwill/')
run_folder = run_folder.joinpath(baseyear, basemonth)

# restarts 
final_restart_folder = pathlib.Path('/home/rudiwill/bsu_wrf/restarts')

# If the month is greater than 9... then there should be a restart 
if args.month == 9:
    restart = False
    logger.info('Spinup period. No restart requestd')
else:
    restart = True
    logger.info('Restart required')

# If there is an existing directory, delete it.
if args.overwrite == True:
    if run_folder.exists():
        logger.info('!!!Found existing run directory. Overwriting!!!') 
        shutil.rmtree(run_folder)        



# 5) ----------------- Being Main WPS/WRF Run ---------------# 
main = pathlib.Path('user_config/main.yml')


# This is a 'patch' dictionary that modifies the static .yaml file
# somwehat confusing... 
update = {'main_run_dirc':run_folder, 
          'start_date': start_date,
          'end_date': end_date,
          'lbc_type': lbc
}
print(update)
setup = SetMeUp(main, update=update) 

wps = RunWPS(main, update=update) 
wrf = RunWRF(main, wps=wps, update=update) 

wrf.required_files()
rest_found, rest_message = acc.file_check(wrf.rst_files, wrf.wrf_run_dirc)

if not rest_found:
    for rst in wrf.rst_files:    
        logger.info('Copying the following restart files...')
        logger.info(rst)    
        logger.info('{} --> {}'.format(wrf.restart_directory, wrf.wrf_run_dirc))
        shutil.copy(wrf.restart_directory.joinpath(rst), wrf.wrf_run_dirc)




