#!/bin/bash -l        
#PBS -l walltime=RUN_TIME,nodes=NODES:ppn=TASKS
#PBS -m WRF_TASK 
#PBS -q QUEUE
#PBS -m abe
#PBS -M EMAIL 
#PBS -e LOGNAME



#~~~~~~~~ Source Module Files ~~~~~~~~~~~~~~~~~~~~~
module purge 
source ENVIRONMENT_FILE 

#~~~~~~~~~~~~ RUN EXECUTABLE ~~~~~~~~~~~~~~~~
mpirun -np TASKS ./EXECUTABLE &> CATCHID # !!!!!!  CHANGE ME !!!!!!! 

exit 
