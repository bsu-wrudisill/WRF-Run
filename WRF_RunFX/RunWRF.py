import RunDivide as RD
import datetime 
import sys,os
import subprocess
import time 
from shutil import copyfile

"""
General structure:
The "RunDivde" script creates a "chunk" object given a starting and ending date.
This object divides up the run into intervals with the appropriate times. The 
chunk object contains a method to update and write out namelist files when called 
(chunk.UpdateNamelist and chunk.WriteNameList respectively).
The RunWRF class is used to make calls to the chunk object when appropriate (to update 
namelists/submit scripts) and make system calls to run wrf.exe and real.exe
"""


class WRF_Run():
    # chunk is a chunk object created by ____.py 

    user='wrudisill'
    current_state = "starting WRF Run"

    def __init__(self,chunk,runDirectory):
        self.runDirectory=runDirectory       # Copy files into the run directory and CD there
        self.chunk = chunk
        copyfile("namelist.input.template", "{}/namelist.input.template".format(self.runDirectory))
        copyfile("submit_template.sh", "{}/submit_template.sh".format(self.runDirectory))
        os.chdir(self.runDirectory)

    def Run(self, **kwargs):
        # loop through the list of chunk time periods and 
        # 1) update/write namelists
        # 2) run real.exe  
        # 3) update/write namelists 
        # 4) run wrf.exe 
        wrfinmod = kwargs.get("wrfinmod", False)

        # loop through chunks         
        for i in range(self.chunk.Counter):
            print i
            # do stuff           
            # update namelist 
            self.chunk.UpdateNamelist(i)
            self.chunk.WriteNamelist()
            # proceed as normal 
            self.Real()
            
            # run WRF 
            # wait for jobs 
            self.WRF()
            # finish and clean up
            # CLEAN ME 
            # 
        self.cleanRun()
    
    def Message(self):
        pass 

    def cleanRun(self):
        rslcmd=["cat rsl.out.???? >> rsl_out_all",
                "cat rsl.error.???? >> rsl_error_all",
                "rm rsl.error.*",
                "rm rsl.out.*"]
        
        # clean up the rsl files  
        map(self.system_cmd, rslcmd)
         
          
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
    
    def RealWrapper(self,chunk,**kwargs):
        # only run real if the chunk is > 0.
        # this lets us change the wrfinput files
        if chunk == 0:
            pass
        else: 
            self.Real()

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

