# run the data download process for WRF given the specified boundary conditions 
# and time/dates 

import pathlib as pl
import sys 
import datetime 
import pandas as pd
import urllib3
import accessories as acc
import threading 
import time 

# read the setup file ...
# -- data download directory
# -- start end date
# -- lbc type
# -- keep or delete (maybe)
# -- 

# temp 
start_date = datetime.datetime(2011,1,1)
end_date = datetime.datetime(2011,1,2)
date_range = pd.date_range(start_date, end_date, freq='5H')

#
lbc_type = 'cfsr'
out_dir = './'

# -------- GLOBALS -------
file_spec = '06.gdas'
nomads_url = "https://nomads.ncdc.noaa.gov/modeldata/cmd_{}/{}/{}{}/{}{}{}/"


# ---- Functions ---- 
def fetchFile(filename):
	acc.SystemCmd('wget {}'.format(filename))

def createDlist(date_range):
	#assert extension == 'pgbh' or extension == 'flxf', 'bad argument' 
	dlist = []
	for date in date_range:
		for extension in ['pgbh', 'flxf']:
			year = date.strftime('%Y')
			month = date.strftime('%m')
			day = date.strftime('%d')
			hour = date.strftime('%H')
			# get the pgbh files 
			base = nomads_url.format(extension, year, year, month, year, month,day)
			filename = base + '{}{}.{}{}{}{}.grb2'.format(extension,file_spec, year, month, day, hour)
			# create lists of each  
			dlist.append(filename)
	return dlist 		

def threadDownload():
	# uses the python 'threading' module to start multiple download processes at the same time
	# significantly speeds things up 
	urls = createDlist(date_range)
	threads = [threading.Thread(target=fetchFile, args=(url,)) for url in urls]
	for thread in threads:
		thread.start()
	for thread in threads:
		thread.join()

