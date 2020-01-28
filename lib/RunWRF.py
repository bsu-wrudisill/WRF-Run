import sys
import os
import logging
import pandas as pd
import accessories as acc
from SetMeUp import SetMeUp
import secrets
import f90nml
from math import ceil


class RunWRF(SetMeUp):

    def __init__(self, setup, wps=None, update=None):
        super(self.__class__, self).__init__(setup)
        self.logger = logging.getLogger(__name__)
        self.logger.info('Entering RunWRF')
        # OPTIONAL: Pass in a WPS instance
        # and read stuff from it. Get latest
        # WPS state. The internal WPS checks
        # should say that WPS is good-to-go
        # The latest date information should
        # should also be present
        if wps is not None:
            self.InheritWPS(wps)
        else:
            self.logger.info('No WPS instance inherited')
        
        # update the run directory if a 'location' is provided 
        
        if update: 
            self._SetMeUp__update(**update)
        # Divide up the run into sections
        self.RunDivide()
        self.logger.info('Main Run Directory: {}'.format(self.wrf_run_dirc)) 
        
        # these are the restart files that should be created by this wrf process
        self.final_rst_files = ['wrfrst_d02_{}'.format(self.end_date.strftime(self.time_format)),
                                'wrfrst_d01_{}'.format(self.end_date.strftime(self.time_format))]
        

        # list the WRF files that will be created  
        wrf_file_list = []
        
        # TODO: !!!!!!!THIS DOES NOT WORK FOR ALL OUTPUT TIMESTEPS!!!!!!
        date_range = pd.date_range(self.start_date, self.end_date, freq='1D')
        date_range = date_range.strftime("%Y-%m-%d_%H:00:00")
        for d in range(self.num_wrf_dom):
            for date in date_range:
                wrf_name = self.output_format.format(d+1, date)
                wrf_file_list.append(wrf_name)
        
        # make wrf file list available elsewhere
        self.wrf_file_list = wrf_file_list 
   

    def InheritWPS(self, wps, ):
        # !!!!!!!! THIS SEEMS A BIT ODD !!!!!!!!!!!!
        # update current state
        self.start_date = wps.start_date
        self.end_date = wps.end_date
        self.main_run_dirc = wps.main_run_dirc
        #self._SetMeUp__update(self.main_run_dirc)
        
        # new state
        self.WRFready = wps.WRFready
        self.wps = wps

    def RunDivide(self, **kwargs):
        '''
        Divide up the run into the correct size of 'chunks'. (We don't want to
        run WRF in one continuous run-- that is too much time on the scheduler
        most likely...). Use logic to figure out the amount of walltime to
        request.

        :type       kwargs: start_date (str)
                            end_date: (str)
                            chunk_size: (int)
        '''
        # Read in the kwargs and assign optional values
        start_date = acc.DateParser(kwargs.get('start_date', self.start_date))
        end_date = acc.DateParser(kwargs.get('end_date', self.end_date))
        temporary_chunk_size = self.wrf_run_options['chunk_size']
        chunk_size = kwargs.get('chunk_size', temporary_chunk_size)

        # Get the start/end dates
        zippedlist = list(acc.DateGenerator(start_date, end_date, chunk_size))
        chunk_tracker = []
        # Log things
        self.logger.info('WRF start date: %s', self.start_date)
        self.logger.info('WRF end date: %s', self.end_date)
        self.logger.info('WRF chunk time: %s days', chunk_size)
        self.logger.info('WRF number of chunks: %s', len(zippedlist))

        # Loop through the list of dates and create chunking dictionary
        for i, dates in enumerate(zippedlist):
            # Calculate the lenght of the chunk
            chunk_start = dates[0]
            chunk_end = dates[1]

            # Get hrs/days from length, compute hours
            _cdays_to_hrs = (chunk_end - chunk_start).days*24
            _cdays_to_sec = (chunk_end - chunk_start).seconds/3600
            chunk_hours = _cdays_to_hrs + _cdays_to_sec

            # determine if the initial run is a restart:
            if i == 0:
                # check if the 'restart' flag exists in the setup, and 
                # verify that the restart file lives in the correct spot 
                restart = self.restart  # should be true or false
                
                #check that the restart files exist in the run directory...
                #TODO 
            else:
                restart = True
            
            # write out some useful information
            log_message_template = 'Chunk {}:{}->{}({}hrs). Restart:{}'
            log_message = log_message_template.format(i,
			                              chunk_start,
                                                      chunk_end,
                                                      chunk_hours,
                                                      restart)
            self.logger.info(log_message)
            
            # Create the wall time string -- no need to EVER ask for less than
            # an hour of wall time. Only whole hours allowed.
            # Get the rate value from the setup parameters
            time_rate = self.wrf_run_options['wall_time_per_hour']
            # rounds up -- minumum is 1 hour
            wall_hours = ceil(chunk_hours*time_rate)
            wall_hours_format = "{}:00:00"

            walltime_request = wall_hours_format.format(wall_hours)
            # assign things to the dictionary
            chunk = {'start_date': chunk_start,  # timestamp obj
                     'end_date': chunk_end,      # timestamp obj
                     'run_hours': int(chunk_hours),
                     'restart': restart,
                     'walltime_request': walltime_request}
            # assign to the list
            chunk_tracker.append(chunk)
        # assign chunk list to self
        self.chunk_tracker = chunk_tracker
    
    def PreCheck(self, **kwargs):
        """
        Based on the start:end date and other parameters... check that the
        required geogrid and metgrid files are found in the directory of your
        choosing. This can be used to search for files from the WPS directory
        before linking them over, or to pre-check the WRF directrory before
        submitting a run.

        :param      kwargs:  'geo_dirc':<filepath>
                             'met_dirc':<filepath>
        :type       kwargs:  str or pathlib.path

        :returns:   Dictioanary with the status of the seach
        :rtype:     { return_type_description }
        """

        geo_dirc = kwargs.get('geo_dirc', self.geo_run_dirc)
        met_dirc = kwargs.get('met_dirc', self.met_run_dirc)

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
        # Create list of the required dates
        # TODO:Check on metgrid freq (3H); what controls this???
        date_range = pd.date_range(self.start_date, self.end_date, freq='3H')

        met_format = 'met_em.d0{}.{}-{}-{}_{}:00:00.nc'
        required_met_files = []

        # Number of wrf_domains# number of wrf_domains
        for i in range(n):
            for date in date_range:
                y = date.strftime('%Y')
                m = date.strftime('%m')
                d = date.strftime('%d')
                h = date.strftime('%H')
                required_met_files.append(met_format.format(i+1, y, m, d, h))

        # Assign the 'required met files' to self
        # (why do this, but return the found status (and not assign to self?))
        # (can't exactly say why...)

        # Check if the required metgrid files exist in the metgrid directory
        met_found, met_message = acc.file_check(required_met_files,
                                                met_dirc,
                                                desc='MetgridFiles')
        # create status and return
        status = {'geo': [geo_found, geo_message, required_geo_files],
                  'met': [met_found, met_message, required_met_files]}
        
        # look for the RESTART FILES, if they exist 
        #  TODO 


        return status

    def SetupRunFiles(self, **kwargs):
        ''' kwargs:
              1) start_date
              2) end_date
              3) met_dirc   (location of metfiles. str or posixPath)
        '''
        status = self.PreCheck(geo_dirc=self.geo_run_dirc,
                               met_dirc=self.met_run_dirc)

        met_found, met_message, required_met_files = status['met']
        geo_found, geo_message, required_geo_files = status['geo']

        # Link appropriate files
        # ---------------------
        # Symlinks in the destination directory will be overwritten
        if met_found and geo_found:
            self.logger.info('Found required geogrid and metgrid files')

            self.logger.info('Symlinking geo and metfiles to {}'.format(
                             self.wrf_run_dirc))

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
            # done if
            self.logger.info('****Success********')

        # Either met or geo are NOT found. Both cases are fatal
        # (but we want to know status of both anyways)
        else:
            if not geo_found:
                self.logger.error('geog files not found: {}'.format(
                                   self.geo_run_dirc))
                self.logger.error(geo_message)
            if not met_found:
                self.logger.error('met files not found: {}'.format(
                                   self.met_run_dirc))
                self.logger.error(met_message)
            self.logger.error('Required met/geo files not found.\nExiting')
            sys.exit()
        
        if self.restart:
            logger.info('Restart run... search for appropriate restart files:')
            rest_found, rest_message = acc.file_check(self.rst_files,
                                                      self.wrf_run_dirc)
            if rest_found:
                self.logger.info('Found appropriate restart files')
            else:
                self.logger.error(rest_message)
                sys.exit()            
                                                     
    def CheckOut(self):
        # Verify that the WRF run finished correctly. 
        # DO NOT MOVE FILES ANYWHERE. 
        # This should be done outside of the main 'wrf run' 
        # script, I would argue. 
        

        # flags for success/failure... 
        wrfout_success = False 
        restart_success = False 
        
        # --- look for WRFOUT FILES ---
        self.logger.info('Looking for wrfout files...')
        found_files, message = acc.file_check(self.wrf_file_list, self.wrf_run_dirc)
        if found_files:
            self.logger.info(message)
            wrfout_success = True
        else:
            self.logger.error(message)
        
        # --- look for the final RESTART FILES---
        self.logger.info('Looking for final restart files:\n{}'.format(self.final_rst_files)) 
        found_files, message = acc.file_check(self.final_rst_files, self.wrf_run_dirc)
        if found_files:
            self.logger.info(message)
            restart_success = True
        else:
            self.logger.error(message)
        
        # Continue doing stuff if all of the files have been found  
        if wrfout_success and restart_success:
            return True
        else:
            return False 

    def _real(self, **kwargs):
        """
        Runs real.exe. Does NOT create the appropriate namelist file for the
        run. This is to be done elsewhere. It does write out a submission
        script, however.

        :param      kwargs:  The keywords arguments
        :type       kwargs:  dictionary

        :returns:   { description_of_the_return_value }
        :rtype:     { return_type_description }
        """
        self.logger.info('starting real')

        # 0/xxx Check that a namelist exists (does not update namelists)
        namelist = self.wrf_run_dirc.joinpath('namelist.input')
        if namelist.is_file():
            self.logger.info('Found {}. Continuing'.format(namelist))
        else:
            self.logger.error('No namelist.input found in {}'.format(
                               namelist.parent()))
            self.logger.error('Exit.')
            raise FileNotFoundError

        # 1/xxx Gather/create parameters
        queue = kwargs.get('queue', self.queue)
        qp = kwargs.get('queue_params', self.queue_params.get('real'))

        # create random name for the queue
        unique_name = "r_{}".format(secrets.token_hex(2))
        success_message = "real_em: SUCCESS COMPLETE REAL_EM INIT"
        real_log = self.wrf_run_dirc.joinpath('rsl.out.0000')

        # 2/xxx Create the REAL job submission script
        submit_script = self.wrf_run_dirc.joinpath('submit_real.sh')

        # Form the command
        lines = ["source %s" % self.environment_file,
                 "cd %s" % self.wrf_run_dirc,
                 "./real.exe &> real.catch"]

        command = "\n".join(lines)  # create a single string separated by space

        # create the run script based on the type of job scheduler system
        replacedata = {"QUEUE": queue,
                       "JOBNAME": unique_name,
                       "LOGNAME": "real",
                       "CMD": command,
                       "RUNDIR": str(self.wrf_run_dirc)
                       }
        # write the submit script
        acc.WriteSubmit(qp, replacedata, submit_script)

        # 3/xxx Submit the Job and wait for completion
        jobid, error = acc.Submit(submit_script, self.scheduler)
        # wait for the job to complete
        acc.WaitForJob(jobid, self.user, self.scheduler)

        # 4/xxx check that the job completed correctly
        success, status = acc.log_check(real_log,
                                        success_message,
                                        logger=self.logger)
        if success:
            return True

        if not success:
            self.logger.error('Real.exe did not finish successfully.\nExiting')
            self.logger.error('check {}/rsl.error* for details...')
            self.logger.error(self.wrf_run_dirc)
            return False

    def _wrf(self, **kwargs):
        """
        This function ONLY: runs WRF and waits for it to complete! It does NOT
        setup the namelist.input.Namelist setup must be done elsewhere. It
        writes the submit script, however. Which is why the walltime gets
        passed in as a kwarg. I suppose that it could read the namelist.input
        and figure out the correct walltime to write... but that's too much
        weird logic

        :type       kwargs:  walltime
        :param      kwargs:  The keywords arguments

        :returns:   { description_of_the_return_value }
        :rtype:     { return_type_description }
        """
        self.logger.info('starting wrf')

        # 0/xxx Check that a namelist exists
        namelist = self.wrf_run_dirc.joinpath('namelist.input')
        if namelist.is_file():
            self.logger.info('Found {}. Continuing'.format(namelist))
        else:
            self.logger.error('No namelist.input found in {}'.format(
                               namelist.parent()))
            raise FileNotFoundError

        # 1/xxx Gather/create parameters
        queue = kwargs.get('queue', self.queue)
        qp = kwargs.get('queue_params', self.queue_params.get('wrf'))
        # Walltime gets passed into the submission bash script. Important
        walltime = kwargs.get("walltime", "05:00:00")

        # names,logs etc.
        unique_name = "w_{}".format(secrets.token_hex(2))
        success_message = "wrf: SUCCESS COMPLETE WRF"
        wrf_log = self.wrf_run_dirc.joinpath('rsl.out.0000')

        # 2/xxx Create the REAL job submission script
        submit_script = self.wrf_run_dirc.joinpath('submit_wrf.sh')

        # Form the command
        lines = ["source %s" % self.environment_file,
                 "cd %s" % self.wrf_run_dirc,
                 "mpirun ./wrf.exe &> wrf.catch"]
        command = "\n".join(lines)  # create a single string separated by space

        # create the run script based on the type of job scheduler system
        replacedata = {"QUEUE": queue,
                       "JOBNAME": unique_name,
                       "LOGNAME": "wrf",
                       "WALLTIME": walltime,
                       "CMD": command,
                       "RUNDIR": str(self.wrf_run_dirc)
                       }

        # write the submit script
        acc.WriteSubmit(qp, replacedata, submit_script)

        # 3/xxx Submit the Job and wait for completion
        jobid, error = acc.Submit(submit_script, self.scheduler)

        # wait for the job to complete
        acc.WaitForJob(jobid, self.user, self.scheduler)

        # 4/xxx check that the job completed correctly
        success, status = acc.log_check(wrf_log,
                                        success_message,
                                        logger=self.logger)
        if success:
            return True
        if not success:
            self.logger.error('Wrf.exe did not finish successfully.\nExiting')
            self.logger.error('check {}/rsl.error* for details')
            self.logger.error(self.wrf_run_dirc)
            return False

    def WRF_TimePeriod(self, **kwargs):
        '''
        Run WRF and Real
        :type       kwargs:  dictionary
        :param      kwargs:  The keywords arguments
        '''
	# Create CSV file with all of the expected WRF files and restarsts
	# TODO:

        open_message = '****Starting Real/WRF Chunk ({}/{})****'
        # Number of chunks
        num_chunks = len(self.chunk_tracker)
        for num, chunk in enumerate(self.chunk_tracker):
            self.logger.info(open_message.format(num, num_chunks))
            self.logger.info(self.wrf_run_dirc)
            self.logger.info('restart={}'.format(chunk['restart']))
            # restart interval is always the chunk length 
            restartinterval = str(chunk['run_hours']*60)
            if chunk['run_hours'] < 24:
                framesperout = chunk['run_hours']
                framesperaux = str(24)
            # is this sufficient logic? I think so...
            else:
                framesperout = str(24)
                framesperaux = str(24)
            
            walltime_request = str(chunk['walltime_request'])
            n = self.num_wrf_dom
            # TODO: create a chunk class where the strings formatting
            # is a method.. This is Gnar...
            # update starting dates
            input_patch = {"time_control":
                           {"run_days": 0,
                            "run_hours": chunk['run_hours'],
                            "start_year": acc.RepN(chunk['start_date'].strftime('%Y'), n),
                            "start_month": acc.RepN(chunk['start_date'].strftime('%m'), n),
                            "start_day": acc.RepN(chunk['start_date'].strftime('%d'), n),
                            "start_hour": acc.RepN(chunk['start_date'].strftime('%H'), n),
                            "end_year":  acc.RepN(chunk['end_date'].strftime('%Y'), n),
                            "end_month": acc.RepN(chunk['end_date'].strftime('%m'), n),
                            "end_day":  acc.RepN(chunk['end_date'].strftime('%d'), n),
                            "end_hour": acc.RepN(chunk['end_date'].strftime('%H'), n),
                            "frames_per_outfile": acc.RepN(framesperout, n),
                            "restart": chunk['restart'],
                            "restart_interval": acc.RepN(restartinterval, 1),
                            "frames_per_auxhist3": acc.RepN(framesperaux, n)}
                           }

            # Write the namelists.input...
            mrd = self.main_run_dirc
            wrd = self.wrf_run_dirc
            template_namelist_input = mrd.joinpath('namelist.input.template')
            namelist_input_quotes = wrd.joinpath('namelist.input.quotes')
            namelist_input = wrd.joinpath('namelist.input')

            # Write out namelist files
            # there does not seem to be a way to write double padded
            # integers using f90nml, which is why we do this ....
            f90nml.patch(template_namelist_input,
                         input_patch,
                         namelist_input_quotes)
            # And... remove all of the quotes.
            acc.RemoveQuotes(namelist_input_quotes,
                             namelist_input)

            # !Run Real!
            real_success = self._real()
            if not real_success:  # real worked (or at least returned True)
                self.logger.error('Real failed for chunk {}'.format(num))
                self.logger.error('Check rsl* logs in {}'.format(wrd))
                sys.exit()
            else:
                self.logger.info("Real Success for chunk {}".format(num))

            # !Run WRF!
            wrf_success = self._wrf(walltime=walltime_request)
            if not wrf_success:
                self.logger.error('WRF failed for chunk {}'.format(num))
                self.logger.error('Check rsl* logs in {}'.format(wrd))
                sys.exit()
            else:
                self.logger.info("WRF Success for chunk {}".format(num))

    def move_files():
        # Move the files to the final location... wherever that may be 
        #
        pass





