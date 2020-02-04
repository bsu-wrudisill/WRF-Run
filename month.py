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



# Get the working directory 

cwd = pathlib.Path(os.getcwd())
# Configure the logger 
#suffix = datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")
#logname = 'WY{}_MO{}_{}'.format(args.wateryear, args.month, suffix)
#logging.config.fileConfig('./user_config/logger.ini', defaults={'LogName': logname})
#logger = logging.getLogger(__name__)
#logger.info('Starting...')



# 2) ------------- Configure the logger   ---------------------

suffix = datetime.datetime.now().strftime("%m-%d_%H%M%S")
logfile= '{}{}log_{}.log'.format(args.wateryear, month_double_pad, suffix)
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
logger.info('Water Year: {}'.format(args.wateryear))
logger.info('month: {}'.format(args.month))
logger.info('i.e. {}->{}'.format(start_date, end_date))

## unlink logfile to the parent directory....
#current_logfiles = path('./').glob('{}{}log_*'.format(args.wateryear, month_double_pad)) 
#if current_logfiles:
#    for cl in current_logfiles:
#        os.unlink(cl)
#
## create a link in the parent directory 
#os.symlink(logfile, '.')
#

# 3) -------------- Manage the Run Directory and Output Directories ----------# 

# Folder to create 
baseyear = "WY{}".format(args.wateryear)
basemonth= "Month{}".format(month_double_pad)

run_folder = pathlib.Path('/home/rudiwill/rudiwill/')
run_folder = run_folder.joinpath(baseyear, basemonth)

# Final output destinations  
# wrfouts 
final_output_path = pathlib.Path('/home/rudiwill/bsu_wrf/INL_SIMS')
final_output_folder = final_output_path.joinpath(basemonth, baseyear)
final_output_folder.mkdir(exist_ok=True, parents=True)
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

# remove any old logfiles for this month...
current_logfiles = list(pathlib.Path('./').glob('{}{}log_*'.format(args.wateryear, month_double_pad)))
#print(current_logfiles)
current_logfiles.remove(pathlib.Path(logfile))

if current_logfiles:
    for cl in current_logfiles: 
        # make sure we don't remove the current logfile...
        logger.info('removing previous logfiles...')
        os.remove(cl)


# 5) ----------------- Being Main WPS/WRF Run ---------------# 
main = pathlib.Path('user_config/main.yml')


# This is a 'patch' dictionary that modifies the static .yaml file
# somwehat confusing... 
update = {'main_run_dirc':run_folder, 
          'restart':restart,
          'start_date': start_date,
          'end_date': end_date}

setup = SetMeUp(main, update=update) 
logger.info('Main run directory: {}'.format(setup.main_run_dirc))


# Perform some preliminary checks
checks = RunPreCheck(main, update=update) 
passed = checks.run_all()
#time.sleep(3)

# Run prelimnary checks. Fail if they do not pass 
if not passed:
    logger.error('Removing log file and exiting')
    os.remove(logfile)
    sys.exit()


setup.createRunDirectory()
# update the setup files
setup._SetMeUp__update_yaml()
# link the log file
os.symlink(cwd.joinpath(logfile), setup.main_run_dirc.joinpath(logfile))

# Begin WPS
wps = RunWPS(main, update=update) 
wps.geogrid()
wps.dataDownload()
wps.ungrib()
wps.metgrid()

## Begin WRF
wrf = RunWRF(main, wps=wps, update=update) 
wrf.SetupRunFiles()
wrf.WRF_TimePeriod()


## Verify that hte WRF run completed, link files to folders w/in the directory 
success = wrf.CheckOut()


## 6) --------------------- WRF Post Processing (move files, etc) -------------------------# 
if success:
    # create the storage space if it does not already exist 
   if month==9:
    # do not move any wrf files...
        logger.info('On Spinup month. NOT moving wrfout files.') 
   else:
        logger.info('Moving wrfoutput files to storage space...')
        for wrf_file in wrf.wrf_file_list:
            src = wrf.wrf_run_dir.joinpath(wrf_file)
            dst = final_output_folder
            shutil.move(src, dst, follow_symlinks=True)
            # now create links back to the originanl ...
            os.symlink(dst.joinpath(wrf_file), run_wrfout)
        for rst in wrf.final_rst_files:
            src = wrf.wrf_run_dir.joinpath(rst)
            dst = final_restart_folder 
            # move the restart 
            shutil.move(src, dst, follow_symlinks=True)
            # create a link for the 
            os.symlink(dst.joinpath(rst), run_restart)


