import sys
import shutil
import os
import logging
import yaml
from pathlib import Path
import pandas as pd
#import f90nml  # must be installed via pip



class SetMeUp:
    """
    This class describes a set me up.
    """


    # These are completely static parameters that do not depend on config options
    time_format = "%Y-%m-%d_%H:%M:%S"
    output_format = "wrfout_d0{}_{}"
    logger = logging.getLogger(__name__)


    def __init__(self, main, update=None):
        """
        Constructs a new instance of SetMeUp. Reads options from the main yml
        file and converts into the appropirate instance attributes. This setup
        gets used by multiple classes via '__super__'.

        :param      main:  full path to config.yml file.
        :type       main:  str or pathlib.Path
        """

        # Begin reading yml. Uses a somewhat 'hacky' way to
        # read in multiple files via the 'includes' list
        self.main = main
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
        ungrib_template = _ungribtemplates.get(self.lbc_type.upper())
        ungrib_template = ungrib_template.get('wrf_version')
        self.ungrib_template = ungrib_template.get(self.wrf_version)


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

        # Directories to copy from the compiled WRF model
        # (or wherever they live on the system)
        self.wrf_exe_dirc = Path(yamlfile['wrf_exe_directory'])
        self.wps_exe_dirc = Path(yamlfile['wps_exe_directory'])
        self.geo_exe_dirc = self.wps_exe_dirc.joinpath('geogrid')
        self.met_exe_dirc = self.wps_exe_dirc.joinpath('metgrid')
        self.ungrib_exe_dirc = self.wps_exe_dirc.joinpath('ungrib')


        # ---- Locations for the Run Directory -----
        self.main_run_dirc = Path(yamlfile['scratch_space'])
        self.restart = yamlfile['restart'] # should be true or false

        # Fetch dates for start and end dates
        self.run_date = yamlfile['run_date']

        # Get wrf_run_options
        self.wrf_run_options = yamlfile['wrf_run_options']

        # Look for the restart file
        self.restart_directory = Path(yamlfile['restart_directory'])

        self.storage_space = Path(yamlfile['storage_space'])


        # Other RunTime Options Below Here
        # --------------------------------

        ndown_options = yamlfile['ndown_options']
        self.ndown_options = Path(ndown_options['parent_wrf_run'])

        hydro_options = yamlfile['hydro_options']
        self.hydro_options = Path(hydro_options['wrf_hydro_basin_files'])

    def __updater(self, **kwargs):
        """
        Update any of the self.attrs given a new key:value pair.
        Args:
            **kwargs: Description. This can be a dictionary
        """
        non_special_attrs = [attr for attr in dir(self) if not attr.startswith('__')]
        for attr in non_special_attrs:
            if attr in list(kwargs.keys()):
                new_value = kwargs[attr]
                logger.info('updating %s...', attr)
                logger.info('%s --> %s'%(self.attr, new_value))
                setattr(self, attr, new_value)


    '''
    Define a bunch of properties about the run.
    @properties have the advantage of dynamically updating based on
    other attrs in 'self'
    '''

    @property
    def start_date(self):
        return pd.to_datetime(self.run_date['start_date'])

    @property
    def end_date(self):
        return pd.to_datetime(self.run_date['end_date'])

    @property
    def wrf_run_dirc(self):
        return self.main_run_dirc.joinpath('wrf')

    @property
    def wps_run_dirc(self):
        return self.main_run_dirc.joinpath('wps')

    @property
    def geo_run_dirc(self):
        return self.wps_run_dirc.joinpath('geogrid')

    @property
    def ungrib_run_dirc(self):
        return self.wps_run_dirc.joinpath('ungrib')

    @property
    def met_run_dirc(self):
        return self.wps_run_dirc.joinpath('metgrid')

    @property
    def data_dl_dirc(self):
        return self.wps_run_dirc.joinpath('raw_lbcs')

    @property
    def wrf_output_folder(self):
        return self.main_run_dirc.joinpath('wrfouts')

    @property
    def restart_output_folder(self):
        return self.main_run_dirc.joinpath('restarts')

    @property
    def wps_namelist_file(self):
        with open(self.wps_namelist_path) as nml_file:
            return f90nml.read(nml_file)

    @property
    def input_namelist_file(self):
        with open(self.input_namelist_path) as nml_file:
            return f90nml.read(nml_file)

    @property
    def num_wrf_dom(self):
        return self.input_namelist_file['domains']['max_dom']

    @property
    def rst_files(self):
        if self.restart:
            return ['wrfrst_d0{}_{}'.format(dom, self.start_date.strftime(self.time_format)) for dom in range(self.max_dom)]
        else:
            return []

    # --------------------------
    # Special Options Below Here
    # --------------------------
    @property
    def ndown_wrf_parent_files(self):
        return self.ndown_options['parent_wrf_run'].joinpath('wrf')

    @property
    def ndown_ungrib_files(self):
        return self.ndown_options['parent_wrf_run'].joinpath('wps', 'ungrib')

    @property
    def wrf_hydro_basin_files(self):
        return self.hydro_options['wrf_hydro_basin_files']










