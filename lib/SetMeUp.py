import sys
import shutil
import os
import logging
import yaml
import pathlib as pl
import pandas as pd
import f90nml  # must be installed via pip


def path(obj):
    # turn object into a posix path if its not none
    if not obj:
        return pl.Path(obj)
    else:
        return None


class SetMeUp:
    """
    This class describes a set me up.
    """

    def __init__(self, main):
        """
        Constructs a new instance of SetMeUp. Reads options from the main yml
        file and converts into the appropirate instance attributes. This setup
        gets used by multiple classes via '__super__'.

        :param      main:  full path to config.yml file.
        :type       main:  str or pathlib.Path
        """
        self.logger = logging.getLogger(__name__)
        self.logger.info('Initializing...')

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
        # on setup parameters.
        machine = yamlfile.get('machine')
        # Check that the machine spec. in setup. is in the config file
        if machine not in yamlfile.keys():
            _message = 'machine specification <{}> not found in config.yml'
            self.logger.error(_message.format(machine))
            sys.exit()

        # Get the queue submission information from the config.yml file
        queue_params = yamlfile.get(machine)  # yuck this is kind of ugly.
        if yamlfile.get('queue') not in queue_params.get('queue_list'):
            self.logger.error()
            sys.exit()
        self.queue_params = queue_params  # assign queue params to self

        # Main Configuration -- machine related
        self.geog_data_path = path(yamlfile['geog_data_path'])
        self.setup = main  # name of the setup file
        self.cwd = path(os.getcwd())
        self.user = yamlfile['user']
        self.scheduler = yamlfile.get(machine).get('scheduler')

        # Queue located in the 'setup.yml' file since it will freqently change
        self.queue = yamlfile['queue']
        self.wrf_version = yamlfile['wrf_version']

        # Env. file should contain all appropriate module loads necessary
        # to run the wrf/real/geo... etc. executable files.
        self.environment_file = self.cwd.joinpath(yamlfile['environment'])

        # Look for the restart file
        self.restart = yamlfile['restart']

        # Find/Parse the namelist files using f90nml
        # !!!!! DANGER !!!!!
        # Assumes they live in cwd/namelists dir
        _wps_name_path = yamlfile['wps_namelist_file']
        _input_name_path = yamlfile['input_namelist_file']
        self.wps_namelist_file_path = self.cwd.joinpath('namelists',
                                                        _wps_name_path)
        self.input_namelist_file_path = self.cwd.joinpath('namelists',
                                                          _input_name_path)

        # Read the namelist filecontents
        with open(self.wps_namelist_file_path) as nml_file:
            self.wps_namelist_file = f90nml.read(nml_file)

        with open(self.input_namelist_file_path) as nml_file:
            self.wps_namelist_file = f90nml.read(nml_file)
        # Extrack key parameters about the WRF configuration
        self.num_wrf_dom = self.wps_namelist_file['domains']['max_dom']

        # Directories to copy from the compiled WRF model
        # (or wherever they live on the system)
        self.wrf_exe_dirc = path(yamlfile['wrf_exe_directory'])
        self.wps_exe_dirc = path(yamlfile['wps_exe_directory'])
        self.geo_exe_dirc = self.wps_exe_dirc.joinpath('geogrid')
        self.met_exe_dirc = self.wps_exe_dirc.joinpath('metgrid')
        self.ungrib_exe_dirc = self.wps_exe_dirc.joinpath('ungrib')

        # self.metgrid_files = path(yamlfile['metgrid_files'])
        # self.geogrid_file = yamlfile['geogrid_file']

        # Determine whether or not we need to run geo/met/ungrib
        self.run_download_flag = True  # ! Not currently implemented
        self.run_metgrid_flag = True  # ! Not currently implemented
        self.run_geogrid_flag = True  # ! Not currently implemented

        # These get created
        self.main_run_dirc = path(yamlfile['main_run_dirc'])
        self.wrf_run_dirc = self.main_run_dirc.joinpath('wrf')
        self.wps_run_dirc = self.main_run_dirc.joinpath('wps')
        self.geo_run_dirc = self.wps_run_dirc.joinpath('geogrid')
        self.ungrib_run_dirc = self.wps_run_dirc.joinpath('ungrib')
        self.met_run_dirc = self.wps_run_dirc.joinpath('metgrid')
        self.data_dl_dirc = self.wps_run_dirc.joinpath('raw_lbcs')

        # Forcing files time format
        self.time_format = "%Y-%m-%d_%H:%M:%S"
        self.output_format = "wrfout_d0{}_{}"

        # Fetch dates for start and end dates
        run_date = yamlfile['run_date']
        self.start_date = pd.to_datetime(run_date['start_date'])
        self.end_date = pd.to_datetime(run_date['end_date'])
        self.lbc_type = yamlfile['lbc_type']

        # Get wrf_run_options
        self.wrf_run_options = yamlfile['wrf_run_options']

    def createRunDirectory(self):
        # copy contents of the 'WRFVX/run' directory to the main run dir
        self.main_run_dirc.mkdir()

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
        shutil.copy(self.input_namelist_file_path,
                    self.main_run_dirc.joinpath('namelist.input.template'))
        shutil.copy(self.wps_namelist_file_path,
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


if __name__ == '__main__':
    setup = SetMeUp('main.yml')
    setup.createRunDirectory()
