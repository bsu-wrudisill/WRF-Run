#!/bin/bash

# *****************************************************************************
# 
# FILE:     envWRF_3.8.1_R2.sh   
# AUTHOR:   Matt Masarik      (MM) 
# VERSION:  0     2016-03-14   MM    Base version v3.7.1
#           1     2016-07-12   MM    v3.8
#           2     2017-01-18   MM    v3.8.1 on R2
#           2.1   2017-02-28   MM    New modules
#           2.2   2017-03-01   MM    More exports from build script
#           2.3   2017-03-19   MM    Updated for Intel 17.0.1
#           2.4   2017-05-24   MM    NetCDF4 module vs. built
#           2.5   2017-05-31   MM    hdf5:  1.8.17 --> 1.8.18
#           2.6   2017-06-19   MM    non-essential module additions
#           2.7   2017-10-05   MM    Intel: compiler/mpi/mkl - update
#           2.8   2018-03-12   MM    Intel: compiler-17.0.5/mpi/mkl - update
#           2.9   2018-10-12   MM    Slurm update
#
# PURPOSE:  Provides evironment variables and modules required for WRF v3.8.1
#           built from script, buildWRF_3.8.1_R2.sh.
#
# USAGE:    source ./envWRF_3.8.1_R2.sh
#
# OUTLINE:  
#          (1) Parameters
#          (2) Module loads
# 
# NOTES:  
#
# *****************************************************************************


# -----------------------------------------------------------------------------
# (1) Parameters
# -----------------------------------------------------------------------------

# Base directory for WRF install           # !! USER CHANGE TO LIKING.. !!
export WRF_BASE_DIR=/home/${USER}/LEAF/WRF



# WRF version
export WRF_VERSION=3.8.1


# WRF build directories
export SRC_DIR=$WRF_BASE_DIR/SRC
export WRF_BUILD_DIR=$WRF_BASE_DIR/$WRF_VERSION
export WRF_LIBS_DIR=$WRF_BUILD_DIR/WRF_LIBS


# libary install directories
export JASPER_GRIB2=$WRF_LIBS_DIR/grib2
export JASPERLIB=$JASPER_GRIB2/lib
export JASPERINC=$JASPER_GRIB2/include


# compile flags
export LDFLAGS=-L$JASPERLIB
export CPPFLAGS=-I$JASPERINC


# path variables
export PATH=$JASPER_GRIB2/bin:$PATH
export LD_LIBRARY_PATH=$JASPERLIB:$LD_LIBRARY_PATH



# -----------------------------------------------------------------------------
# (2) Module loads
# -----------------------------------------------------------------------------

# unload any auto-loaded modules
module purge

# now, load desired modules
module use $HOME/modules/modulefiles
module load shared
module load slurm/17.11.8
module load git/64/2.12.2
module load intel/compiler/64/2017/17.0.2
module load intel/mpi/64/2017/2.174
module load intel/mkl/64/2017/2.174
module load hdf5_18/intel/1.8.18
module load netcdf/intel/64/4.4.1
module load udunits/intel/64/2.2.24
