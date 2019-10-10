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


class RunWPS(SetMeUp):
	#
	def __init__(self, setup):
		super(self.__class__, self).__init__(setup)	
	
	
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
if __name__ == '__main__':
	setup = SetMeUp('setup.yaml')
	#setup.createRunDirectory()
	foo = RunWPS('setup.yaml')
	foo.geogrid()
