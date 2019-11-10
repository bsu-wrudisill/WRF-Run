import yaml 
import sys 

setup='main.yml'
with open(setup) as y:
	yamlfile = yaml.load(y, Loader=yaml.FullLoader)
	for include in yamlfile.get("includes", []):
		yamlfile.update(yaml.load(open(include), Loader=yaml.FullLoader))

machine=yamlfile.get('machine')
if machine not in yamlfile.keys(): # check that the machine spec. in setup. is in the config file  
	print('machine specification <{}> not found in config.yml'.format(machine))
	sys.exit()

queue_params  = yamlfile.get(machine) #yuck this is kind of ugly. 
if yamlfile.get('queue') not in queue_params.get('queue_list'):
	print('error')   
	sys.exit()

def write_submit(queue_params,
		 replacedic = None,   
		 command = None):             
	#assert type(queue_params) == list, 'unsure of queue params input'
	# open the file and write out the options line by line 
	with open('test.sh', 'w') as f:
		f.write('#!/bin/bash \n') # write the header 
		for qp in queue_params:
			if qp.endswith('\n'):
				line = qp 
			else:
				line = "{}\n".format(qp)
			
			# replace things  
			for key in replacedic.keys():
				if key in line:
					line = line.replace(key, replacedic.get(key))
		
			f.write(line)
		# write three blank lines
		f.write('\n')
		f.write('\n')
		f.write('\n')
		f.write('# job execute command goes below here\n')
		f.write(command)
		f.write('\n')

replacedic = {'WALLTIME':'00:30:00',
	      'QUEUE':'leaf'}

write_submit(queue_params.get('wrf'), replacedic,command='cd ../.')



