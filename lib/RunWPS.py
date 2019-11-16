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
	def geogrid(self, **kwargs):
		# kwargs options: 1) 'queue'
		#                 2) 'queue_params'
		#                 3) 'submit_script'
		
		# gather information about the job
		cwd = os.getcwd() 
		self.logger.info('starting geogrid')	
		catch_id = 'geogrid.catch'
		unique_name = "g_{}".format(secrets.token_hex(2))              # create random name 
		queue = kwargs.get('queue', self.queue)                        # get the queue 
		qp = kwargs.get('queue_params', self.queue_params.get('wps'))  # get the submit parameters               
		# location of submit script/name 
		submit_script = kwargs.get('submit_script', self.geo_run_dirc.joinpath('submit_geogrid.sh')) 
		
		# form the command 
		lines = ["source %s" %self.environment_file,
			 "cd %s" %self.geo_run_dirc,
			 "./geogrid.exe &> geogrid.catch"]
		command = "\n".join(lines)  # create a single string separated by spaces
		
		# create the run script based on the type of job scheduler system  
		replacedata = {"QUEUE":queue,
			       "JOBNAME":unique_name,
			       "LOGNAME":"geogrid",
			       "CMD": command
			       }
		
		acc.WriteSubmit(qp, replacedata, filename=submit_script)
		
		# Job Submission 
		# navigate to the run directory 
		os.chdir(self.ungrib_run_dirc)		
		jobid, error = acc.Submit(submit_script, self.scheduler)	
		# wait for the job to complete 
		acc.WaitForJob(jobid, self.user, self.scheduler)  #CHANGE_ME 
		
		# move back to main directory after job completion/failure 
		os.chdir(cwd)		
	
		# !!! check stuff !!!!
		# ! check that the geogrid.log file says "success"
		success, status = SC.test_geolog(self.geo_run_dirc)
		if not success:
			self.logger.error(status)
			self.geoStatus = True 
		else:
			self.logger.info(status)
			self.geoStatus = False 

		#! check that the geo_em? files get created 
		success, status = SC.test_geofiles(self.geo_run_dirc)
		if not success:
			self.logger.error(status)
			self.geoStatus = False 
		else:
			self.logger.info(status)

	@acc.timer	
	def ungrib(self, **kwargs):
		'''
		Run the ungrib.exe program
		kwargs:
			1) queue
			2) queue_params
			3) submit_script 
			(# Defaults to the options found in 'self')
		'''
		# Start logging
		logger = logging.getLogger(__name__)
		logger.info('entering Ungrib process in directory')
		logger.info('WRF Version {}'.format(self.wrf_version))
		
		# Fixed paths -- these should get created 
		cwd = os.getcwd() 
		vtable = self.ungrib_run_dirc.joinpath('Vtable')
		ungrib_log = self.ungrib_run_dirc.joinpath('ungrib.log')
		namelist_wps = self.ungrib_run_dirc.joinpath('namelist.wps')        
		linkGrib = '{}/link_grib.csh {}/{}' # CHANGE ME 
		catch_id = 'ungrib.catch'
		unique_name = 'u_{}'.format(secrets.token_hex(2))
		success_message = 'Successful completion of program ungrib.exe'
		
		# Get pbs submission parameters and create submit command 
		queue = kwargs.get('queue', self.queue)                        # get the queue 
		qp = kwargs.get('queue_params', self.queue_params.get('wps'))  # get the submit parameters               
		submit_script = kwargs.get('submit_script', self.ungrib_run_dirc.joinpath('submit_ungrib.sh')) 
		
		# Form the job submission command 
		lines = ["source %s" %self.environment_file,
			 "cd %s" %self.ungrib_run_dirc,
			 "./ungrib.exe &> ungrib.catch"]
		command = "\n".join(lines)  # create a single string separated by spaces
		
		# Create the run script based on the type of job scheduler system  
		replacedata = {"QUEUE":queue,
			       "JOBNAME":unique_name,
			       "LOGNAME":"ungrib-PLEVS",
			       "CMD": command
			       }
		
		
		# Adjust parameters in the namelist.wps template script 
		wps_replace_dic = {"GEOG_PATH":self.geog_data_path,
      			           "GEOG_TBL_PATH":self.geo_exe_dirc,
			           "METGRID_TBL_PATH":self.met_exe_dirc,
			           "ungribprefix":'PLEVS',	
			           "startdate":self.start_date.strftime(self.time_format),
			           "enddate":self.end_date.strftime(self.time_format),
			           }
		# Navigate to the ungrib director. !!! NOT SURE IF WE NEED TO DO THIS !!!
		os.chdir(self.ungrib_run_dirc)
		
		# Symlink the vtable
		# Different versions of WRF have differnt Vtables even for the same LBCs 
		
		# WRF V 4.0++
		if str(self.wrf_version) == '4.0':
			logger.info('Running WRF Version {} ungrib for {}' .format(self.wrf_version, self.lbc_type))
			# there is only one vtable for wrf 4.0... I think?? for CFSR 
			required_vtable = self.ungrib_run_dirc.joinpath('Variable_Tables/Vtable.CFSR')
			if not required_vtable.exists():
				logger.error('variable table {} not found. exiting'.format(required_vtable))
				sys.exit()
			# Link the Vtable; unlink if there already is one for whatver reason  
			if vtable.exists():
				os.unlink(vtable)
			os.symlink(required_vtable, vtable)
		
		# WRF V 3.8.1 
		elif str(self.wrf_version) == '3.8.1':
			required_vtable_plv = self.ungrib_run_dirc.joinpath('Variable_Tables/Vtable.CFSR_press_pgbh06')
			required_vtable_flx = self.ungrib_run_dirc.joinpath('Variable_Tables/Vtable.CFSR_press_flxf06')
			required_vtables = [required_vtable_plv.exists(), required_vtable_flx.exists()] 
			if False in required_vtables: 
				logger.error('WRF {} variable table {} not found. exiting'.format(self.wrf_version, required_vtable))
				sys.exit()
			os.symlink(required_vtable_plv, vtable) 
		
		# Other WRF Version (Catch this error earlier!!)
		else:
			logger.error('unknown wrf version {}'.format(self.wrf_version))
			sys.exit() 
 
		# 1) Ungrib the Pressure Files (PLEVS) first  
		logger.info('Starting on PLEVS (1/2)')
		acc.GenericWrite(self.main_run_dirc.joinpath('namelist.wps.template'), wps_replace_dic, namelist_wps)
		acc.WriteSubmit(qp, replacedata, filename=submit_script)
		acc.SystemCmd(linkGrib.format(self.ungrib_run_dirc, self.data_dl_dirc, 'pgbh06'))	
		
		# pressure files job submission	
		jobid, error = acc.Submit(submit_script,self.scheduler)	
		acc.WaitForJob(jobid, self.user, self.scheduler)
		
		# Verify the completion of 1) 
		success, status = acc.log_check(ungrib_log, success_message)
		if success: 
			logger.info(status)
		if not success: 
			logger.error(status)
			logger.error("Ungrib PLEVS step (1/2) did not finish correctly. Exiting")
			logger.error("check {}".format(self.ungrib_run_dirc))
			sys.exit()
		# Clean up 1) 
		globfiles = self.ungrib_run_dirc.glob('GRIBFILE*')
		for globfile in globfiles:
			logger.debug('unlinked {}'.format(str(globfile)))
			os.unlink(globfile)
		
		# 2) Ungrib the Surface Flux files (SFLUX) 
		logger.info('Starting on SFLUX (2/2)')
		
		# We need to switch vtables if we are using 3.8.1	
		if self.wrf_version == '3.8.1':
			os.unlink('unlink plevs vtable; link flx vtable')
			os.symlink(required_vtable_flx, vtable) 
		
		# Upate Dictionaries -- regardless of wrf versio we do this 
		wps_replace_dic['ungribprefix'] = 'SFLUX'
		replacedata['LOGNANE'] = "ungrib-SFLUX"
		
		# Write the submit script and the wps namelist updates
		acc.WriteSubmit(qp, replacedata, filename=submit_script)
		acc.GenericWrite(self.main_run_dirc.joinpath('namelist.wps.template'), wps_replace_dic, namelist_wps)
		
		# Link SFLXF files 
		acc.SystemCmd(linkGrib.format(self.ungrib_run_dirc, self.data_dl_dirc, 'flxf06'))
		
		# Submit the job	
		jobid, error = acc.Submit(submit_script, self.scheduler)
		acc.WaitForJob(jobid, self.user, self.scheduler) 
		
		# Verify completion
		success, status = acc.log_check(ungrib_log, success_message)
		if success: 
			logger.info(status)
		if not success: 
			logger.error(status)
			logger.error("Ungrib SFLUX step (2/2) did not finish correctly. Exiting")
			logger.error("check {}".format(self.ungrib_run_dirc))
			sys.exit()
		
		# cleanup 
		globfiles = self.ungrib_run_dirc.glob('GRIBFILE*')
		for globfile in globfiles:
			logger.debug('unlinked {}'.format(str(globfile)))
			os.unlink(globfile)
		# check that the script finished correctly
		os.chdir(cwd)
	
	
	@acc.timer
	def metgrid(self, **kwargs):
		# ----------------------------------------------
		# kwarg options
		# 
		#  ungrib_location: (path to SFLUX/PLEVS files)
		#  geogrid_location: (path to geo_em* files)
		#  --force: whether or not to clean out the metgrid directory or not  
		# ----------------------------------------------


		# Start logging
		logger = logging.getLogger(__name__)
		logger.info('entering metgrib process in directory')
		logger.info('WRF Version {}'.format(self.wrf_version))
		
		# 
		clean = kwargs.get('force', True)  #whether or not to 'clean' the dir before running 

		# Fixed paths -- these should get created 
		cwd = os.getcwd() 
		metgrid_log = self.met_run_dirc.joinpath('metgrid.log')
		namelist_wps = self.met_run_dirc.joinpath('namelist.wps')        
		catch_id = 'metgrid.catch'
		unique_name = 'm_{}'.format(secrets.token_hex(2))
		success_message = 'Successful completion of program metgrid.exe'
		
		# link ungrib files 
		logger.info('Creating symlink for SFLUX')
		for sflux in self.ungrib_run_dirc.glob('SFLUX*'):
			os.symlink(sflux, self.met_run_dirc.joinpath(sflux.name))
		
		logger.info('Creating symlink for PLEVS')
		for plevs in self.ungrib_run_dirc.glob('PLEVS*'):
			os.symlink(sflux, self.met_run_dirc.joinpath(plevs.name))

		# link geogrid files 
		for geo_em in self.geo_run_dirc.glob('geo_em.d0?.nc'):
			logger.info('Creating symlink...')
			logger.info('Found {} in {}'.format(geo_em.name, self.geo_run_dirc))
			os.symlink(geo_em, self.met_run_dirc.joinpath(geo_em.name))

		
		# Get pbs submission parameters and create submit command 
		queue = kwargs.get('queue', self.queue)                        # get the queue 
		qp = kwargs.get('queue_params', self.queue_params.get('wps'))  # get the submit parameters               
		submit_script = self.met_run_dirc.joinpath('submit_metgrid.sh')
		
		# Form the job submission command 
		lines = ["source %s" %self.environment_file,
			 "cd %s" %self.met_run_dirc,
			 "./metgrid.exe &> metgrid.catch"]
		command = "\n".join(lines)  # create a single string separated by spaces
		
		# Create the run script based on the type of job scheduler system  
		replacedata = {"QUEUE":queue,
			       "JOBNAME":unique_name,
			       "LOGNAME":"metgrid",
			       "CMD": command
			       }
		
		# Adjust parameters in the namelist.wps template script 
		wps_replace_dic = {"GEOG_PATH":self.geog_data_path,
      			           "GEOG_TBL_PATH":self.geo_exe_dirc,
			           "METGRID_TBL_PATH":self.met_exe_dirc,
			           "startdate":self.start_date.strftime(self.time_format),
			           "enddate":self.end_date.strftime(self.time_format),
			           }
		
		# Navigate to the metgrid director. !!! NOT SURE IF WE NEED TO DO THIS !!!
		acc.GenericWrite(self.main_run_dirc.joinpath('namelist.wps.template'), wps_replace_dic, namelist_wps)
		acc.WriteSubmit(qp, replacedata, filename=submit_script)

		# 
		jobid, error = acc.Submit(submit_script, self.scheduler)
		acc.WaitForJob(jobid, self.user, self.scheduler) 
		
		# Verify completion
		success, status = acc.log_check(ungrib_log, success_message)
		if success: 
			logger.info(status)
		if not success: 
			logger.error(status)
			logger.error("Metgrid finsihed successfully")
			logger.error("check {}".format(self.ungrib_run_dirc))
			sys.exit()
	
	@acc.timer
	def dataDownload(self):
		logger = logging.getLogger(__name__)
		logger.info('beginning data download')
		sub6 = datetime.timedelta(hours=6)
		date_range = pd.date_range(self.start_date - sub6, self.end_date, freq='6H')
		self.file_spec = '06.gdas'
		# 
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

