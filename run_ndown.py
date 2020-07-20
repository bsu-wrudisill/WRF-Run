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
from checks import RunPreCheck
import accessories as acc
import pandas as pd
from dateutil.relativedelta import relativedelta
import shutil
import os

# Parse the input
parent_wrf_dirc = pathlib.Path("/home/wrudisill/scratch/spring_season_18/wrf")

# Perform some preliminary checks
main = pathlib.Path('user_config/main.yml')
setup = SetMeUp(main)


#!!! SEARCH FOR THE PARENT WRF FILES !!!

# Begin WPS
wps = RunWPS(main)

# LINK THESE THINGS IF THEY DO NOT ALREADY EXIST
#wps.geogrid()
#wps.dataDownload()
#wps.ungrib()
#wps.metgrid()


# Create some new directories ...

# Check that the wrfout files specified in the setup file
# match the outer grid dimensions in the namelist file...
ndown_dirc = wps.main_run_dirc.joinpath('ndown')
ndown_run_dirc_real = ndown_dirc.joinpath('wps')
ndown_run_dirc_wrf = ndown_dirc.joinpath('wrf')

# Make the directories...
#ndown_dirc.mkdir()
#ndown_run_dirc_wps.mkdir()
#ndown_run_dirc_wrf.mkdir()

# Link the wrf files to the wps directory...


# Link the parent wrf files to the ndown_wps_dirc

# # Begin WRF
#wrf = RunWRF(main, wps=wps)


#wrf.SetupRunFiles()
#wrf.WRF_TimePeriod()


#
## WRF should have completed
#success = wrf.CheckOut()
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
