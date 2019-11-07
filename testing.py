import sys
import shutil
import os 
import time 
import sys 
import datetime 
import logging
import yaml 

libPathList = ['./lib'] 
for libPath in libPathList:
	sys.path.insert(0,libPath)


# setup the log file --- this will get passed to all of the imported modules!!!
suffix = datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")
logfile= 'WRF_logfile_{}.log'.format(suffix)
file_handler = logging.FileHandler(filename=logfile)
stdout_handler = logging.StreamHandler(sys.stdout)
logging.basicConfig(level=logging.INFO, format = '%(asctime)s %(name)15s %(levelname)-8s %(message)s',datefmt='%a, %d %b %Y %H:%M:%S',handlers=[file_handler, stdout_handler])
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

setupfile = 'setup.yaml'
logger.info('starting {}. reading {} setup'.format(__name__, setupfile))
