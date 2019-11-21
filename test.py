import sys 
import logging, logging.config
import datetime 
import sys 
import pathlib
libPathList = ['./lib/']
for libPath in libPathList:
		sys.path.insert(0,libPath)

# import moduels from ./lib
from SetMeUp import SetMeUp
from RunWPS import RunWPS
from RunWRF import RunWRF



if __name__ == '__main__':
	#--- logger stuff ---- 	
	suffix = datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")
	logging.config.fileConfig('logger.ini', defaults={'date':suffix})
	logger = logging.getLogger(__name__)
	logger.info('Starting...')
	
	# Main Config file
	main = pathlib.Path('user_config/main.yml')


	#--- done loggering --- 
	setup = SetMeUp(main)
	setup.createRunDirectory()
	wps = RunWPS('main.yml')  
	wps.geogrid()

	#wps.dataDownload()
	#wps.ungrib()
	#wps.metgrid()
	#
	##logger.info("--------STARTING WRF-------")
	#wrf = RunWRF('main.yml')
	#wrf.SetupRunFiles()
	#wrf.WRF_TimePeriod()
