#!/bin/bash

# *****************************************************************************
# 
# FILE:     envWRF_4.1.2_R2.sh   
# AUTHOR:   Matt Masarik      (MM) 
# VERSION:  0     2019-05-31   MM    Base version
#
# PURPOSE:  Provides evironment variables and modules required for WRF v4.1.2
#           built from script, buildWRF_4.1.2_R2.sh.
#
# USAGE:    source ./envWRF_4.1.2_R2.sh
#
# OUTLINE:  
#          (1) Parameters
#          (2) Module loads
# *****************************************************************************


# -----------------------------------------------------------------------------
# (1) Parameters
# -----------------------------------------------------------------------------

##########################   USER: CHANGE ME   ################################
# Base directory for WRF install              
export WRF_BASE_DIR=/home/wrudisill/WRF-R2/

# WRF version                                 
export WRF_VERSION=4.1.2



#####################   DO NOT MODIFY BELOW HERE   ############################
# WRF build directories
export SRC_DIR=$WRF_BASE_DIR/SRC
export WRF_BUILD_DIR=$WRF_BASE_DIR/$WRF_VERSION
export WRF_LIBS_DIR=$WRF_BUILD_DIR/WRF_LIBS
export WRF_DIR=$WRF_BASE_DIR/$WRF_VERSION/WRF-$WRF_VERSION

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

# load modules
module load shared
module load git/64/2.12.2
module load slurm/17.11.12
module load intel/compiler/64/2020/2020.3
module load intel/mpi/64/2020/2020.3
module load intel/mkl/64/2020/2020.3
module load hdf5_18/intel/1.8.18-mpi
module load netcdf/intel/64/4.4.1
module load udunits/intel/64/2.2.24
