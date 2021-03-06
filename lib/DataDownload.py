import sys
import os
import datetime
import logging
import pandas as pd
import accessories as acc
from SetMeUp import SetMeUp
from multiprocessing import Pool


def CFSRV2(start_date,
           end_date,
           data_dl_dirc='./',
           logger=False):

    # Notes:
    # CFSRV2 is available from 2011-- onwards. The filenames that the ftp server spits out
    # are not unique, meaning that they must be assigned the correct name convention after
    # downloading (unlike CFSR, where the name is unique and correct). See the example URL

    # Example URL
    # https://nomads.ncdc.noaa.gov/modeldata/cfsv2_analysis_flxf/2011/201104/20110401/cdas1.t18z.sfluxgrbf06.grib2
    if type(start_date) == str:
        start_date = pd.to_datetime(start_date)
    if type(end_date) == str:
        end_date = pd.to_datetime(end_date)
                  
    #nomads_url = "https://www.ncei.noaa.gov/thredds/fileServer/model-cfs_v2_anl_6h_pgb/2020/202004/20200429/"
    nomads_url = "https://www.ncei.noaa.gov/thredds/fileServer/model-cfs_v2_anl_6h_{}/{}/{}/{}/"
    # OLD nomads_url = "https://nomads.ncdc.noaa.gov/modeldata/cfsv2_analysis_{}/{}/{}{}/{}{}{}/"
    filename = "cdas1.t{}z.{}.grib2"
    sub6 = datetime.timedelta(hours=6)
    date_range = pd.date_range(start_date - sub6, end_date, freq='6H')

    # Assert extension == 'pgbh' or extension == 'flxf', 'bad argument'
    dlist = []
    filelist = []
    renamelist = []
    for date in date_range:
        for extension in ['pgb', 'flxf']:
            if extension == 'pgb':
                fname_extension = 'pgrbh06'
                rename_extension = 'pgbh06'  # this is to be consisten w/ cfsr .... confusing i know. 
            elif extension == 'flxf':
                fname_extension = 'sfluxgrbf06'
                rename_extension = 'flxf06'  # this is to be consisten w/ cfsr .... confusing i know. 
            # get date info duh 
            year = date.strftime('%Y')
            month = date.strftime('%m')
            day = date.strftime('%d')
            hour = date.strftime('%H')

            # get the pgbh files
            base = nomads_url.format(extension, year, year+ month, year+month+day)
            filename_complete = filename.format(hour, fname_extension)
            filepath = base + filename_complete
            rename = "{}_{}{}{}{}_{}".format(rename_extension, year, month, day, hour, filename_complete)

            # create lists of each
            dlist.append(filepath)
            filelist.append(filename_complete)
            renamelist.append(rename)
            # append rename to list 
    print(dlist)
    return dlist, filelist, renamelist


def CFSR(start_date,
         end_date,
         data_dl_dirc='./'):

    # Notes:
    #
    #
    # HARDCODED
    #OLD --- nomads_url = "https://nomads.ncdc.noaa.gov/modeldata/cmd_{}/{}/{}{}/{}{}{}/"

# EXAMPLE   
    
    #nomads_url_pres  = "https://www.ncei.noaa.gov/thredds/catalog/model-cfs_reanl_6h_pgb/{}/{}/{}/catalog.html?dataset=cfs_reanl_6h_pgb/{}/{}/{}/"
    #nomads_url_sfc = "https://www.ncei.noaa.gov/thredds/catalog/model-cfs_reanl_6h_flxf/{}/{}/{}/catalog.html?dataset=cfs_reanl_6h_flxf/{}/{}/{}/"
    
    nomads_url = "https://www.ncei.noaa.gov/thredds/fileServer/model-cfs_reanl_6h_{}/{}/{}/{}/"



 
    file_spec = '06.gdas'

    if type(start_date) == str:
        start_date = pd.to_datetime(start_date)
    if type(end_date) == str:
        end_date = pd.to_datetime(end_date)

    # START THE LOGIC
    sub6 = datetime.timedelta(hours=6)
    date_range = pd.date_range(start_date - sub6, end_date, freq='6H')

    # ---- Functions ----
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
            if extension == 'pgbh':
                    front='pgb'
                    base = nomads_url.format(front, year, year+month, year+month+day)

            if extension == 'flxf':
                    front='flxf' 
                    base = nomads_url.format(front, year, year+month, year+month+day)
            
            filename = '{}{}.{}{}{}{}.grb2'.format(extension, file_spec, year, month, day, hour)
            filepath = base + filename
            # create lists of each
            dlist.append(filepath)
            filelist.append(filename)
    return dlist, filelist

#     # fix the data destination argument
#     cwd = os.getcwd()
#     os.chdir(data_dl_dirc)

#     # create url list and filenames
#     urls, filenames = createDlist(date_range)
#     # acc.multi_thread(acc.fetchFile, urls) # BROKEN --- misses downloading some files
#     for url in urls:
#         acc.fetchFile(url)
#         print(url)
# #        logger.debug('downloading ....{}'.format(url))

#     os.chdir(cwd)
#     missing_files = 0
#     for f in filenames:
#         if self.data_dl_dirc.joinpath(f).exists():
#             pass
#         else:
#             print(self.data_dl_dirc.joinpath(f))
#             missing_files += 1
#     if missing_files != 0:
#         self.logger.error("{} missing files... ".format(missing_files))
#         sys.exit()
