import sys
import os
import datetime
import logging
import pandas as pd
import accessories as acc
#from SetMeUp import SetMeUp
from RunWPS import RunWPS
import secrets
import f90nml   # this must be installed via pip ... ugh


class RunNDown(SetMeUp):
    """
    This class describes run wps.
    """

    def __init__(self, setup, update=None):
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
        #self.start_date = acc.DateParser(kwargs.get('start_date',
        #                                            self.start_date))
        #self.end_date = acc.DateParser(kwargs.get('end_date',
        #                              self.end_date))

        # check if there is an 'update' to pass into runwps
        if update:
            self._SetMeUp__update(**update)

        # Internal flags
        # Process Completed
        self.logger.info('Main Run Directory: {}'.format(self.wrf_run_dirc))

        # Check that the wrfout files specified in the setup file
        # match the outer grid dimensions in the namelist file...
        self.ndown_run_dirc_wps = self.main_run_dirc.joinpath('ndown_wps')
        self.ndown_run_dirc_wrf = self.main_run_dirc.joinpath('ndown_wrf')

        # get the wrf parent grid...
        self.parent_grid_wrf = Path(self.yamlfile['parent_grid_wrf'])

        # do some tests ...

    def _ndown_pre_checks(self):
        assert self.parent_grid_wrf.is_directory(), 'Parent wrf directory not found. Exit'

        # find the wrf files...
        #wrf_files = self.parent_grid_wrf.joinpath('wrf')
        #for wf in wrf_files.glob('wrfout_d01*'):
            # make sure they are all there...


    def LinkFiles(self, **kwargs):
        """
        Link the appropriate files from the parent wrf directory
        """


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



