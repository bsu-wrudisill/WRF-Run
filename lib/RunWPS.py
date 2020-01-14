import sys
import os
import datetime
import logging
import pandas as pd
import accessories as acc
from SetMeUp import SetMeUp
import secrets
import f90nml   # this must be installed via pip ... ugh


class RunWPS(SetMeUp):
    """
    This class describes run wps.
    """

    def __init__(self, setup, **kwargs):
        '''
        Inherit methods/stuff from SetMeUp (read from main.yml)
        :type       setup:   { type_description }
        :param      setup:   The setup
        :type       kwargs:  dictionary
        :param      kwargs:  The keywords arguments
        '''
        # Get stuff from the SetMeUp __init__
        super(self.__class__, self).__init__(setup)
        self.logger = logging.getLogger(__name__)
        self.logger.info('initialized RunWPS instance')

        # Read in OPTIONAL kwargs
        self.start_date = acc.DateParser(kwargs.get('start_date',
                                                    self.start_date))
        self.end_date = acc.DateParser(kwargs.get('end_date',
                                       self.end_date))
        # Create patch on iniitalization for the namelist
        self.patch()

        # Internal flags
        # Process Completed
        self.WRFready = False

    def patch(self, **kwargs):
        '''
        Create the dictionary with the right terms for updating the wps
        namelist files.

        :type       kwargs:  dictionary
        :param      kwargs:  The keywords arguments
        '''
        self.logger.info('Calling wps.patch()')
        # Get the start/end dates in the right format for WPS namelist
        wps_start_date = self.start_date.strftime(self.time_format)
        wps_end_date = self.end_date.strftime(self.time_format)

        # Get number of domains
        n = self.num_wrf_dom

        # Create a repeated list of start/end dates for namelists
        start_date_rep = acc.RepN(wps_start_date, n)
        end_date_rep = acc.RepN(wps_end_date, n)

        # WPS patch object
        self.wps_patch = {
                          "geogrid": {
                             "opt_geogrid_tbl_path": str(self.geo_exe_dirc),
                             "geog_data_path": str(self.geog_data_path)},
                          "metgrid": {
                             "opt_metgrid_tbl_path": str(self.met_exe_dirc)},
                          "ungrib": {
                             "prefix": "PLEVS"},
                          "share": {
                             "start_date": start_date_rep,
                             "end_date": end_date_rep}
                            }

    def writeNamelist(self, directory, remove_quotes=False):
        """
        Write the WPS namelist into the given directory
        () Adjust parameters in the namelist.wps template script

        :param      directory:      The directory
        :type       directory:      { type_description }
        :param      remove_quotes:  The remove quotes
        :type       remove_quotes:  boolean
        """

        if remove_quotes:
            # Do this whole dumb thing to remove quotes line by line
            template_namelist_wps = self.main_run_dirc.joinpath(
                                        'namelist.wps.template')
            namelist_wps_quotes = directory.joinpath(
                                        'namelist.wps.quotes')
            namelist_wps = directory.joinpath('namelist.wps')

            # Apply the 'patch' to the namelist
            f90nml.patch(template_namelist_wps,
                         self.wps_patch,
                         namelist_wps_quotes)
            # Remove the quotes ...
            acc.RemoveQuotes(namelist_wps_quotes,
                             namelist_wps)

        else:
            # Leave in the quotes ... ugh. For WPS this is ok.
            # Namelist.input, it's not. So dumb...
            template_namelist_wps = self.main_run_dirc.joinpath(
                                        'namelist.wps.template')
            namelist_wps = directory.joinpath('namelist.wps')

            # Update the file
            f90nml.patch(template_namelist_wps,
                         self.wps_patch,
                         namelist_wps)
        # log/record state
        self.logger.info('updated/wrote {}'.format(namelist_wps))
        self.wrote = True

    @acc.timer
    def geogrid(self, **kwargs):
        '''
        kwargs options: 1) 'queue' 2) 'queue_params' 3) 'submit_script'

        :type       kwargs:  dictionary
        :param      kwargs:  The keywords arguments
        '''
        logger = logging.getLogger(__name__)
        logger.info('Entering Geogrid process')

        # Read **kwargs
        queue = kwargs.get('queue', self.queue)
        qp = kwargs.get('queue_params', self.queue_params.get('wps'))
        submit_script = kwargs.get('submit_script',
                                   self.geo_run_dirc.joinpath(
                                           'submit_geogrid.sh')
                                   )

        # update state -- geogrid has been attempted
        self.ran_geogrid = True

        unique_name = "g_{}".format(secrets.token_hex(2))
        geogrid_log = self.geo_run_dirc.joinpath('geogrid.log')
        success_message = "Successful completion of program geogrid.exe"

        # () Write the submission script

        # form the command 
        lines = ["source %s" % self.environment_file,
                 "cd %s" % self.geo_run_dirc,
                 "./geogrid.exe &> geogrid.catch"]

        command = "\n".join(lines)  # create a single string separated by space

        # create the run script based on the type of job scheduler system
        replacedata = {"QUEUE": queue,
                       "JOBNAME": unique_name,
                       "LOGNAME": "geogrid",
                       "CMD": command,
                       "RUNDIR": str(self.geo_run_dirc)
                       }

        acc.WriteSubmit(qp, replacedata, str(submit_script))

        #  Adjust parameters in the namelist.wps template script
        self.writeNamelist(self.geo_run_dirc)

        # () Job Submission
        # Navigate to the run directory
        jobid, error = acc.Submit(submit_script, self.scheduler)

        # Wait for the job to complete
        acc.WaitForJob(jobid, self.user, self.scheduler)  # CHANGE_ME

        # () Check Job Completion
        # --------------------
        success, status = acc.log_check(geogrid_log, success_message)
        if success:
            logger.info(status)
        if not success:
            logger.error(status)
            logger.error("check {}".format(self.geo_run_dirc))
            sys.exit()

    # @acc.timer
    # def new_ungrib(self):
    #     logger = logging.getLogger(__name__)
    #     logger.info('entering Ungrib process in directory')
    #     logger.info('WRF Version {}'.format(self.wrf_version))

    #     # read the ungrub config file
    #     with open(self.)

    @acc.timer
    def ungrib(self, **kwargs):
        '''
        Run the ungrib.exe program
        kwargs:
            1) queue
            2) queue_params
            3) submit_script
            # Defaults to the options found in 'self')
        '''
        # Start logging
        logger = logging.getLogger(__name__)
        logger.info('entering Ungrib process in directory')
        logger.info('WRF Version {}'.format(self.wrf_version))

        # update state --attempted
        self.ran_ungrib = True

        # Read **kwargs
        queue = kwargs.get('queue',
                           self.queue)

        qp = kwargs.get('queue_params',
                        self.queue_params.get('wps'))

        submit_script = kwargs.get('submit_script',
                                   self.ungrib_run_dirc.joinpath(
                                              'submit_ungrib.sh'))

        # Fixed paths -- these should get created
        cwd = os.getcwd()
        vtable = self.ungrib_run_dirc.joinpath('Vtable')
        ungrib_log = self.ungrib_run_dirc.joinpath('ungrib.log')
        linkGrib = '{}/link_grib.csh {}/{}'
        unique_name = 'u_{}'.format(secrets.token_hex(2))
        success_message = 'Successful completion of program ungrib.exe'

        # Form the job submission command
        lines = ["source %s" % self.environment_file,
                 "cd %s" % self.ungrib_run_dirc,
                 "./ungrib.exe &> ungrib.catch"]

        command = "\n".join(lines)  # create a single string separated by space

        # (XXX/NNN) Update namelist.wps script and write to directory

        replacedata = {"QUEUE": queue,
                       "JOBNAME": unique_name,
                       "LOGNAME": "ungrib-PLEVS",
                       "CMD": command,
                       "RUNDIR": str(self.ungrib_run_dirc)
                       }

        # Write the namelist.wps
        self.writeNamelist(self.ungrib_run_dirc)

        # (XXX/NNN)Symlink the vtables (check WRF-Version)
        # Different versions of WRF have differnt Vtables even for the same LBC

        # WRF V 4.0++
        if str(self.wrf_version) == '4.0':
            _message = 'Running WRF Version {} ungrib for {}'
            _message = _message.format(self.wrf_version, self.lbc_type)
            logger.info(_message)

            # There is only one vtable for wrf 4.0... I think?? for CFSR
            required_vtable = self.ungrib_run_dirc.joinpath(
                               'Variable_Tables/Vtable.CFSR')

            if not required_vtable.exists():
                _errormessage = 'variable table {} not found. exiting'
                _errormessage.format(required_vtable)
                logger.error(_errormessage)
                sys.exit()
            # Check if the required vtable exists -- unlink if so
            if vtable.exists():
                os.unlink(vtable)
            os.symlink(required_vtable, vtable)

        # WRF V 3.8.1
        elif str(self.wrf_version) == '3.8':
            required_vtable_plv = self.ungrib_run_dirc.joinpath('Variable_Tables/Vtable.CFSR_press_pgbh06')
            required_vtable_flx = self.ungrib_run_dirc.joinpath('Variable_Tables/Vtable.CFSR_sfc_flxf06')
            required_vtables = [required_vtable_plv.exists(), required_vtable_flx.exists()]

            if False in required_vtables:
                logger.error('WRF {} variable table {} not found. exiting'.format(self.wrf_version, required_vtables))
                sys.exit()
            os.symlink(required_vtable_plv, vtable)
        # Other WRF Version (Catch this error earlier!!)
        else:
            logger.error('unknown wrf version {}'.format(self.wrf_version))
            sys.exit()

        # (XXX/NNN) Begin Ungrib (2 parts--Plevs and SFLUX (FOR CFSR))
        # Ungrib the Pressure Files (PLEVS) first
        logger.info('Starting on PLEVS (1/2)')

        # issue the link command
        os.chdir(self.ungrib_run_dirc)
        acc.SystemCmd(linkGrib.format(self.ungrib_run_dirc, self.data_dl_dirc, 'pgbh06'))
        os.chdir(cwd)

        # Create the submit script, link grib files
        acc.WriteSubmit(qp, replacedata, submit_script)

        # Pressure files job submission
        jobid, error = acc.Submit(submit_script,
                                  self.scheduler)
        acc.WaitForJob(jobid,
                       self.user,
                       self.scheduler)

        # Verify the completion of .1
        success, status = acc.log_check(ungrib_log, success_message)
        if success:
            logger.info(status)

        if not success:
            logger.error(status)
            logger.error("Ungrib PLEVS step (1/2) did not finish correctly. Exiting")
            logger.error("check {}".format(self.ungrib_run_dirc))
            sys.exit()

        # Clean up .1
        globfiles = self.ungrib_run_dirc.glob('GRIBFILE*')
        for globfile in globfiles:
            logger.debug('unlinked {}'.format(str(globfile)))
            os.unlink(globfile)

        # (XXX/NNN.2) Ungrib the Surface Flux files (SFLUX)
        logger.info('Starting on SFLUX (2/2)')

        # We need to switch vtables if we are using 3.8.1
        if self.wrf_version == '3.8':
            os.unlink('unlink plevs vtable; link flx vtable')
            os.symlink(required_vtable_flx, vtable)

        # Update Dictionaries -- regardless of wrf versio we do this
        replacedata['LOGNAME'] = "ungrib-SFLUX"

        # Write the submit script
        acc.WriteSubmit(qp, replacedata, filename=submit_script)

        # Switch the ungrib prefix--PLEVS --> SFLUX
        self.wps_patch['ungrib']['prefix'] = "SFLUX"

        # Patch the file, rewriting the old one 
        self.writeNamelist(self.ungrib_run_dirc)

        # Link SFLXF files
        os.chdir(self.ungrib_run_dirc)
        acc.SystemCmd(linkGrib.format(self.ungrib_run_dirc,
                                      self.data_dl_dirc,
                                      'flxf06')
                      )
        os.chdir(cwd)

        # Submit the job
        jobid, error = acc.Submit(submit_script,
                                  self.scheduler)
        acc.WaitForJob(jobid,
                       self.user,
                       self.scheduler)

        # (XXX/NNN) Verify completion
        success, status = acc.log_check(ungrib_log, success_message)
        if success:
            logger.info(status)
        if not success:
            logger.error(status)
            logger.error("Ungrib SFLUX step (2/2) did not finish correctly. Exiting")
            logger.error("check {}".format(self.ungrib_run_dirc))
            sys.exit()

        # cleanup
        globfiles = self.ungrib_run_dirc.glob('GRIBFILE*')
        for globfile in globfiles:
            logger.debug('unlinked {}'.format(str(globfile)))
            os.unlink(globfile)
        # check that the script finished correctly
        os.chdir(cwd)

    @acc.timer
    def metgrid(self, **kwargs):
        """
        ungrib_location: (path to SFLUX/PLEVS files)
        geogrid_location: (path to geo_em* files)
        --force: whether or not to clean out the metgrid directory or not
        :param      kwargs:  The keywords arguments
        :type       kwargs:  dictionary
        """
        logger = logging.getLogger(__name__)
        logger.info('entering metgrib process in directory')
        logger.info('WRF Version {}'.format(self.wrf_version))

        # Update state
        self.ran_metgrid = True

        # What do I do w/ old met files?
        # Whether or not to 'clean' the dir before running
        # !clean = kwargs.get('force', True)  # UNUSED

        # Fixed paths -- these should get created
        metgrid_log = self.met_run_dirc.joinpath('metgrid.log')
        unique_name = 'm_{}'.format(secrets.token_hex(2))
        success_message = 'Successful completion of program metgrid.exe'

        # link ungrib files
        logger.info('Creating symlink for SFLUX')
        for sflux in self.ungrib_run_dirc.glob('SFLUX*'):
            dst = self.met_run_dirc.joinpath(sflux.name)
            if dst.is_symlink():
                dst.unlink()
            os.symlink(sflux, dst)

        logger.info('Creating symlink for PLEVS')
        for plevs in self.ungrib_run_dirc.glob('PLEVS*'):
            dst = self.met_run_dirc.joinpath(plevs.name)
            if dst.is_symlink():
                dst.unlink()
            os.symlink(plevs, dst)

        # link geogrid files TODO: how many geogrid are needed???
        for geo_em in self.geo_run_dirc.glob('geo_em.d0?.nc'):
            dst = self.met_run_dirc.joinpath(geo_em.name)
            if dst.is_symlink():
                dst.unlink()
            os.symlink(geo_em, dst)

        # Get pbs submission parameters and create submit command
        queue = kwargs.get('queue', self.queue)                        # get the queue
        qp = kwargs.get('queue_params', self.queue_params.get('wps'))  # get the submit parameters
        submit_script = self.met_run_dirc.joinpath('submit_metgrid.sh')

        # Form the job submission command
        lines = ["source %s" % self.environment_file,
                 "cd %s" % self.met_run_dirc,
                 "./metgrid.exe &> metgrid.catch"]
        command = "\n".join(lines)  # create a single string separated by spaces

        # Create the run script based on the type of job scheduler system
        replacedata = {"QUEUE": queue,
                       "JOBNAME": unique_name,
                       "LOGNAME": "metgrid",
                       "CMD": command,
                       "RUNDIR": str(self.met_run_dirc)
                       }
        # write the submit script
        acc.WriteSubmit(qp, replacedata, str(submit_script))

        # Adjust parameters in the namelist.wps template script
        # ----------------------------------------------------
        self.writeNamelist(self.met_run_dirc)

        # Submit the job and wait for completion
        # --------------------------------------
        jobid, error = acc.Submit(submit_script, self.scheduler)
        acc.WaitForJob(jobid, self.user, self.scheduler)

        # Verify completion
        # -----------------
        success, status = acc.log_check(metgrid_log, success_message)
        if success:
            logger.info(status)
        if not success:
            logger.error(status)
            logger.error("check {}".format(self.met_run_dirc))
            sys.exit()

    @acc.timer
    def dataDownload(self):
        """
        { function_description }

        :returns:   { description_of_the_return_value }
        :rtype:     { return_type_description }
        """
        logger = logging.getLogger(__name__)
        logger.info('beginning data download')

        # update state
        self.ran_dl = True

        sub6 = datetime.timedelta(hours=6)
        date_range = pd.date_range(self.start_date - sub6, self.end_date, freq='6H')
        file_spec = '06.gdas'

        if self.lbc_type == 'cfsr':
            nomads_url = "https://nomads.ncdc.noaa.gov/modeldata/cmd_{}/{}/{}{}/{}{}{}/"
        else:
            sys.exit()  # FOR NOW

        # ---- Functions ----
        def createDlist(date_range):
            # Assert extension == 'pgbh' or extension == 'flxf', 'bad argument'
            dlist = []
            filelist = []
            for date in date_range:
                for extension in ['pgbh', 'flxf']:
                    year = date.strftime('%Y')
                    month = date.strftime('%m')
                    day = date.strftime('%d')
                    hour = date.strftime('%H')
                    # get the pgbh files
                    base = nomads_url.format(extension, year, year, month, year, month,day)
                    filename = '{}{}.{}{}{}{}.grb2'.format(extension,self.file_spec, year, month, day, hour)
                    filepath = base + filename
                    # create lists of each
                    dlist.append(filepath)
                    filelist.append(filename)
            return dlist, filelist
        # fix the data destination argument
        cwd = os.getcwd()
        os.chdir(self.data_dl_dirc)

        # create url list and filenames
        urls, filenames = createDlist(date_range)
        # acc.multi_thread(acc.fetchFile, urls) # BROKEN --- misses downloading some files
        for url in urls:
            acc.fetchFile(url)
            self.logger.debug('downloading ....{}'.format(url))

        os.chdir(cwd)
        missing_files = 0
        for f in filenames:
            if self.data_dl_dirc.joinpath(f).exists():
                pass
            else:
                print(self.data_dl_dirc.joinpath(f))
                missing_files += 1
        if missing_files != 0:
            self.logger.error("{} missing files... ".format(missing_files))
            sys.exit()

if __name__ == '__main__':
    pass
