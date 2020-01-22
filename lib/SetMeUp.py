import sys
import shutil
import os
import logging
import yaml
from pathlib import Path
import pandas as pd
import f90nml  # must be installed via pip


class SetMeUp:
    """
    This class describes a set me up.
    """
    
    def __init__(self, main, location=None, restart=False):
        """
        Constructs a new instance of SetMeUp. Reads options from the main yml
        file and converts into the appropirate instance attributes. This setup
        gets used by multiple classes via '__super__'.

        :param      main:  full path to config.yml file.
        :type       main:  str or pathlib.Path
        """
        self.logger = logging.getLogger(__name__)

        # Begin reading yml. Uses a somewhat 'hacky' way to
        # read in multiple files via the 'includes' list
        with open(main) as m:
            config_location = main.parent
            yamlfile = yaml.load(m, Loader=yaml.FullLoader)
            # Try to read all of the files listed in the 'includes' list
            for include in yamlfile.get("includes", []):
                include_path = config_location.joinpath(include)
                # Read in the extra yml file
                include_file = yaml.load(open(include_path),
                                         Loader=yaml.FullLoader)
                # Join the main yml file with contents from the includes files
                yamlfile.update(include_file,
                                Loader=yaml.FullLoader)

        # Now apply some logic to read in the correct config information based
        _template_request = yamlfile.get('jobtemplate')  # the requested template
        _templates_config = yamlfile.get('JobTemplates')  # dic of avail templates

        if _template_request not in _templates_config.keys():
            _message = 'job specification <{}> not found in config.yml'
            self.logger.error(_message.format(_template_request))
            sys.exit()
        else:
            self.jobtemplate = _templates_config.get(_template_request)

        # read machine parameters
        _machines = yamlfile.get('machines')
        self.scheduler = _machines.get(self.jobtemplate['machine']).get('scheduler')

        # Get the queue submission information from the config.yml file
        self.queue_params = self.jobtemplate['submit_parameters']
        self.queue = self.jobtemplate['queue']

        # Main Configuration -- machine related
        self.geog_data_path = Path(yamlfile['geog_data_path'])
        self.setup = main  # name of the setup file
        self.user = yamlfile['user']
        self.wrf_version = yamlfile['wrf_version']
        self.lbc_type = yamlfile['lbc_type']

        # get the appropriate ungrib template based on ...
        # the wrf version and the LBC type 
        _ungribtemplates = yamlfile.get('ungribtemplates')
        try:
            ungrib_template = _ungribtemplates.get(self.lbc_type.upper())
            ungrib_template = ungrib_template.get('wrf_version')
            self.ungrib_template = ungrib_template.get(self.wrf_version)

        except KeyError as E:
            logger.error(E)
            logger.error('Check the user_config/_ungribtemplates')

        # Env. file should contain all appropriate module loads necessary
        # to run the wrf/real/geo... etc. executable files.
        self.cwd = Path(os.getcwd())
        self.environment_file = self.cwd.joinpath(yamlfile['environment'])

      
        # Find/Parse the namelist files using f90nml
        # !!!!! DANGER !!!!!
        # Assumes they live in cwd/namelists dir
        _wps_name = self.jobtemplate['wps_namelist']
        _input_name = self.jobtemplate['input_namelist']
        self.wps_namelist_path = self.cwd.joinpath('user_config',
                                                   'namelists',
                                                   _wps_name)

        self.input_namelist_path = self.cwd.joinpath('user_config',
                                                     'namelists',
                                                     _input_name)

        # Read the namelist filecontents
        with open(self.wps_namelist_path) as nml_file:
            self.wps_namelist_file = f90nml.read(nml_file)

        with open(self.input_namelist_path) as nml_file:
            self.wps_namelist_file = f90nml.read(nml_file)
        # Extrack key parameters about the WRF configuration
        self.num_wrf_dom = self.wps_namelist_file['domains']['max_dom']

        # Directories to copy from the compiled WRF model
        # (or wherever they live on the system)
        self.wrf_exe_dirc = Path(yamlfile['wrf_exe_directory'])
        self.wps_exe_dirc = Path(yamlfile['wps_exe_directory'])
        self.geo_exe_dirc = self.wps_exe_dirc.joinpath('geogrid')
        self.met_exe_dirc = self.wps_exe_dirc.joinpath('metgrid')
        self.ungrib_exe_dirc = self.wps_exe_dirc.joinpath('ungrib')

        # self.metgrid_files = path(yamlfile['metgrid_files'])
        # self.geogrid_file = yamlfile['geogrid_file']

        # Determine whether or not we need to run geo/met/ungrib
        self.run_download_flag = True  # ! Not currently implemented
        self.run_metgrid_flag = True  # ! Not currently implemented
        self.run_geogrid_flag = True  # ! Not currently implemented

        ########################################################
        ####   DYNAMIC LOGIC STUFF --- WEIRDNESS, DANGER   #####
        self.main_run_dirc = Path(yamlfile['scratch_space']).joinpath('test')
        self.restart = yamlfile['restart'] # should be true or false 
        ########################################################

        # Forcing files time format
        self.time_format = "%Y-%m-%d_%H:%M:%S"
        self.output_format = "wrfout_d0{}_{}"

        # Fetch dates for start and end dates
        run_date = yamlfile['run_date']
        self.start_date = pd.to_datetime(run_date['start_date'])
        self.end_date = pd.to_datetime(run_date['end_date'])

        # Get wrf_run_options
        self.wrf_run_options = yamlfile['wrf_run_options']

        # Look for the restart file
        self.restart_directory = Path(yamlfile['restart_directory'])

        #TODO: need option for more than 2 domains...
        self.rst_files = ['wrfrst_d02_{}'.format(self.start_date.strftime(self.time_format)),
                          'wrfrst_d01_{}'.format(self.start_date.strftime(self.time_format))]

        self.storage_space = Path(yamlfile['storage_space']) 
        update = {'main_run_dirc':self.main_run_dirc, 'restart':restart}
        
        # NOTE: The two asterix mean that the function will take * number of arguments
        #... so like all of the key:value pairs of a dictionary
        self.__update(**update)

    def __update(self, **kwargs):  #main_run_dirc, restart):
        main_run_dirc = kwargs.get('main_run_dirc', None)
        restart = kwargs.get('restart', None)
        
        if main_run_dirc:
            # update the paths -- this is a bit yucky 
            self.main_run_dirc = main_run_dirc
            self.wrf_run_dirc = main_run_dirc.joinpath('wrf')
            self.wps_run_dirc = main_run_dirc.joinpath('wps')
            self.geo_run_dirc = self.wps_run_dirc.joinpath('geogrid')
            self.ungrib_run_dirc = self.wps_run_dirc.joinpath('ungrib')
            self.met_run_dirc = self.wps_run_dirc.joinpath('metgrid')
            self.data_dl_dirc = self.wps_run_dirc.joinpath('raw_lbcs')
        if restart:
            self.restart = restart 
        # update whether or not the run is a restart
        
    def createRunDirectory(self):
        # copy contents of the 'WRFVX/run' directory to the main run dir
        self.main_run_dirc.mkdir(parents=True)

        # Self.wrf_run_dirc.mkdir()
        shutil.copytree(self.wrf_exe_dirc.joinpath('run'),
                        self.wrf_run_dirc, symlinks=True)

        # get geogrid
        self.wps_run_dirc.mkdir()
        self.geo_run_dirc.mkdir()
        self.met_run_dirc.mkdir()
        self.ungrib_run_dirc.mkdir()
        self.data_dl_dirc.mkdir()

        # NAMELIST.INPUT
        shutil.copy(self.input_namelist_path,
                    self.main_run_dirc.joinpath('namelist.input.template'))
        shutil.copy(self.wps_namelist_path,
                    self.main_run_dirc.joinpath('namelist.wps.template'))

        # Copy METGRID
        shutil.copy(self.met_exe_dirc.joinpath('metgrid.exe'),
                    self.met_run_dirc)
        shutil.copy(self.met_exe_dirc.joinpath('METGRID.TBL'),
                    self.met_run_dirc)

        # Copy ungrib files
        shutil.copytree(self.ungrib_exe_dirc.joinpath('Variable_Tables'),
                        self.ungrib_run_dirc.joinpath('Variable_Tables'))

        shutil.copy(self.ungrib_exe_dirc.joinpath('ungrib.exe'),
                    self.ungrib_run_dirc)

        shutil.copy(self.wps_exe_dirc.joinpath('link_grib.csh'),
                    self.ungrib_run_dirc)

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
        # get the restart files
        if self.restart:
            for rst in self.rst_files:
                shutil.copy(self.restart_directory.joinpath(rst), self.wrf_run_dirc)
        else:
            # nothing to copy 
            pass



if __name__ == '__main__':
    setup = SetMeUp('main.yml')
    setup.createRunDirectory()
