from SetMeUp import SetMeUp
from RunWPS import RunWPS
from check_completion import geogrid_ver
import logging 
import datetime 
import sys 



if __name__ == '__main__':
	#--- logger stuff ---- 	
	setup = SetMeUp('setup.yaml')
	setup.createRunDirectory()
	wps = RunWPS('setup.yaml')
	wps.geogrid()
	geogrid_ver('setup.yaml').run_all()
	wps.dataDownload()
	wps.ungrib()
