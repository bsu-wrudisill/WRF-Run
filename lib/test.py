from SetMeUp import SetMeUp
from RunWPS import RunWPS
from check_completion import geogrid_ver
import logging 
import datetime 
import sys 



if __name__ == '__main__':
	#--- logger stuff ---- 	
	suffix = datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")
	logfile= 'WRF_logfile_{}.log'.format(suffix)
	file_handler = logging.FileHandler(filename=logfile)
	stdout_handler = logging.StreamHandler(sys.stdout)
	logging.basicConfig(level=logging.INFO, format = '%(asctime)s %(name)15s %(funcName)s %(levelname)-8s %(message)s',datefmt='%a, %d %b %Y %H:%M:%S',handlers=[file_handler, stdout_handler])
	logger = logging.getLogger(__name__)
	logger.setLevel(logging.DEBUG)
	#--- done loggering --- 
	
	setup = SetMeUp('setup.yaml')
	#setup.createRunDirectory()
	wps = RunWPS('setup.yaml')
	#wps.geogrid()
	#geogrid_ver('setup.yaml').run_all()
	wps.dataDownload()
	#wps.ungrib()
