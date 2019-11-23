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
import f90nml #must be installed via pip

def path(obj):
	# turn object into a posix path if its not none
	if obj != None:
		return pl.Path(obj)
	else:
		return None

class SetMeUp:
	def __init__(self,main):
		logger = logging.getLogger(__name__)
		logger.info('Initializing...')	
		# open up the 'main' file	
		# there should be a list of multiple 'includes', listing
		# other .yml files to read in. this is the simplest way 
		# to separate multiple config files but read them in as one
		with open(main) as m:
			config_location = main.parent
			yamlfile = yaml.load(m, Loader=yaml.FullLoader)
			for include in yamlfile.get("includes", []):
				include_path = config_location.joinpath(include)
				yamlfile.update(yaml.load(open(include_path), Loader=yaml.FullLoader), Loader=yaml.FullLoader)
	
		# 2 files should be read into the main 'yamlfile' dictionary -- a 'setup' and a 'config'
		# apply some logic to read in the correct config information based on setup params (machine
		# type, for example 
		
		# read the appropriate configuration from the config.yml file 
		machine=yamlfile.get('machine')
		if machine not in yamlfile.keys(): # check that the machine spec. in setup. is in the config file  
			logger.error('machine specification <{}> not found in config.yml'.format(machine))
			sys.exit()
		
		# get the queue submission information from the config.yml file 
		queue_params  = yamlfile.get(machine) #yuck this is kind of ugly. 
		if yamlfile.get('queue') not in queue_params.get('queue_list'):
			logger.error()
			sys.exit()
			
		# Main Configuration -- machine related
		self.geog_data_path = path(yamlfile['geog_data_path'])
		self.queue_params = queue_params
		self.setup = main # name of the setup file
		self.cwd = path(os.getcwd())
		self.user = yamlfile['user']
		self.scheduler = yamlfile.get(machine).get('scheduler')
		self.queue = yamlfile['queue']  # this is located in the 'setup.yml' file since it will freqently change 
		self.wrf_version = yamlfile['wrf_version']
		self.environment_file = self.cwd.joinpath(yamlfile['environment'])	
		
		# Look for the restart file 
		self.restart = yamlfile['restart']	

		# Find/Parse the namelist files using f90nml  
		# Assumes that they live in the /parent/namelists directory 
		# !!DANGER!! self.cwd --> this is the directory where the script gets called from !!DANGER!!
		self.wps_namelist_file_path = self.cwd.joinpath('namelists', yamlfile['wps_namelist_file'])
		self.input_namelist_file_path = self.cwd.joinpath('namelists', yamlfile['input_namelist_file'])
		
		# read the namelist file 
		with open(self.wps_namelist_file_path) as nml_file:
			self.wps_namelist_file = f90nml.read(nml_file)	

		with open(self.input_namelist_file_path) as nml_file:
			self.wps_namelist_file = f90nml.read(nml_file)	
		# Extrack key parameters about the WRF configuration
		self.num_wrf_dom = self.wps_namelist_file['domains']['max_dom']
		
		# Directories to copy from the compiled WRF model (or wherever they live on the system) 
		self.wrf_exe_dirc = path(yamlfile['wrf_exe_directory'])
		self.wps_exe_dirc = path(yamlfile['wps_exe_directory'])
		self.geo_exe_dirc = self.wps_exe_dirc.joinpath('geogrid')
		self.met_exe_dirc = self.wps_exe_dirc.joinpath('metgrid')
		self.ungrib_exe_dirc = self.wps_exe_dirc.joinpath('ungrib')
		
		#self.metgrid_files = path(yamlfile['metgrid_files'])   # OPTION FOR IF THESE ALREADY EXIST
		#self.geogrid_file = yamlfile['geogrid_file']           # "                               " 
		
		# Determine whether or not we need to run... metgrid, lbc download, geogrid 
		self.run_download_flag = True
		self.run_metgrid_flag = True
		self.run_geogrid_flag = True
		
		# these get created 
		self.main_run_dirc = path(yamlfile['main_run_dirc'])
		self.wrf_run_dirc = self.main_run_dirc.joinpath('wrf')
		self.wps_run_dirc = self.main_run_dirc.joinpath('wps')
		self.geo_run_dirc = self.wps_run_dirc.joinpath('geogrid')
		self.ungrib_run_dirc = self.wps_run_dirc.joinpath('ungrib')
		self.met_run_dirc = self.wps_run_dirc.joinpath('metgrid')
		self.data_dl_dirc = self.wps_run_dirc.joinpath('raw_lbcs')

		# forcing files stuff goes here 
		self.time_format = "%Y-%m-%d_%H:%M:%S" #!!! FOR WRF -- CHANGE ME LATER !!! 
		self.output_format ="wrfout_d0{}_{}"  # !! FOR WRF -- CHANGE ME LATER !!! 
		
		# get dates for start, end of spinup,eval period
		run_date = yamlfile['run_date']
		self.start_date = pd.to_datetime(run_date['start_date'])
		self.end_date = pd.to_datetime(run_date['end_date'])
		self.lbc_type = yamlfile['lbc_type'] 
		
		#get wrf_run_options
		self.wrf_run_options = yamlfile['wrf_run_options']
	
	def createRunDirectory(self):
		logger = logging.getLogger(__name__)	
		logger.info('Initializing...')	
		# copy contents of the 'WRFVX/run' directory to the main run dir 
		self.main_run_dirc.mkdir()
		#self.wrf_run_dirc.mkdir()
		shutil.copytree(self.wrf_exe_dirc.joinpath('run'),
				self.wrf_run_dirc, symlinks=True)
		
		# get geogrid  
		self.wps_run_dirc.mkdir()
		self.geo_run_dirc.mkdir()
		self.met_run_dirc.mkdir()
		self.ungrib_run_dirc.mkdir()
		self.data_dl_dirc.mkdir()
		
		# NAMELIST.INPUT
		shutil.copy(self.input_namelist_file_path, self.main_run_dirc.joinpath('namelist.input.template'))
		shutil.copy(self.wps_namelist_file_path, self.main_run_dirc.joinpath('namelist.wps.template'))
		
		# Copy METGRID
		shutil.copy(self.met_exe_dirc.joinpath('metgrid.exe'), self.met_run_dirc)
		shutil.copy(self.met_exe_dirc.joinpath('METGRID.TBL'), self.met_run_dirc)
		
		# Copy ungrib files 
		shutil.copytree(self.ungrib_exe_dirc.joinpath('Variable_Tables'), 
				self.ungrib_run_dirc.joinpath('Variable_Tables'))		
		
		shutil.copy(self.ungrib_exe_dirc.joinpath('ungrib.exe'), 
			    self.ungrib_run_dirc)		
		
		shutil.copy(self.wps_exe_dirc.joinpath('link_grib.csh'), 
			    self.ungrib_run_dirc)		

		# Copy geogrid files 
		shutil.copy(self.geo_exe_dirc.joinpath('geogrid.exe'), self.geo_run_dirc)		
		shutil.copy(self.geo_exe_dirc.joinpath('GEOGRID.TBL'), self.geo_run_dirc)		
		
		# Copy the environment file 
		shutil.copy(self.environment_file, self.main_run_dirc)
		
		# Copy the configure scripts  ### !!!! DANGER !!!! cwd #####
		shutil.copytree(self.cwd.joinpath('user_config'), self.main_run_dirc.joinpath('user_config'))

if __name__ == '__main__':
	setup = SetMeUp('main.yml')
	setup.createRunDirectory()
