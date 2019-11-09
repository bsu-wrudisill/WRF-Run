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

def path(obj):
	# turn object into a posix path if its not none
	if obj != None:
		return pl.Path(obj)
	else:
		return None

class SetMeUp:
	def __init__(self,setup):
		# read stuff from yaml
		with open(setup) as y:
			yamlfile = yaml.load(y, Loader=yaml.FullLoader)
			
		self.setup = setup # name of the setup file. THIS MIGHT CHANGE LATER !!!!	
		self.cwd = path(os.getcwd())
		self.scheduler = yamlfile['scheduler']	
		self.lbc_type = yamlfile['lbc_type'] 
		self.wrf_version = yamlfile['wrf_version']
		#!!!!!!!!!!!!!!!!!!!!! VERY UGLY RELATIVE PATHS ---- NOT LONG TERM SOLUTION !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
		# READ FROM THE MAIN CONFIG SECTION 
		self.submit_template = self.cwd.parent.joinpath('namelists/submit.template.{}.sh'.format(self.scheduler))	 # CHANGE ME CHANGE ME CHANGE ME
		self.environment_file = self.cwd.parent.joinpath(yamlfile['environment'])
		self.queue = yamlfile['queue']
		self.cpu_type = yamlfile['cpu_type']
		#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
		
		# gather static paths 
		self.geog_data_path = path(yamlfile['geog_data_path'])
		self.wps_namelist_file = path(yamlfile['wps_namelist_file'])
		self.input_namelist_file = path(yamlfile['input_namelist_file'])
		
		# LOGIC
		# determing whether or not we need to run... metgrid, lbc download, geogrid 
		self.run_download_flag = True
		self.run_metgrid_flag = True
		self.run_geogrid_flag = True
		
		
		# directories to copy from the compiled WRF model (or wherever they live on the system) 
		self.wrf_exe_dirc = path(yamlfile['wrf_exe_directory'])
		self.wps_exe_dirc = path(yamlfile['wps_exe_directory'])
		self.geo_exe_dirc = self.wps_exe_dirc.joinpath('geogrid')
		self.met_exe_dirc = self.wps_exe_dirc.joinpath('metgrid')
		self.ungrib_exe_dirc = self.wps_exe_dirc.joinpath('ungrib')
		
		#self.metgrid_files = path(yamlfile['metgrid_files'])   # OPTION FOR IF THESE ALREADY EXIST
		#self.geogrid_file = yamlfile['geogrid_file']           # "                               " 
		
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
		self.output_format ="wrfout_d02_{}"  # !! FOR WRF -- CHANGE ME LATER !!! 
		
		# get dates for start, end of spinup,eval period
		run_date = yamlfile['run_date']
		self.start_date = pd.to_datetime(run_date['start_date'])
		self.end_date = pd.to_datetime(run_date['end_date'])
		
		# !!! Run Configuration Options !!!# 	
		self.user = yamlfile['user']
		self.wrf_params = yamlfile['wrf_params']
		self.wps_params = yamlfile['wps_params']
		
	
	def createRunDirectory(self):
		# copy contents of the 'WRFVX/run' directory to the main run dir 
		shutil.copytree(self.wrf_exe_dirc, self.wrf_run_dirc)
		
		# get geogrid  
		self.wps_run_dirc.mkdir()
		self.geo_run_dirc.mkdir()
		self.met_run_dirc.mkdir()
		self.ungrib_run_dirc.mkdir()
		self.data_dl_dirc.mkdir()
		
		# NAMELIST.WPS--update template and create copy 
		replace_dic = {"GEOG_PATH":self.geog_data_path,
			       "GEOG_TBL_PATH":self.geo_exe_dirc,
			       "METGRID_TBL_PATH":self.met_exe_dirc
				}
		# deal w/ filenmaes 
		wps_base = self.wps_namelist_file.name
		updated_wps_file = self.main_run_dirc.joinpath(wps_base)
		# 
		acc.GenericWrite(self.wps_namelist_file, replace_dic, updated_wps_file)
		
		# NAMELIST.INPUT
		shutil.copy(self.input_namelist_file, self.main_run_dirc)
		
		# copy METGRID
		shutil.copy(self.met_exe_dirc.joinpath('metgrid.exe'), self.met_run_dirc)
		shutil.copy(self.met_exe_dirc.joinpath('METGRID.TBL'), self.met_run_dirc)
		os.symlink(updated_wps_file, self.met_run_dirc.joinpath('namelist.wps'))
		
		# copy ungrib files 
		shutil.copytree(self.ungrib_exe_dirc.joinpath('Variable_Tables'), self.ungrib_run_dirc.joinpath('Variable_Tables'))		
		shutil.copy(self.ungrib_exe_dirc.joinpath('ungrib.exe'), self.ungrib_run_dirc)		
		shutil.copy(self.wps_exe_dirc.joinpath('link_grib.csh'), self.ungrib_run_dirc)		

		# copy geogrid files 
		shutil.copy(self.geo_exe_dirc.joinpath('geogrid.exe'), self.geo_run_dirc)		
		shutil.copy(self.geo_exe_dirc.joinpath('GEOGRID.TBL'), self.geo_run_dirc)		
		os.symlink(updated_wps_file, self.geo_run_dirc.joinpath('namelist.wps'))

if __name__ == '__main__':
	setup = SetMeUp('setup.yaml')
	setup.createRunDirectory()
