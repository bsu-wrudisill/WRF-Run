import sys
import shutil
import os 
import time 
import sys 
import datetime 
import logging
import yaml 
import pathlib as pl
import pandas as pd 
import accessories as acc 
from SetMeUp import SetMeUp
from RunWPS import RunWPS
from functools import partial 
import glob 
import secrets
import f90nml 

class RunWRF(SetMeUp):
    def __init__(self, setup, wps=None):
        super(self.__class__, self).__init__(setup) 
        self.logger = logging.getLogger(__name__)
        self.logger.info('initialized RunWRF instance') 
        # OPTIONAL: Pass in a WPS instance 
        # and read stuff from it. Get latest 
        # WPS state. The internal WPS checks 
        # should say that WPS is good-to-go
        # The latest date information should
        # should also be present 
        if wps != None:
            self.InheritWPS(wps)
        
        # Divide up the run into sections   
        self.RunDivide()    
    
    def InheritWPS(self,wps):
        # update current state  
        self.start_date = wps.start_date 
        self.end_date = wps.end_date 
    
        # new state 
        self.WRFready = wps.WRFready
        self.wps = wps
    
    def RunDivide(self, **kwargs):
        '''
        Divide up the run into the correct size of 'chunks'
        We generally (perhaps debatably...) don't want to 
        run WRF for long run times. Also figure out the walltime 
        for the runs  
        '''
        # THIS MODIFIES THE STATE OF ITSELF EVERYTIME IT GETS CALLED!!!! 
        start_date = acc.DateParser(kwargs.get('start_date', self.start_date))
        end_date = acc.DateParser(kwargs.get('end_date', self.end_date))
        chunk_size = kwargs.get('chunk_size', self.wrf_run_options['chunk_size'])

        # get the start/end dates 
        zippedlist = list(acc.DateGenerator(start_date, end_date, chunk_size))
        chunk_tracker = [] 
            
        # log things    
        self.logger.info('WRF start date: %s', self.start_date)
        self.logger.info('WRF end date: %s', self.end_date)
        self.logger.info('WRF chunk time: %s days', chunk_size)
        self.logger.info('WRF number of chunks: %s', len(zippedlist))
        for i,dates in enumerate(zippedlist):
            # calculate the lenght of the chunk 
            chunk_start = dates[0]
            chunk_end = dates[1]
            chunk_days  = (chunk_end - chunk_start).days
            chunk_hours  = (chunk_end - chunk_start).days*24 + (chunk_end - chunk_start).seconds/3600
            self.logger.info('Chunk %s: %s -- %s (%s hours)', i, chunk_start, chunk_end, chunk_hours)
            # determine if the initial run is a restart:
            if i == 0:
                restart = False #self.restart -- pass into the setup file TODO
            else:
                restart = True
            
            # assign things to the dictionary
            chunk = {'start_date': chunk_start,  # timestamp obj
                     'end_date': chunk_end,      # timestamp obj
                     'run_hours': int(chunk_hours),
                 'restart': restart,
                     'walltime_request': chunk_hours*self.wrf_run_options['wall_time_per_hour']}
            # assign to the list 
            chunk_tracker.append(chunk)
                
        # assign chunk list to self
        self.chunk_tracker = chunk_tracker  
        
    def PreCheck(self,**kwargs):
        '''
        Based on the start:end date and other parameters... check that the 
        required geogrid and metgrid files are found in the directory of your 
        choosing. This can be used to search for files from the WPS directory
        before linking them over, or to pre-check the WRF directrory before 
        submitting a run. 
        '''
        # Gather kwargs or assign defaults
        # -------------------------------
        # if no path is assigned, the met dirc will look in the 
        # metgrid run directory by default  
        geo_dirc = kwargs.get('geo_dirc', self.geo_run_dirc)
        met_dirc = kwargs.get('met_dirc', self.met_run_dirc)
        
        # log start 
        self.logger.info('Setting up...\n{}'.format(self.wrf_run_dirc))
        self.logger.info('Seeking met files in...\n{}'.format(met_dirc))
        self.logger.info('Seeking geogrid files in...\n{}'.format(geo_dirc))
        
        # Get the number of WRF domains 
        n = self.num_wrf_dom
        
        # Geogrid Check 
        # -------------------------------------------------
        required_geo_files = ['geo_em.d0{}.nc'.format(i+1) for i in range(n)]   
        geo_found, geo_message = acc.file_check(required_geo_files,
                                  geo_dirc,
                          desc='GeoFiles')
        # Metgrid Check 
        #-------------------------------------------------
        # create list of the required dates 
        date_range = pd.date_range(self.start_date, self.end_date, freq='3H')  
        # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        #            ALERT !!! 3 hours...(IS IT ALWAYS THIS???)
        # What controls the timestep for metgrid???? 
        # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        met_format = 'met_em.d0{}.{}-{}-{}_{}:00:00.nc'
        required_met_files = []
        for i in range(n): # number of wrf_domains
            for date in date_range:
                y = date.strftime('%Y')
                m = date.strftime('%m')
                d = date.strftime('%d')
                h = date.strftime('%H')
                required_met_files.append(met_format.format(i+1,y,m,d,h))
            
        # Check if the required metgrid files exist in the metgrid directory
        met_found, met_message = acc.file_check(required_met_files, 
                                 met_dirc, 
                         desc='MetgridFiles')
        
        # create status and return 
        status = {'geo': [geo_found, geo_message],
                  'met': [met_found, met_message]}
        return status 

    def SetupRunFiles(self, **kwargs):
        ''' kwargs:
              1) start_date
              2) end_date
              3) met_dirc   (location of metfiles. str or posixPath)
        '''
        status = self.PreCheck(geo_dirc=self.geo_run_dirc,
                               met_dirc=self.met_run_dirc)
        # 
        met_found,met_message = status['met']
        geo_found,geo_message = status['geo']
        # Link appropriate files
        # ---------------------
        # Symlinks in the destination directory will be overwritten 
        if met_found and geo_found: 
            self.logger.info('Found required geogrid and metgrid files')
            self.logger.info('Symlinking geo and met files to {}'.format(self.wrf_run_dirc))
            # move metgrid files to the run directory 
            for metfile in required_met_files:
                src = self.met_run_dirc.joinpath(metfile)
                dst = self.wrf_run_dirc.joinpath(metfile)
                # remove destination link if it exists 
                if dst.is_symlink():
                    dst.unlink()
                os.symlink(src, dst)

            for geofile in required_geo_files: 
                src = self.geo_run_dirc.joinpath(geofile)
                dst = self.wrf_run_dirc.joinpath(geofile)
                # remove destination link if it exists 
                if dst.is_symlink():
                    dst.unlink()
                os.symlink(src, dst)
            # log success message 
            self.logger.info('******Success********')
        
        else:
            if not geo_found:
                logger.error('req. geogrid files not found in {}\nExiting.'.format(geo_dirc))
                logger.error(geo_message)
            if not met_found:
                logger.error('req. metgrid files not found in {}\nExiting.'.format(geo_dirc))
                logger.error(met_message)
            self.logger.error('Required met/geo files not found.\nExiting')
            sys.exit()
    
    def TearDown(self):
        # Move files to appropriate directories, if successful 
        wrf_file_list = []
        date_range = pd.date_range(self.start_date, self.end_date, freq='1D') 
        for d in self.num_wrf_dom:
            for date in date_range:
                wrf_name = self.output_format(d, date)
                wrf_file_list.append(wrf_name)
        found_files, message = acc.filecheck(wrf_file_list, self.wrf_run_dirc)
        if found_files:
            self.logger.info(message)
        else:
            self.logger.error(message)
            self.logger.info('Exiting')
            sys.exit()

    def _real(self, **kwargs):
        # 0/xxx Check that a namelist exists (this function does not update namelists!)
        namelist = self.wrf_run_dirc.joinpath('namelist.input')
        if namelist.is_file():
            self.logger.info('Found {}. Continuing'.format(namelist))
        else:
            self.logger.error('No namelist.input found in {}. Exiting\n'.format(namelist.parent()))
            raise FileNotFound  

        # 1/xxx Gather/create parameters
        # ------------------------------
        cwd = os.getcwd()
        self.logger.info('starting real')   
        catch_id = 'real.catch'
        unique_name = "r_{}".format(secrets.token_hex(2))              # create random name 
        queue = kwargs.get('queue', self.queue)                        # get the queue 
        qp = kwargs.get('queue_params', self.queue_params.get('real'))  # get the submit parameters               
        success_message = "real_em: SUCCESS COMPLETE REAL_EM INIT"
        real_log = self.wrf_run_dirc.joinpath('rsl.out.0000')
        
        # 2/xxx Create the REAL job submission script 
        # -------------------------------------------
        submit_script = self.wrf_run_dirc.joinpath('submit_real.sh')
        
        # form the command 
        lines = ["source %s" %self.environment_file,
             "cd %s" %self.wrf_run_dirc,
             "./real.exe &> real.catch"]
        command = "\n".join(lines)  # create a single string separated by spaces
        
        # create the run script based on the type of job scheduler system  
        replacedata = {"QUEUE":queue,
                   "JOBNAME":unique_name,
                   "LOGNAME":"real",
                   "CMD": command,
                   "RUNDIR":str(self.wrf_run_dirc)
                   }
        # write the submit script 
        acc.WriteSubmit(qp, replacedata, submit_script)
        
        # 3/xxx Submit the Job and wait for completion
        #---------------------------------------------  
        jobid, error = acc.Submit(submit_script, self.scheduler)    
        # wait for the job to complete 
        acc.WaitForJob(jobid, self.user, self.scheduler)  
        
        
        # 4/xxx check that the job completed correctly 
        success, status = acc.log_check(real_log, success_message, logger=self.logger)
        if success:
            return True 
        
        if not success:
            self.logger.error('Real.exe did not finish successfully.\nExiting')
            self.logger.error('check {}/rsl.error* for details'.format(self.wrf_run_dirc))
            return False 
    
    def _wrf(self, **kwargs):
        """
        This function ONLY: runs WRF and waits for it to complete! It does NOT setup the namelist.input.
        Namelist setup must be done elsewhere. It writes the submit script, however. Which is why 
        the walltime gets passed in as a kwarg. I suppose that it could read the namelist.input
        and figure out the correct walltime to write... but that's too much weird logic 

        kwargs: 1) walltime (defaults to 05:00)
        """
        self.logger.info('starting wrf')

        # 0/xxx Check that a namelist exists (this function does not update namelists!)
        # -----------------------------------------------------------------------------
        namelist = self.wrf_run_dirc.joinpath('namelist.input')
        if namelist.is_file():
            self.logger.info('Found {}. Continuing'.format(namelist))
        else:
            self.logger.error('No namelist.input found in {}. Exiting\n'.format(namelist.parent()))
            raise FileNotFound  
    
        # 1/xxx Gather/create parameters
        # ------------------------------
        cwd = os.getcwd()
        walltime = kwargs.get("walltime","05:00:00")
        catch_id = 'wrf.catch'
        unique_name = "w_{}".format(secrets.token_hex(2))              # create random name 
        queue = kwargs.get('queue', self.queue)                        # get the queue 
        qp = kwargs.get('queue_params', self.queue_params.get('wrf'))  # get the submit parameters               
        success_message = "wrf: SUCCESS COMPLETE WRF"
        wrf_log = self.wrf_run_dirc.joinpath('rsl.out.0000')
        
        # 2/xxx Create the REAL job submission script 
        # -------------------------------------------
        submit_script = self.wrf_run_dirc.joinpath('submit_wrf.sh')
        
        # form the command 
        lines = ["source %s" %self.environment_file,
             "cd %s" %self.wrf_run_dirc,
             "mpirun ./wrf.exe &> wrf.catch"]
        command = "\n".join(lines)  # create a single string separated by spaces
        
        # create the run script based on the type of job scheduler system  
        replacedata = {"QUEUE":queue,
                   "JOBNAME":unique_name,
                   "LOGNAME":"wrf",
                   "WALLTIME": walltime,
                   "CMD": command,
                   "RUNDIR":str(self.wrf_run_dirc)
                   }
        # write the submit script 
        acc.WriteSubmit(qp, replacedata, submit_script)
        
        # 3/xxx Submit the Job and wait for completion
        #---------------------------------------------  
        jobid, error = acc.Submit(submit_script, self.scheduler)    
        # wait for the job to complete 
        acc.WaitForJob(jobid, self.user, self.scheduler)  
        
        # 4/xxx check that the job completed correctly 
        success, status = acc.log_check(wrf_log, success_message, logger=self.logger)
        if success:
            return True
        if not success:
            return False 
            self.logger.error('Wrf.exe did not finish successfully.\nExiting')
            self.logger.error('check {}/rsl.error* for details'.format(self.wrf_run_dirc))

        
    def WRF_TimePeriod(self, **kwargs):
        '''
        Run WRF and Real
        '''
        #numer of chunks
        num_chunks = len(self.chunk_tracker)
        for num,chunk in enumerate(self.chunk_tracker):
            self.logger.info('****Starting Real/WRF Chunk ({}/{})****'.format(num, num_chunks)) 
            self.logger.info(self.wrf_run_dirc) 
            framesperout=24
            framesperaux=24
            restartinterval=chunk['run_hours']*60
            walltime=chunk['walltime_request']
            n = self.num_wrf_dom            
            
            # TODO: create a chunk class where the strings formatting is a method..
            # This is Gnar...
            # update starting dates  
            input_patch = {"time_control": {"run_days": 0,  
                                        "run_hours": chunk['run_hours'],
                                            "start_year": acc.RepN(chunk['start_date'].strftime('%Y'), n),
                                            "start_month": acc.RepN(chunk['start_date'].strftime('%m'), n),
                                            "start_day": acc.RepN(chunk['start_date'].strftime('%d'), n),
                                            "start_hour": acc.RepN(chunk['start_date'].strftime('%H'), n),
                                            "end_year":  acc.RepN(chunk['end_date'].strftime('%Y'), n),
                                            "end_month": acc.RepN(chunk['end_date'].strftime('%m'), n), 
                                            "end_day":  acc.RepN(chunk['end_date'].strftime('%d'), n), 
                                            "end_hour": acc.RepN(chunk['end_date'].strftime('%H'), n),
                                            "frames_per_outfile": framesperout,
                                            "restart":chunk['restart'],
                                            "restart_interval": restartinterval,
                                            "frames_per_auxhist3": framesperaux}
                                            }

            # Write the namelist 
            template_namelist_input = self.main_run_dirc.joinpath('namelist.input.template')
            namelist_input_quotes = self.wrf_run_dirc.joinpath('namelist.input.quotes')
            namelist_input = self.wrf_run_dirc.joinpath('namelist.input')
            
            # write out namelist files 
            # there does not seem to be a way to write double padded integers using f90nml ... :( 
            f90nml.patch(template_namelist_input, input_patch, namelist_input_quotes)
            acc.RemoveQuotes(namelist_input_quotes, namelist_input)
            
            #run Real for chunk_X
            real_success = self._real()
            if not real_success:  # real worked (or at least returned True)
                self.logger.error('Real failed for chunk {}'.format(num))
                self.logger.error('Check rsl* logs in {}'.format(self.wrf_run_dirc))
                sys.exit()
                
            wrf_success = self._wrf(walltime=walltime_request)
            if not wrf_success:
                self.logger.error('WRF failed for chunk {}'.format(num))
                self.logger.error('Check rsl* logs in {}'.format(self.wrf_run_dirc))
                sys.exit()
            self.logger.info('****Completed Real/WRF Chunk ({}/{})****'.format(num,num_chunks))
        
