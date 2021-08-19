import sys
import os
import datetime
import logging
import pandas as pd
import accessories as acc
#from SetMeUp import SetMeUp
from RunWPS import RunWPS
from RunWRF import RunWRF
import secrets
import f90nml   # this must be installed via pip ... ugh
import shutil

class RunNDown(RunWPS, RunWRF):
    """
    We get to use all of the RunWPS functions in addition to the RunWRF Funtcions!!
    """

    def start(self):
        self.logger.info('Main Run Directory: {}'.format(self.main_run_dirc))
        self.use_ndown()
        #self.createRunDirectory()

    def _ndown_pre_checks(self):
        assert self.parent_grid_wrf.is_directory(), 'Parent wrf directory not found. Exit'

        # find the wrf files...
        #wrf_files = self.parent_grid_wrf.joinpath('wrf')
        #for wf in wrf_files.glob('wrfout_d01*'):
            # make sure they are all there...

    def createRunDirectory(self):
        # copy contents of the 'WRFVX/run' directory to the main run dir
        self.main_run_dirc.mkdir(parents=True, exist_ok=True)

        # Self.wrf_run_dirc.mkdir()
        shutil.copytree(self.wrf_exe_dirc.joinpath('run'),
                        self.wrf_run_dirc, symlinks=True)

        # make directories
        self.wps_run_dirc.mkdir()
        self.geo_run_dirc.mkdir()
        self.met_run_dirc.mkdir()
        self.ndown_run_dirc.mkdir()

        # NAMELIST.INPUT
        shutil.copy(self.input_namelist_path,
                    self.main_run_dirc.joinpath('namelist.input.template'))

        shutil.copy(self.wps_namelist_path,
                    self.main_run_dirc.joinpath('namelist.wps.template'))

        shutil.copy(self.input_namelist_inner,
                    self.main_run_dirc.joinpath('namelist.input.template_inner'))

        #!!!  We actually do not need this !!!
        #shutil.copy(self.wps_namelist_inner,
        #            self.main_run_dirc.joinpath('namelist.wps.template_inner'))

        # Copy real.exe to the ndown directory
        shutil.copy(self.wrf_exe_dirc.joinpath('run', 'real.exe'), self.ndown_run_dirc)
        shutil.copy(self.wrf_exe_dirc.joinpath('run', 'ndown.exe'), self.ndown_run_dirc)

        # Copy METGRID
        shutil.copy(self.met_exe_dirc.joinpath('metgrid.exe'),
                    self.met_run_dirc)
        shutil.copy(self.met_exe_dirc.joinpath('METGRID.TBL'),
                    self.met_run_dirc)

        # Copy geogrid files
        shutil.copy(self.geo_exe_dirc.joinpath('geogrid.exe'),
                    self.geo_run_dirc)
        shutil.copy(self.geo_exe_dirc.joinpath('GEOGRID.TBL'),
                    self.geo_run_dirc)

        # Copy the environment file
        shutil.copy(self.environment_file,
                    self.main_run_dirc)

        # Copy the configure scripts  ### !!!! DANGER !!!! cwd #####
        shutil.copytree(self.cwd.joinpath('user_config'),
                        self.main_run_dirc.joinpath('user_config'))

        '''
        Copy the d01 (parent grid) WRF files to a safe place
        '''
        # Find the correct WRF files
        wfl, rl = self.expected_wrf_files(1, self.start_date, self.end_date)
        wfl_full_path = [self.ndown_wrf_parent_files.joinpath(x) for x in wfl]

        # Link the files
        for src in wfl_full_path:
            name = src.name
            dst = self.ndown_run_dirc.joinpath(name)
            self.logger.info("symlinking parent domain wrf files...")
            #self.logger.info('%s --> %s' % (src, dst))
            os.symlink(src, dst)


        # if hydro flag is on....
        if self.hydro_flag:
            self.logger.info("WRF Hydro Coupling == True")

            # Create folder for geog information
            domain = self.main_run_dirc.joinpath("Domain")
            domain.mkdir()
            for src_whf in self.wrf_hydro_basin_files.glob('*'):

                dst_whf = domain.joinpath(src_whf.name)

                if dst_whf.is_file():
                    os.unlink(dst_whf)
                self.logger.info("%s --> %s"%(src_whf,dst_whf))
                os.symlink(src_whf, dst_whf)

            # Copy the hdyro.namelist file
            dst_hydro_namelist = self.main_run_dirc.joinpath(self.hydro_namelist_file.name)
            shutil.copy(self.hydro_namelist_file, dst_hydro_namelist)
        else:
            self.logger.info("WRF Hydro Coupling == False")

        # Get the restart file if it is called for
        if self.restart:
            # 1. Look for restart files in the wrf directory
            self.logger.info('Restart run... search for appropriate restart files:')
            rest_found, rest_message = acc.file_check(self.rst_files,
                                                      self.wrf_run_dirc)
            if rest_found:
                self.logger.info('Found restart files in wrf run directory')

            else:
                # 2. look for restart files in the parent restart directory.
                rest_found, rest_message = acc.file_check(self.rst_files,
                                                          self.restart_directory)

                # copy them over if they have been found
                if rest_found:
                    for rst in self.rst_files:
                        self.logger.info('Copying the following restart files...')
                        self.logger.info(rst)
                        self.logger.info('{} --> {}'.format(self.restart_directory, self.wrf_run_dirc))
                        shutil.copy(self.restart_directory.joinpath(rst), self.wrf_run_dirc)
                else:
                    self.logger.error('Did not location restart files in {}'.format(self.restart_directory))
                    self.logger.error(rest_message)
                    sys.exit()

        else:
            self.logger.info('No restart files are requested')



    '''
    def geogrid(): ....

        doesn't need to do anyhing different than RunWPS.geogrid !!



    def metgrid(): ....

        same! we can simply call the metgrid function defined in RunWPS

    '''

    def _ndown(self, directory):
        """Summary
        1) Run real.exe to create wrfinput files
        2) Run ndown.exe to create LBC conditions (wrfbdy files)
           Do this in 'one fell swoop' for all LBC files...
        """

        self.logger.info('starting ndown')

        # 0/xxx Check that a namelist exists (does not update namelists)
        namelist = directory.joinpath('namelist.input')
        if namelist.is_file():
            self.logger.info('Found {}. Continuing'.format(namelist))
        else:
            self.logger.error('No namelist.input found in {}'.format(
                namelist.parent()))
            self.logger.error('Exit.')
            raise FileNotFoundError

        # Check for wrfbdy_d01 and wrfndi_d02 ??
        ndi_file = directory.joinpath('wrfndi_d02')
        if ndi_file.is_file():
            self.logger.info('Found {}. Continuing'.format(ndi_file))
        else:
            raise FileNotFoundError

        # 1/xxx Gather/create parameters
        queue = self.queue
        qp = self.queue_params.get('real')  # NOT AN ERROR. Just use the real params for now

        # create random name for the queue
        unique_name = "n_{}".format(secrets.token_hex(2))
        success_message = "ndown_em: SUCCESS COMPLETE NDOWN_EM INIT"
        ndown_log = directory.joinpath('rsl.out.0000')

        # 2/xxx Create the REAL job submission script
        submit_script = directory.joinpath('submit_ndown.sh')

        # Form the command
        lines = ["source %s" % self.environment_file,
                 "cd %s" % directory,
                 "./ndown.exe &> real.catch"]

        command = "\n".join(lines)  # create a single string separated by space

        # create the run script based on the type of job scheduler system
        replacedata = {"QUEUE": queue,
                       "JOBNAME": unique_name,
                       "LOGNAME": "ndown",
                       "CMD": command,
                       "RUNDIR": str(directory)
                       }

        # write the submit script
        acc.WriteSubmit(qp, replacedata, submit_script)

        # 3/xxx Submit the Job and wait for completion
        jobid, error = acc.Submit(submit_script, self.scheduler)

        # wait for the job to complete
        acc.WaitForJob(jobid, self.user, self.scheduler)

        # 4/xxx check that the job completed correctly
        success, status = acc.log_check(ndown_log,
                                        success_message,
                                        logger=self.logger)
        if success:
            return True

        if not success:
            self.logger.error('ndown.exe did not finish successfully.\nExiting')
            self.logger.error('check {}/rsl.error* for details...')
            self.logger.error(directory)
            return False
        # Link the appropraite WRF files

    def WRF_Ndown_TimePeriod(self, skip_first_real_ndown=False):
        '''
        Run WRF and Real for specified intervals
        '''

        open_message = '****Starting Real/Ndown/WRF Chunk ({}/{})****'

        # Number of chunks
        num_chunks = len(self.chunk_tracker)
        
        # loop through WRF steps...
        for num, chunk in enumerate(self.chunk_tracker):
            
            # create boolean for status of chunks. The first chunk is special.
            if num == 0:
               first_chunk = True
            else:
               first_chunk = False 

            self.logger.info(open_message.format(num, num_chunks))
            self.logger.info(self.wrf_run_dirc)
            self.logger.info('restart={}'.format(chunk['restart']))
                
            # !!!! MAKE THIS MORE DYNAMIC !!!! 
            # !!!! We might want the restart interval to be much less for various reasons !!!
            
            # restart interval is always the chunk length
            #restartinterval = str(chunk['run_hours'] * 60)
            restartinterval = str(1440)

            if chunk['run_hours'] < 24:
                framesperout = chunk['run_hours']
                framesperaux = str(24)
            # is this sufficient logic? I think so...
            else:
                framesperout = str(24)
                framesperaux = str(24)

            walltime_request = str(chunk['walltime_request'])

            # TODO: create a chunk class where the strings formatting
            # is a method.. This is Gnar...
            # update starting dates

            def input_patch(n):
                input_patch = {"time_control":
                               {"run_days": 0,
                                "run_hours": chunk['run_hours'],
                                "start_year": acc.RepN(chunk['start_date'].strftime('%Y'), n),
                                "start_month": acc.RepN(chunk['start_date'].strftime('%m'), n),
                                "start_day": acc.RepN(chunk['start_date'].strftime('%d'), n),
                                "start_hour": acc.RepN(chunk['start_date'].strftime('%H'), n),
                                "end_year": acc.RepN(chunk['end_date'].strftime('%Y'), n),
                                "end_month": acc.RepN(chunk['end_date'].strftime('%m'), n),
                                "end_day": acc.RepN(chunk['end_date'].strftime('%d'), n),
                                "end_hour": acc.RepN(chunk['end_date'].strftime('%H'), n),
                                "frames_per_outfile": acc.RepN(framesperout, n),
                                "restart": chunk['restart'],
                                "restart_interval": acc.RepN(restartinterval, 1),
                                "frames_per_auxhist3": acc.RepN(framesperaux, n),
                                "io_form_auxinput2": 2}
                               }
                return input_patch


            # Write the namelists.input...
            mrd = self.main_run_dirc
            wrd = self.wrf_run_dirc
            nrd = self.ndown_run_dirc

        
            '''
            PART 1:
            Run real + ndown to generatre the wrfbdy and wrfinput files in the ndown directory
            We can skip this, if skip_first_real_ndown == True. In the case that this step went OK,
            but WRF failed for whatever reason, and we don't like waiting...
            '''
            if (skip_first_real_ndown) and (num == 0):
                self.logger.info("Skiping the first ndown step, which has presumably already been run")
            
            else:
                print(num, skip_first_real_ndown)
                template_namelist_input = mrd.joinpath('namelist.input.template')
                namelist_input_quotes = nrd.joinpath('namelist.input.quotes')
                namelist_input = nrd.joinpath('namelist.input')

                # Write out namelist files
                # there does not seem to be a way to write double padded
                # integers using f90nml, which is why we do this ....
                f90nml.patch(template_namelist_input,
                             input_patch(self.num_wrf_dom),
                             namelist_input_quotes)

                # And... remove all of the quotes.
                acc.RemoveQuotes(namelist_input_quotes,
                                 namelist_input)

                # Link the metgrid files !
                self.logger.info('Creating symlink for metgrid...')
                for met in self.met_run_dirc.glob("met_em*"):
                    dst = self.ndown_run_dirc.joinpath(met.name)
                    if dst.is_symlink():
                        dst.unlink()
                    os.symlink(met, dst)

                #! Run Real !
                real_success = self._real(nrd)
                if not real_success:  # real worked (or at least returned True)
                    self.logger.error('Real failed for chunk {}'.format(num))
                    self.logger.error('Check rsl* logs in {}'.format(nrd))
                    sys.exit()
                else:
                    self.logger.info("Real Success for chunk {}".format(num))

                #! Run Ndown !

                # link/rename the wrf_input_d02 file
                src_ndi = nrd.joinpath('wrfinput_d02')
                dst_ndi  = nrd.joinpath('wrfndi_d02')
                self.logger.info('%s --> %s'%(src_ndi,dst_ndi))
                shutil.copyfile(src_ndi, dst_ndi)

                # Add the auxinput line to the namelist
                #patch = {"time_control": {"io_form_auxinput2": 2}}
                #acc.PatchInPlace(namelist_input, patch)

                # run ndown
                ndown_success = self._ndown(nrd)
                if not ndown_success:  # real worked (or at least returned True)
                    self.logger.error('nddown failed for chunk {}'.format(num))
                    self.logger.error('Check rsl* logs in {}'.format(nrd))
                    sys.exit()
                else:
                    self.logger.info("ndown Success for chunk {}".format(num))

            '''
            PART 2:
            Link the appropriate files, namelists, and run WRF
            '''

            # Link over the wrfbdy files from the ndown directory...
            src_wrfbdy = nrd.joinpath('wrfbdy_d02')
            dst_wrfbdy = wrd.joinpath('wrfbdy_d01')

            src_wrfinput = nrd.joinpath('wrfinput_d02')
            dst_wrfinput = wrd.joinpath('wrfinput_d01')

            src_wrflow = nrd.joinpath('wrflowinp_d02')
            dst_wrflow = wrd.joinpath('wrflowinp_d01')

            # unlink files if they exist...
            if dst_wrfbdy.is_symlink():
                dst_wrfbdy.unlink()

            # link the wrfinput file...
            if dst_wrfinput.is_symlink():
                dst_wrfinput.unlink()

            # link the wrflow file...
            if dst_wrflow.is_symlink():
                dst_wrflow.unlink()

            # link the correct files
            os.symlink(src_wrfbdy, dst_wrfbdy)
            os.symlink(src_wrfinput, dst_wrfinput)
            
            # ???? copy this one ... why ???
            shutil.copy(src_wrflow, dst_wrflow)

            # Link the namelist file
            template_namelist_input = mrd.joinpath('namelist.input.template_inner')
            namelist_input_quotes = wrd.joinpath('namelist.input.template_inner.quotes')
            namelist_input = wrd.joinpath('namelist.input')

            # Write out namelist files
            # there does not seem to be a way to write double padded
            # integers using f90nml, which is why we do this ....
            f90nml.patch(template_namelist_input,
                         input_patch(1),
                         namelist_input_quotes)

            # And... remove all of the quotes.
            acc.RemoveQuotes(namelist_input_quotes,
                             namelist_input)


            # !ADJUST THE HYDRO.NAMELIST FILE IF NEEDED !#
            if self.hydro_flag:
                time_format = "%Y-%m-%d_%H:%M:%S"
                if self.hydro_restart_override and first_chunk:
                    hydro_restart = self.hydro_restart_override 
                else:
                    hydro_restart = "./HYDRO_RST.%s_DOMAIN1"%(chunk['start_date'].strftime("%Y-%m-%d_%H:%M"))

                """
                Note that we are not using hte f90 nml package to do this...
                """
                if chunk['restart']:
                    hydro_update = {"RESTART_FILE": "RESTART_FILE = \"%s\"" % hydro_restart,
                                    "GW_RESTART": "GW_RESTART = 1"}

                else:
                    hydro_update = {"RESTART_FILE": "!RESTART_FILE",
                                    "GW_RESTART": "GW_RESTART = 0"}

                # write the file...
                acc.GenericWrite(self.hydro_namelist_file,
                                 hydro_update,
                                 wrd.joinpath('hydro.namelist'))


            # !Run WRF!
            wrf_success = self._wrf(walltime_request)
            if not wrf_success:
                self.logger.error('WRF failed for chunk {}'.format(num))
                self.logger.error('Check rsl* logs in {}'.format(wrd))
                sys.exit()
            else:
                self.logger.info("WRF Success for chunk {}".format(num))
                # now clean up the WRF files ....
                self.clean_wrf_directory()



