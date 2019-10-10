import sys
import shutil
import os 
import time 
import sys 
import datetime 
import logging
import yaml 
import pathlib as pl
import pandas as pd 
import accessories as acc 
from SetMeUp import SetMeUp
from check_completion import geogrid_ver
from functools import partial 

class RunWPS(SetMeUp):
	#
	def __init__(self, setup):
		super(self.__class__, self).__init__(setup)	
	
			
	@acc.timer	
	def geogrid(self):
		# mpicommand
		catch_id = 'geogrid.catch'
		replacedata = {"LOGNAME":"geogrid",
				"TASKS":2,
				"NODES":1,
				"QUEUE":"leaf",
				"RUN_TIME":"01:00:00",
				"ENVIRONMENT_FILE": self.environment_file,
				"CATCHID":catch_id,
				"EXECUTABLE":"geogrid.exe"
				}
		
		# copy/update the SLURM submit template ---> ~/geo/. directory  
		submit_script = self.geo_run_dirc.joinpath('submit_geogrid.sh')
		acc.GenericWrite(self.submit_template, replacedata, submit_script) 
		# this seems to be easier to submit jobs this way ... 
		cwd = os.getcwd()
		os.chdir(self.geo_run_dirc)
		# now run geogrid 
		jobid, error = acc.Submit(submit_script,catch_id)	
		# wait for the job to complete 
		acc.WaitForJob(jobid, 'wrudisill')
		os.chdir(cwd)
	
	def dataDownload(self):
		start_date = datetime.datetime(2011,1,1)
		end_date = datetime.datetime(2011,1,4)
		date_range = pd.date_range(start_date, end_date, freq='6H')
		self.file_spec = '06.gdas'
		#### 
		if self.lbc_type == 'cfsr': 
			nomads_url = "https://nomads.ncdc.noaa.gov/modeldata/cmd_{}/{}/{}{}/{}{}{}/"
		
		else:
			sys.exit()  # FOR NOW 
		# ---- Functions ---- 
		def createDlist(date_range):
			#assert extension == 'pgbh' or extension == 'flxf', 'bad argument' 
			dlist = []
			filelist = []
			for date in date_range:
				for extension in ['pgbh', 'flxf']:
					year = date.strftime('%Y')
					month = date.strftime('%m')
					day = date.strftime('%d')
					hour = date.strftime('%H')
					# get the pgbh files 
					base = nomads_url.format(extension, year, year, month, year, month,day)
					filename = '{}{}.{}{}{}{}.grb2'.format(extension,self.file_spec, year, month, day, hour)					
					filepath = base + filename
					# create lists of each  
					dlist.append(filepath)
					filelist.append(filename)
			return dlist,filelist
		# fix the data destination argument 
		cwd = os.getcwd()	
		os.chdir(self.data_dl_dirc)
		# create url list 
		urls,filenames= createDlist(date_range)
		#acc.multi_thread(acc.fetchFile, urls) # BROKEN --- misses downloading some files 
		for url in urls:
			acc.fetchFile(url)
		os.chdir(cwd)	
		
		required_files = len(date_range)
		missing_files = 0 
		for f in filenames:
			if self.data_dl_dirc.joinpath(f).exists():
				pass
			else:
				print(self.data_dl_dirc.joinpath(f))
				missing_files += 1 
		print("{} missing files".format(missing_files))
		# check that the files are in fact there 
		

if __name__ == '__main__':
	pass 


