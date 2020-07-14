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

        # Create patch on iniitalization for the namelist
        self.patch()

        # Internal flags
        # Process Completed
        self.logger.info('Main Run Directory: {}'.format(self.wrf_run_dirc))

        # Check that the wrfout files specified in the setup file
        # match the outer grid dimensions in the namelist file...
        self.ndown_run_dirc_wps = main_run_dirc.joinpath('ndown_wps')
        self.ndown_run_dirc_wrf = main_run_dirc.joinpath('ndown_wrf')


    def CreateDirectory(self, **kwargs):
        """Summary

        Args:
            **kwargs: Description
        """

        # STEP 1: Look for the corrrect met and geo files
        status = self.PreCheck(geo_dirc=self.geo_run_dirc,
                               met_dirc=self.met_run_dirc)

        met_found, met_message, required_met_files = status['met']
        geo_found, geo_message, required_geo_files = status['geo']

        if met_found and geo_found:
            self.logger.info("Found metgrid and geogrid files***")

        else:
            raise FileNotFoundError
            sys.exit()

        # STEP 2: Create the directories...
        self.ndown_run_dirc_wps.mkdir()
        self.ndown_run_dirc_wrf.mkdir()

        # STEP 3: Symlik files
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



    def RunNDown(self):
        """Summary
        1) Run real.exe to create wrfinput files
        2) Run ndown.exe to create LBC conditions (wrfbdy files)
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



