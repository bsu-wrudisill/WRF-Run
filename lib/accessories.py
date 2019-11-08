import os
import sys 
import datetime 
import subprocess
import time 
import glob 
import xarray as xr
import numpy as np
import time 
import traceback
import logging
import threading 
logger = logging.getLogger(__name__)


# function decorators 
def passfail(func):
	def wrapped_func(*args, **kwargs):
		try:
			func(*args)
			message = "{} Passed".format(str(func))
			return (True,message)
		except Exception as e:
			trace_string =  traceback.format_exc()	
			error_message = "{} Failed with the following Error: {}\n {}".format(str(func), e, trace_string)
			return (False, error_message)
	return wrapped_func


def timer(function):
	# simple decorator to time a function
	def wrapper(*args,**kwargs):
		t1 = datetime.datetime.now()
		wrapped_function = function(*args,**kwargs)
		t2 = datetime.datetime.now()
		dt = (t2 - t1).total_seconds()/60   # time in minutes
		logging.info('function {} took {} minutes complete'.format(function.__name__, dt))	
		return wrapped_function
	return wrapper

# functions 
def CleanUp(path):
	# remove files from the run directory 
	cwd = os.getcwd()
	os.chdir(path)
	removeList = ["*LDASOUT*"
		    ,"*CHRTOUT*"
		    ,"*RTOUT*"
		    ,"*LSMOUT*"
		    ,"*diag_hydro*"
		    ,"*HYDRO_RST*"
	            "log_wrf_hydro*"]
	
	logger.info('cleaning up model run directory ({})'.format(path)) 
	for removeMe in removeList:
		for singleFile in glob.glob(removeMe):
			try:
				os.remove(singleFile)
			except:
				pass
	# move back to o.g. dir
	os.chdir(cwd)

def SystemCmd(cmd):
	# issue system commands 
	proc = subprocess.Popen([cmd], stdout=subprocess.PIPE, shell=True)
	out,err = proc.communicate()
	return out.split(),err

def Submit(subname,catchid, subtype):
	if scheduler == 'PBS':
		subcmd = 'qsub'
	if scheduler == 'SLURM':
		subcmd = 'sbatch'
	else:
		logger.error('unknown scheduler type {}'.format(subtype))
		
	cmd = '{} --parsable {}'.format(subname, subtype)
	proc = subprocess.Popen([cmd], stdout=subprocess.PIPE, shell=True)	
	jobid,err = proc.communicate()
	logger.info("submitting job: {}".format(cmd))
	return jobid.decode("utf-8").rstrip(),err


def WaitForJob(jobid,user):
	# ----NEW METHOD--- PASS IN JOBID 
	still_running = 1     # start with 1 for still running 
	while still_running == 1: # as long as theres a job running, keep looping and checking
		# command
		chid = "squeue -u {} | sed \"s/^ *//\" | cut -d' ' -f1".format(user)   
		# run command and parse output 
		chidout, chiderr = SystemCmd(chid)    
		chidout = [i.decode("utf-8") for i in chidout]
		# convert the id to an integer
		# the length of the list. should be zero or one. one means the job ID is found 
		still_running_list = list(filter(lambda x: x == jobid, chidout))
		still_running = len(still_running_list)
		logger.debug('jobID {} is still running...'.format(still_running_list))
		logger.debug('sleep for 10 seconds')
		time.sleep(10)

def formatDate(dstr):
	if type(dstr) == str:
		return datetime.datetime.strptime(dstr, '%Y-%m-%d')
	if type(dstr) == datetime.datetime:
		return dstr
	

def GenericWrite(readpath,replacedata,writepath):
	# path to file to read 
	# data dictionary to put into file
	# path to the write out file 
	with open(readpath, 'r') as file:
	    filedata = file.read()
	    #  
	    # loop thru dictionary and replace items
	for item in replacedata:
	    filedata = filedata.replace(item, str(replacedata[item])) # make sure it's a string 

	# Write the file out again
	with open(writepath, 'w') as file:
	    file.write(filedata)
	# done 


#------------- slightly less generic commands ---------# 
def tail(linenumber, filename):
	# issue a system tail commnad 
	returnString, error = SystemCmd('tail -n {} {}'.format(linenumber, filename))
	returnString = ' '.join([x.decode("utf-8")  for x in returnString])
	return returnString 	

def fetchFile(filepath):
	# wget a file 
	SystemCmd('wget --output-file=logfile {}'.format(filepath)) # CHANGE ME...


@timer 
def multi_thread(function, mappable):
	# generic function
	# applies given function to list, where a list item 
	# is the ONLY input arg to that function
	thread_chunk_size = 5 
	def divide_chunks(l, n): 
		# looping till length l 
		for i in range(0, len(l), n):  
			yield l[i:i + n] 		  

	# create a list of lists 
	chunked_list = list(divide_chunks(mappable, thread_chunk_size))
	# loop thru the chunked list. max of <thread_chunk_size> threads get opened 
	for chunk in chunked_list:
		threads = [threading.Thread(target=function, args=(item,)) for item in mappable]
		for thread in threads:
			thread.start()
		for thread in threads:
			thread.join()

