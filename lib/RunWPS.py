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
import glob 


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
	
	def ungrib(self):
		logger = logging.getLogger(__name__)
		logger.info('starting ungrib')
		cwd = os.getcwd() 
		# link the vtable
		#os.symlink(self.ungrib_run_dirc.joinpath('Variable_Tables/Vtable.CFSR'), self.ungrib_run_dirc.joinpath('Vtable'))
		linkGrib = '{}/link_grib.csh {}/{}'
		catch_id = 'ungrib.catch'
		submit_script = self.ungrib_run_dirc.joinpath('submit_ungrib.sh')
		namelist_wps = self.ungrib_run_dirc.joinpath('namelist.wps')        
		# replace namelist items 
		submit_replace_dic = {"LOGNAME":"ungrib",
			     	      "TASKS":1,
				      "NODES":1,
				      "QUEUE":"leaf",
				      "RUN_TIME":"01:00:00",
				      "ENVIRONMENT_FILE": self.environment_file,
				      "CATCHID":catch_id,
				      "EXECUTABLE":"ungrib.exe"
					}
		
		wps_replace_dic = {"GEOG_PATH":self.geog_data_path,
      			           "GEOG_TBL_PATH":self.geo_exe_dirc,
			           "METGRID_TBL_PATH":self.met_exe_dirc,
			           "ungribprefix":'PLEVS',	
			           "startdate":self.start_date.strftime(self.time_format),
			           "enddate":self.end_date.strftime(self.time_format),
			           }
		
		# MOVE THE TO THE UNGRIB DIRECTORY
		os.chdir(self.ungrib_run_dirc)
		
		# ---- UNGRIB PRESSURE FILES 
		logger.info('starting on PLEVS')
		acc.GenericWrite(self.main_run_dirc.joinpath('namelist.wps.template'), wps_replace_dic, namelist_wps)
		acc.SystemCmd(linkGrib.format(self.ungrib_run_dirc, self.data_dl_dirc, 'pgbh06'))
		acc.GenericWrite(self.submit_template, submit_replace_dic, submit_script) 
		
		# submit the ungrib job 
		jobid, error = acc.Submit(submit_script,catch_id)	
		acc.WaitForJob(jobid, 'wrudisill')
		ungrib_log_message = acc.tail(1, self.ungrib_run_dirc.joinpath('ungrib.log'))
		logger.into(ungrib_log_message)
		# remove the previous grib files 
		globfiles = self.ungrib_run_dirc.glob('GRIBFILE*')
		for globfile in globfiles:
			logger.debug('unlinked {}'.format(str(globfile)))
			os.unlink(globfile)
		
		# ---- UNGRIB SFLUX FILES 	
		logger.info('starting on SFLUX')
		wps_replace_dic['ungribprefix'] = 'SFLUX'
		submit_replace_dic['logname'] = "ungrib_flx"
		
		acc.GenericWrite(self.main_run_dirc.joinpath('namelist.wps.template'), wps_replace_dic, namelist_wps)
		acc.SystemCmd(linkGrib.format(self.ungrib_run_dirc, self.data_dl_dirc, 'flxf06'))
			
		jobid, error = acc.Submit(submit_script,catch_id)	
		acc.WaitForJob(jobid, 'wrudisill')
		
		# unlink 
		globfiles = self.ungrib_run_dirc.glob('GRIBFILE*')
		for globfile in globfiles:
			logger.debug('unlinked {}'.format(str(globfile)))
			os.unlink(globfile)
		# run the link csh script 
		# check that the script finished correctly
		os.chdir(cwd)


	def dataDownload(self):
		#start_date = datetime.datetime(2011,1,1)
		#end_date = datetime.datetime(2011,1,4)
		date_range = pd.date_range(self.start_date, self.end_date, freq='6H')
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


