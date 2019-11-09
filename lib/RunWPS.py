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
from check_completion import StatusChecker as SC 
from functools import partial 
import glob 
import secrets

class RunWPS(SetMeUp):
	#
	def __init__(self, setup):
		super(self.__class__, self).__init__(setup)	
		self.logger = logging.getLogger(__name__)
		self.logger.info('initialized RunWPS instance')	
	
	@acc.timer	
	def geogrid(self):
		# ---- gather information about the job -----# 
		self.logger.info('starting geogrid')	
		catch_id = 'geogrid.catch'
		unique_name = "g_{}".format(secrets.token_hex(2))
		
		# ---- create the run script based on the type of job scheduler system ----# 
		if self.scheduler == 'PBS':
			replacedata = {"LOGNAME":"geogrid",
					"QUEUE":self.queue,
					"RUN_TIME":self.geogrid_wall_time,
				        "NODES":self.num_wps_nodes,
				        "NCPUS":self.num_wps_cpus,
				        "MPIPROCS":self.num_wps_mpiprocs,
				        "CPUTYPE":self.wps_cpu_type,
					"ENVIRONMENT_FILE": self.environment_file,
					"RUN_DIR":self.geo_run_dirc,
					"JOBNAME": unique_name, 
					"CMD":"geogrid.exe &> geogrid.catch",
					}
		
		if self.scheduler == 'SLURM':
			replacedata = {"LOGNAME":"geogrid",
					"QUEUE":self.queue,
					"RUN_TIME":"00:30:00",
					"ENVIRONMENT_FILE": self.environment_file,
					"RUN_DIR":self.geo_run_dirc,
					"JOBNAME": unique_name,			
					"CMD":"geogrid.exe &> geogrid.catch",
					}
			
		# --- copy over the submit script information and submit the job-----# 
		# copy/update the SLURM submit template ---> ~/geo/. directory  
		submit_script = self.geo_run_dirc.joinpath('submit_geogrid.sh')
		acc.GenericWrite(self.submit_template, replacedata, submit_script) 
		#
		## this seems to be easier to submit jobs this way ... 
		cwd = os.getcwd()
		os.chdir(self.geo_run_dirc)
		## now run geogrid 
		jobid, error = acc.Submit(submit_script, self.scheduler)	
		## wait for the job to complete 
		acc.WaitForJob(jobid, self.user, self.scheduler)  #CHANGE_ME 
		os.chdir(cwd)
		
		# !!! check stuff !!!!
		# ! check that the geogrid.log file says "success"
		success, status = SC.test_geolog(self.geo_run_dirc)
		if not success:
			self.logger.error(status)
		else:
			self.logger.info(status)
		#! check that the geo_em? files get created 
		success, status = SC.test_geofiles(self.geo_run_dirc)
		if not success:
			self.logger.error(status)
		else:
			self.logger.info(status)


		
		
	@acc.timer	
	def ungrib(self):
		logger = logging.getLogger(__name__)
		logger.info('starting ungrib')
		cwd = os.getcwd() 
		# fixed paths -- these should get created 
		vtable = self.ungrib_run_dirc.joinpath('Vtable')
		submit_script = self.ungrib_run_dirc.joinpath('submit_ungrib.sh')
		namelist_wps = self.ungrib_run_dirc.joinpath('namelist.wps')        
		ungrib_log = self.ungrib_run_dirc.joinpath('ungrib.log')
		linkGrib = '{}/link_grib.csh {}/{}'
		catch_id = 'ungrib.catch'
		unique_name = 'u_{}'.format(secrets.token_hex(2))
		success_message = 'Successful completion of program ungrib.exe'
		# replace namelist items 
		if self.scheduler == 'SLURM':
			# dictionary 
			submit_replace_dic = {"LOGNAME":"ungrib",
					      "TASKS":1,
					      "NODES":1,
					      "QUEUE":self.queue,
					      "RUN_TIME":"01:00:00",
					      "ENVIRONMENT_FILE": self.environment_file,
					      "CATCHID":catch_id,
					      "EXECUTABLE":"ungrib.exe"
						}
		if self.scheduler == 'PBS':
			# dictionary 
			submit_replace_dic = {"LOGNAME":"ubgrib",
					      "QUEUE":self.queue,
					      "RUN_TIME":self.wps_params['ungrib_run_time'],
					      "NODES":self.wps_params['num_nodes'],
					      "NCPUS":self.wps_params['num_cpus'],
					      "MPIPROCS":self.wps_params['num_mpiprocs'],
					      "CPUTYPE":self.cpu_type,
					      "ADDITIONAL_OPTIONS": '',    #!!!! Any additional PBS opitions can be insterted here !!!#
					      "ENVIRONMENT_FILE": self.environment_file,
					      "RUN_DIR":self.ungrib_run_dirc,
					      "JOBNAME": unique_name, 
					      "CMD":"ungrib.exe &> ungrib.catch"
						}
		
#PBS -l select=1:ncpus=36:mpiprocs=0:cputype=broadwell
		wps_replace_dic = {"GEOG_PATH":self.geog_data_path,
      			           "GEOG_TBL_PATH":self.geo_exe_dirc,
			           "METGRID_TBL_PATH":self.met_exe_dirc,
			           "ungribprefix":'PLEVS',	
			           "startdate":self.start_date.strftime(self.time_format),
			           "enddate":self.end_date.strftime(self.time_format),
			           }
		
		# MOVE THE TO THE UNGRIB DIRECTORY
		if not vtable.exists():
			os.symlink(self.ungrib_run_dirc.joinpath('Variable_Tables/Vtable.CFSR'), vtable) 
			
		os.chdir(self.ungrib_run_dirc)
		
		# ---- UNGRIB PRESSURE FILES 
		logger.info('starting on PLEVS')
		acc.GenericWrite(self.main_run_dirc.joinpath('namelist.wps.template'), wps_replace_dic, namelist_wps)
		acc.GenericWrite(self.submit_template, submit_replace_dic, submit_script) 
		acc.SystemCmd(linkGrib.format(self.ungrib_run_dirc, self.data_dl_dirc, 'pgbh06'))	
		## pressure files job submission	
		jobid, error = acc.Submit(submit_script,self.scheduler)	
		acc.WaitForJob(jobid, self.user, self.scheduler)
		
		## verify completion 
		#success, status = log_check(ungrib_log, success_message)
		#if success: logger.info(acc.tail(1,ungrib_log))
		#if not success: 
		#	logger.error(acc.tail(1, ungrib_log))
		#	logger.info("fatal error encountered. exiting")
		#	sys.exit()
		

		# clean up 
		globfiles = self.ungrib_run_dirc.glob('GRIBFILE*')
		for globfile in globfiles:
			logger.debug('unlinked {}'.format(str(globfile)))
			os.unlink(globfile)
		
		## ---- UNGRIB SFLUX FILES 	
		## upate dictionaries
		logger.info('starting on SFLUX')
		wps_replace_dic['ungribprefix'] = 'SFLUX'
		submit_replace_dic['logname'] = "ungrib_flx"
		acc.GenericWrite(self.main_run_dirc.joinpath('namelist.wps.template'), wps_replace_dic, namelist_wps)
		## link flxf files 
		acc.SystemCmd(linkGrib.format(self.ungrib_run_dirc, self.data_dl_dirc, 'flxf06'))
		## submit the job
		jobid, error = acc.Submit(submit_script, self.scheduler)
		acc.WaitForJob(jobid, self.user, self.scheduler) 
		
		# verify completion
		#success, status = log_check(ungrib_log, success_message)
		#if success: logger.info(acc.tail(1,ungrib_log))
		#if not success: 
		#	logger.error(acc.tail(1, ungrib_log))
		#	logger.error("fatal error encountered. exiting")
		#	sys.exit()
		
		# cleanup 
		globfiles = self.ungrib_run_dirc.glob('GRIBFILE*')
		for globfile in globfiles:
			logger.debug('unlinked {}'.format(str(globfile)))
			os.unlink(globfile)
		# run the link csh script 
		# check that the script finished correctly
		os.chdir(cwd)

	@acc.timer
	def dataDownload(self):
		logger = logging.getLogger(__name__)
		logger.info('beginning data download')
		sub6 = datetime.timedelta(hours=6)
		date_range = pd.date_range(self.start_date - sub6, self.end_date, freq='6H')
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
			logger.debug('downloading ....{}'.format(url))
		os.chdir(cwd)	
		required_files = len(date_range)
		missing_files = 0 
		for f in filenames:
			if self.data_dl_dirc.joinpath(f).exists():
				pass
			else:
				print(self.data_dl_dirc.joinpath(f))
				missing_files += 1 
		if missing_files != 0:
			logger.error("{} missing files... ".format(missing_files))
			sys.exit()
		# check that the files are in fact there 
	

if __name__ == '__main__':
	pass 

