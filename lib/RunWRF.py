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


class RunWRF(SetMeUp):
	def __init__(self, setup):
		super(self.__class__, self).__init__(setup)	
		self.logger = logging.getLogger(__name__)
		self.logger.info('initialized RunWRF instance')	
	
		'''
		Divide up the run into the correct size of 'chunks'
		We generally (perhaps debatably...) don't want to 
		run WRF for long run times. Also figure out the walltime 
		for the runs  
		'''
		
		zippedlist = list(acc.DateGenerator(self.start_date, self.end_date, chunksize=1))
		chunk_tracker = {}
		
		self.logger.info('WRF start date: %s', self.start_date)
		self.logger.info('WRF end date: %s', self.end_date)
		self.logger.info('WRF chunk time: %s days', self.wrf_run_options['chunk_size'])
		self.logger.info('WRF number of chunks: %s', len(zippedlist))
		for i,chunk in enumerate(zippedlist):
			# calculate the lenght of the chunk 
			chunk_start = chunk[0]
			chunk_end = chunk[1]
			chunk_days  = (chunk_end - chunk_start).days
			chunk_hours  = (chunk_end - chunk_start).days*24 + (chunk_end - chunk_start).seconds/3600
			self.logger.info('Chunk %s: %s -- %s (%s hours)', i, chunk_start, chunk_end, chunk_hours)
			
			# assign things to the dictionary
			chunk_tracker[i] = {'start_date': chunk_start,
					    'end_date': chunk_end,
					    'run_hours': chunk_hours,
					    'walltime_request': chunk_hours*self.wrf_run_options['wall_time_per_hour']}
		
		# assign chunk list to self
		self.chunk_tracker = chunk_tracker	
	
	def SetupRunFiles(self, **kwargs):
		''' kwargs:
		      1) start_date
		      2) end_date
		      3) met_dirc   (location of metfiles. str or posixPath)
		'''
		# Gather kwargs or assign defaults
		# -------------------------------
		# if no path is assigned, the met dirc will look in the 
		# metgrid run directory by default 	
		geo_dirc = kwargs.get('geo_dirc', self.geo_run_dirc)
		met_dirc = kwargs.get('met_dirc', self.met_run_dirc)
		
		# log start 
		self.logger.info('Setting up...\n{}'.format(self.wrf_run_dirc))
		self.logger.info('Seeking met files in...\n{}'.format(met_dirc))
		self.logger.info('Seeking geogrid files in...\n{}'.format(geo_dirc))
		
		# Geogrid 1) Check and 2) Link to WRF/run directory
		# -------------------------------------------------
		required_geo_files = ['geo_em.d01.nc']   # CHANGE ME--- need to read the namelist to get this right
		geo_found, message = acc.file_check(required_geo_files,
				                  geo_dirc,
						  desc='GeoFiles',
						  logger=self.logger)
		if not geo_found:
			logger.error('req. geogrid files not found in {}\nExiting.'.format(geo_dirc))
		
			

		# Metgrid 1) Check and 2) Link to WRF/run directory 
		#-------------------------------------------------
		# create list of the required dates 
		date_range = pd.date_range(self.start_date, self.end_date, freq='3H')  #!!! ALERT !!! 3 hours... is it always?
		# what controls the timestep for metgrid????
		
		met_format = 'met_em.d01.{}-{}-{}_{}:00:00.nc'
		required_met_files = []
		for date in date_range:
			y = date.strftime('%Y')
			m = date.strftime('%m')
			d = date.strftime('%d')
			h = date.strftime('%H')
			required_met_files.append(met_format.format(y,m,d,h))
			


		# Check if the required metgrid files exist in the metgrid directory
		met_found, message = acc.file_check(required_met_files, 
				                 met_dirc, 
						 desc='MetgridFiles', 
						 logger=self.logger)
		
		if not met_found: # required metgrid files have not been found 
			self.logger.error('unable to located the required metgrid files. exiting')

		# Link appropriate files
		# ---------------------
		# Symlinks in the destination directory will be overwritten 
		if met_found and geo_found:	
			self.logger.info('Found required geogrid and metgrid files')
			self.logger.info('Symlinking geo and met files to {}'.format(self.wrf_run_dirc))
			# move metgrid files to the run directory 
			for metfile in required_met_files:
				src = self.met_run_dirc.joinpath(metfile)
				dst = self.wrf_run_dirc.joinpath(metfile)
				# remove destination link if it exists 
				if dst.is_symlink():
					dst.unlink()
				os.symlink(src, dst)

			for geofile in required_geo_files: 
				src = self.geo_run_dirc.joinpath(geofile)
				dst = self.wrf_run_dirc.joinpath(geofile)
				# remove destination link if it exists 
				if dst.is_symlink():
					dst.unlink()
				os.symlink(src, dst)
			# log success message 
			self.logger.info('******Success********')
		else:
			self.logger.error('Required met/geo files not found.\nExiting')
			sys.exit()
			


	def _real(self, **kwargs):
		'''
		kwargs: 
		1) geo_dir:
		2) met_dir:
		3) wrf_dir: 
		4) start_date:
		5) end_date: 
		6) restart_file: 
		'''
		cwd = os.getcwd()
		self.logger.info('starting real')	
		catch_id = 'real.catch'
		unique_name = "r_{}".format(secrets.token_hex(2))              # create random name 
		queue = kwargs.get('queue', self.queue)                        # get the queue 
		qp = kwargs.get('queue_params', self.queue_params.get('real'))  # get the submit parameters               
		
		# location of submit script/name 
		submit_script = self.wrf_run_dirc.joinpath('submit_real.sh')
		
		# form the command 
		lines = ["source %s" %self.environment_file,
			 "cd %s" %self.wrf_run_dirc,
			 "./real.exe &> real.catch"]
		command = "\n".join(lines)  # create a single string separated by spaces
		
		# create the run script based on the type of job scheduler system  
		replacedata = {"QUEUE":queue,
			       "JOBNAME":unique_name,
			       "LOGNAME":"real",
			       "CMD": command
			       }
		
		acc.WriteSubmit(qp, replacedata, filename=submit_script)
		
		# Job Submission 
		# navigate to the run directory 
		os.chdir(self.wrf_run_dirc)		
		jobid, error = acc.Submit(submit_script, self.scheduler)	
		# wait for the job to complete 
		acc.WaitForJob(jobid, self.user, self.scheduler)  
		
		# move back to main directory after job completion/failure 
		os.chdir(cwd)		
	
	def _wrf(self, **kwargs):
		pass 	
		
	def WRF(self, **kwargs):
		'''
		kwargs: 
		1) geo_dir:
		2) met_dir:
		3) wrf_dir: 
		4) start_date:
		5) end_date: 
		6) restart_file: 
		'''
		
		
		pass
