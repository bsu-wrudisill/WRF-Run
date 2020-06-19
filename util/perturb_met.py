import xarray as xr
import pathlib as pl
import glob
import numpy as np
import os 


met_file_list = glob.glob("met_em*")

for met_file in met_file_list:
    ds = xr.open_mfdataset(met_file)
    
    # data shapes..
    data_shape_sfc  = ds['SNOW'].shape
    data_shape_soil  = ds['SM'].shape
    data_shape_reg  = ds['PRES'].shape
    data_shape_uu = ds['UU'].shape
    data_shape_vv = ds['VV'].shape
    
    # perturb the regular atm variables...
    ds['PRES'] = ds['PRES']+np.random.rand(*data_shape_reg)
    ds['RH'] = ds['RH']+np.random.rand(*data_shape_reg)
    ds['TT'] = ds['TT']+np.random.rand(*data_shape_reg)
    
    # soil moisture 
    ds['SM'] = ds['SM']+np.random.rand(*data_shape_soil)
    
    # surface variables
    ds['PSFC'] = ds['PSFC']+np.random.rand(*data_shape_sfc)
    ds['SNOW'] = ds['SNOW']+np.random.rand(*data_shape_sfc)
    ds['SKINTEMP'] = ds['SKINTEMP']+np.random.rand(*data_shape_sfc)


    # apply to the staggered variables  
    ds['UU'] = ds['UU']+np.random.rand(*data_shape_uu)
    ds['VV'] = ds['VV']+np.random.rand(*data_shape_vv
                    
    
    # unlink the original met file ... 
    print('unlink {}'.format(met_file))
    os.unlink(met_file)
    ds.to_netcdf(met_file)


