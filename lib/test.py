from SetMeUp import SetMeUp
from RunWPS import RunWPS
from check_completion import geogrid_ver


if __name__ == '__main__':
	setup = SetMeUp('setup.yaml')
	setup.createRunDirectory()
	print('created run dir')
	wps = RunWPS('setup.yaml')
	print('running geogrid')
	wps.geogrid()
	print('verify')
	geogrid_ver('setup.yaml').run_all()

