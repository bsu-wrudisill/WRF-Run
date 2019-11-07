# run the data download process for WRF given the specified boundary conditions 
# and time/dates 

import pathlib as pl
import sys 
import datetime 
import pandas as pd
import urllib3
import accessories as acc

import time 

# read the setup file ...
# -- data download directory
# -- start end date
# -- lbc type
# -- keep or delete (maybe)
# -- 

# temp 
start_date = datetime.datetime(2017,1,1)
end_date = datetime.datetime(2017,1,4)
date_range = pd.date_range(start_date, end_date, freq='6H')

#
lbc_type = 'cfsr'
out_dir = './'

# -------- GLOBALS -------
file_spec = '06.gdas'
#nomads_url = "https://nomads.ncdc.noaa.gov/modeldata/cmd_{}/{}/{}{}/{}{}{}/"
nomads_url = "https://nomads.ncdc.noaa.gov/modeldata/cfsv2_analysis_pgbh/{}/{}{}/{}{}{}/"


#https://nomads.ncdc.noaa.gov/modeldata/cfsv2_analysis_pgbh/2012/201203/20120303/cdas1.t00z.pgrbh00.grib2
# ---- Functions ---- 

def createDlistCFSV2(date_range):
	#assert extension == 'pgbh' or extension == 'flxf', 'bad argument' 
	dlist = []
	for date in date_range:
		year = date.strftime('%Y')
		month = date.strftime('%m')
		day = date.strftime('%d')
		hour = date.strftime('%H')
		# get the pgbh files 
		base = nomads_url.format(year, month, year, month,day)
		filename = base + "cdas1.t{}z.pgrbh00.grib2".format(hour)
		# create lists of each  
		dlist.append(filename)
	return dlist 		

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

urls = createDlist(date_range)
acc.multi_thread(fetchFile, urls)
