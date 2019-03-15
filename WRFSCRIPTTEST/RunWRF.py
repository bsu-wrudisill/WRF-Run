from RunDivide import *
import datetime 
import sys,os
import subprocess
import time 
from shutil import copyfile

d1 = datetime.datetime(1998, 3, 22, 0, 0)
d2 = datetime.datetime(1998, 3, 28, 0, 0)
foo=wrfChunk(True)
foo.DateGenerator(d1,d2)

class WRF_Run():
    # chunk is a chunk object created by ____.py 
    runDirectory="/scratch/wrudisill/WRFTestDir/testrun"
    user='wrudisill'
    current_state = "starting WRF Run"
    def __init__(self,chunk):
        # Copy files into the run directory and CD there
        self.chunk = chunk
        copyfile("namelist.input.template", "{}/namelist.input.template".format(self.runDirectory))
        copyfile("submit_template.sh", "{}/submit_template.sh".format(self.runDirectory))
        os.chdir(self.runDirectory)

    def Run(self):
        # loop through chunk list 
        for i in range(self.chunk.Counter):
            print i
            # do stuff           
            # update namelist 
            self.chunk.UpdateNamelist(i)
            self.chunk.WriteNameList()
            # run Real
            # wait for jobs 
            self.Real() 
            # run WRF 
            # wait for jobs 
            self.WRF()
            # finish and clean up
            # CLEAN ME 
            # 
    def Message(self):
        pass 

    def cleanReal(self):
        # rename previous wrfinput files  
        mvcmd = ['mv wrfinput_d0{} wrfinput_d0{}_{}'.format(i, i, self.chunk.slurmlist['JOBNAME']) for i in [1,2]]
        map(self.system_cmd, mvcmd)

        # remove files 
        rmcmd = ['rm wrfbdy_* wrflowinp_*']
        map(self.system_cmd, rmcmd)
        pass 

    def cleanWRF(self):
        pass 

    def Real(self):
        # remove real files 
        self.cleanReal()        
        # create wrf submit script 
        self.chunk.SlurmUpdate('r')
        self.chunk.WriteSlurm()
        # get the catchid and jobname
        catch   = self.chunk.slurmlist['CATCHID']
        jobname = self.chunk.slurmlist['JOBNAME']
        # submit the script 
        cmd_submit = "sbatch submit_{}.sh > {}".format(jobname, catch)
        # submit and gather the output 
        out,err = self.system_cmd(cmd_submit)
        # wait for jobs 
        self.WaitForJob(catch)
        pass

    def WRF(self):
        # create wrf submit script 
        self.chunk.SlurmUpdate('w')
        self.chunk.WriteSlurm()
        # get the catchid and jobname
        jobname = self.chunk.slurmlist['JOBNAME']
        catch   = self.chunk.slurmlist['CATCHID']
        # submit the script 
        cmd_submit = "sbatch submit_{}.sh > {}".format(jobname, catch)
        # submit and gather the output 
        out,err = self.system_cmd(cmd_submit)
        # wait for jobs 
        self.WaitForJob(catch)
        pass

    def system_cmd(self,cmd):
        # issue system commands 
        proc = subprocess.Popen([cmd], stdout=subprocess.PIPE, shell=True)
        out,err = proc.communicate()
        return out.split(),err
    
    def WaitForJob(self,catch):
        # Gather the Job id from the catch file
        # (the catchid gets updated with eath iteration of real/wrf)
        gid = "grep \"\" ./{} | cut -d' ' -f4".format(catch)    
        gidout,giderr = self.system_cmd(gid)    
         
        # IF STDERROR NULL (NO ERRORS) THEN CONTINUE
        jobid = gidout[0]           # assign jobid
        print "jobid found {}".format(jobid)

        still_running = 1                # start with 1 for still running 
        while still_running == 1:        # as long as theres a job running, keep looping and checking
            # command
            chid = "squeue -u {} | sed \"s/^ *//\" | cut -d' ' -f1".format(self.user)   
            # run command and parse output 
            chidout, chiderr = self.system_cmd(chid)    
            # the length of the list. should be zero or one. one means the job ID is found 
            still_running_list = list(filter(lambda x: x == jobid, chidout))
            still_running = len(still_running_list)
            time.sleep(5)
        pass 
    
    def CleanUp(self):
        # concatenate RSL files into one 
        pass        
#
wr = WRF_Run(foo)
wr.Run()

