import sys 
import yaml
import pandas as pd 
import os
import xarray as xr
import glob
from accessories import passfail 
from SetMeUp import SetMeUp
'''
Checks that the necessary files, folders, and environments are setup before starting the calibration procedure
The purpose is to be QUICK -- not completely thorough. The goal is to check for common or likely mistakes 
'''

import logging

# Checker Classes 
class RunPreCheck(SetMeUp):
	# checks that the config.yaml file is sensible (paths exist, etc)
	def __init__(self, setup):
		# This is an incredibly handy function all of the self.X attrs. from SetMeUP 
		# instance get put into the "self" of this object
		# same as super(RunPreCheck, self).__init__(setup)
		super(self.__class__, self).__init__(setup)  
		self.logger = logging.getLogger(__name__)	
	
	@passfail
	def test_existenz(self):
		assert os.path.exists(self.main_run_dirc) == False, '{} already exists. Exiting'.format(self.main_run_dirc)
	
	@passfail
	def test_dates(self):
		#Purpose: test that the date ranges passed into the model config (in the .yaml file) are reasonable
		assert (self.end_date > self.start_date), "Specified model start date is before the model end date. Fatal"
	
	@passfail
	def test_restart(self):
		if (self.restart == 'None') or (self.restart == None):
			assert 1==1
		else:
			assert os.path.exists(self.restart), "{} Not found".format(self.restart)
			# ASSERT THAT THE RESTART IS THE RIGHT DATE 
	@passfail
	def test_queue(self):
		queue_list = self.queue_params['queue_list']
		assert self.queue in queue_list, '{} not one of {}'.format(self.queue, queue_list)
	
	def run_all(self):
		# emulate behavior of the unittesting module 
		testList = [method for method in dir(self.__class__) if method.startswith('test_')]	
		numTests = len(testList)
		numPassedTests = 0 
		self.logger.info("========================   {}     ===================".format(self.__class__.__name__))
		for test in testList:
			testFunction = getattr(self.__class__, test)
			success,status = testFunction(self)
			if success: self.logger.info(status) 
			if not success: self.logger.error(status)
			numPassedTests += success # zero or one 
		self.logger.info("{} out of {} tests passed".format(numPassedTests, numTests))
		# return status of test passing  
		if numPassedTests != numTests:
			return False 
		else:	
			return True


if __name__ == '__main__':
	pass


