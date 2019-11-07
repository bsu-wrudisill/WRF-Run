import sys 
import yaml
import os
import glob
import accessories as acc 
'''
Checks that the necessary files, folders, and environments are setup before starting the calibration procedure
The purpose is to be QUICK -- not completely thorough. The goal is to check for common or likely mistakes 
'''
import logging
logger = logging.getLogger(__name__)
from SetMeUp import SetMeUp

# Checker Classes 
class geogrid_ver(SetMeUp):
	# checks that the config.yaml file is sensible (paths exist, etc)
	def __init__(self,setup):
		# This is an incredibly handy function all of the self.X attrs. from SetMeUP 
		# instance get put into the "self" of this object
		# same as super(RunPreCheck, self).__init__(setup)
		super(self.__class__, self).__init__(setup)  
	
	@acc.passfail
	def test_logmesssage(self):
		# interpret the log file  
		geolog= self.geo_run_dirc.joinpath('geogrid.log')
		string = acc.tail(1, geolog)
		success_message = "Successful completion of program geogrid.exe"
		assert success_message in string, "geogrid failure likely. check {}".format(geolog)

	@acc.passfail
	def test_files(self):
		geo_em= self.geo_run_dirc.joinpath('geo_em.d01.nc')  # MAKE LOCIC TO CHECK MULTIPLE !!!!
		assert geo_em.is_file(), "geo_em? file not found"

	# FIND A WAY TO MAKE THIS APPLY TO ALL CLASSES 
	def run_all(self):
		# emulate behavior of the unittesting module 
		testList = [method for method in dir(self.__class__) if method.startswith('test_')]	
		numTests = len(testList)
		numPassedTests = 0 
		logger.info("========================   {}     ===================".format(self.__class__.__name__))
		for test in testList:
			testFunction = getattr(self.__class__, test)
			success,status = testFunction(self)
			if success: logger.info(status) 
			if not success: logger.error(status)
			numPassedTests += success # zero or one 
		logger.info("{} out of {} tests passed".format(numPassedTests, numTests))
		print("{} out of {} tests passed".format(numPassedTests, numTests))
		# return status of test passing  
		if numPassedTests != numTests:
			return False 
		else:	
			return True

@acc.passfail
def log_check(logfile, message):
	string = acc.tail(1, logfile)
	assert message in string, string 


