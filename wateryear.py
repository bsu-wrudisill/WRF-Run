'''
Run script for an entire water year
Oct 01 --> Sept 30

Everything gets run in the same run directory
'''
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


parser = argparse.ArgumentParser()
parser.add_argument("water_year", type=int, help="WaterYear (YYYY)")
parser.add_argument("spinup", type=int, help="length of time for spinup (days)")
parser.add_argument("--existing", action="store_true", help="Master directory already exists")   

# usage:       
# python <YYYY> <DD>               (defaults to existing=False)
# python <YYYY> <DD> --existing     (becomes to existing=True)
args = parser.parse_args()


# Begin
# -----
# Read in the config file 
main = pathlib.Path('user_config/main.yml')
setup = SetMeUp(main)

# create a date range for the water year 
start = datetime.datetime(args.water_year, 10, 1, 0) - datetime.timedelta(days=args.spinup)
end =  datetime.datetime(args.water_year+1, 9, 30, 0)

# setup.start_date = start.strftime('%Y-%m-%d')
# setup.end_date = end.strftime('%Y-%m-%d')
# setup.restart = False  # if we are starting at the very beginning of the water year.. there is no restart file   




# over write the default start date 
#setup.start_date = 
#setup.end_date = 
