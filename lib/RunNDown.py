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


class RunNDown(RunWPS, RunWRF):
    """
    We get to use all of the RunWPS functions in addition to the RunWRF Funtcions!!
    """

    def start(self):
        self.logger.info('Main Run Directory: {}'.format(self.wrf_run_dirc))


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
        self.ndown_run_directory.mkdir()

        # NO NEED TO DOWNLOAD DATA AGAIN OR RUN UNGRIB


        # NAMELIST.INPUT
        shutil.copy(self.input_namelist_path,
                    self.main_run_dirc.joinpath('namelist.input.template_outer'))

        shutil.copy(self.wps_namelist_path,
                    self.main_run_dirc.joinpath('namelist.wps.template_outer'))


        #
        shutil.copy(self.input_namelist_path,
                    self.main_run_dirc.joinpath('namelist.input.template_outer'))

        shutil.copy(self.wps_namelist_path,
                    self.main_run_dirc.joinpath('namelist.wps.template_outer'))



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
            dst = self.ndown_run_directory.joinpath(name)
            print('%s --> %s'%(src,dst))
            #os.symlink(src, dst)


    def RunGeogrid(self):
        """Summary
        """


    def RunMetgrid(self):
        """Summary
        """
        RunWPS._prepare_metgrid(self.logger,
                                self.met_run_dirc,
                                self.ungrib_run_dirc,
                                self.geo_run_dirc)


    def CreateWRFBdyFiles(self):
        """Summary
        1) Run real.exe to create wrfinput files
        2) Run ndown.exe to create LBC conditions (wrfbdy files)
           Do this in 'one fell swoop' for all LBC files...
        """


    def RunSingleDomain(self):
        """Summary
        """



    def UpdateNamelists(self, **kwargs):
        """Summary

        Args:
            **kwargs: Description
        """


        # Change the interval_seconds in the time_control section to 3600
        # i.e. -- 1hrly forcing from wrf

        # Change the max_dom to 1


        # Change hte .... (what else?)



