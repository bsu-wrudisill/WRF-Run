#!/bin/bash

# *****************************************************************************
# 
# FILE:     envWRF_3.8.1_INL.sh   
# AUTHOR:   Matt Masarik       (MM) 
# VERSION:  0      2016-03-14   MM    Base version v3.7.1  [TACC]
#           1      2016-07-12   MM    Updated for  v3.8    [TACC]
#           2      2016-09-29   MM    Updated for  v3.8.1  [INL]
#           2.1    2016-12-13   MM    Updated module loads
#           2.1.1  2016-12-14   MM    Added module purge, before loads
#
# PURPOSE:  Provides evironment variables and modules required for WRF v3.8.1
#           built from scripts, pre-buildWRF_3.8.1_INL_loginnode.sh and 
#           buildWRF_3.8.1_INL_computenode.sh.
#
# USAGE:    source ./envWRF_3.8.1_INL.sh
#
# OUTLINE:  
#          (1) Parameter defs / exports
#          (2) Module unloads / loads
# 
# NOTES:  
#
# *****************************************************************************



if [ -z "$SOURCED" ]; then
	# -----------------------------------------------------------------------------
	# (2) Module loads
	# -----------------------------------------------------------------------------

	# module unload ALL loaded modules
	module purge

	# module loads
	module load GCC/4.8.3 
	module load icc/2015.0.090
	module load ifort/2015.0.090
	module load iccifort/2015.0.090
	module load OpenMPI/1.8.2-iccifort-2015.0.090
	module load imkl/11.2.0.090
	module load tbb/4.3.0.090
	module load pbs 
	module load iomklt/4.5.0
	module load git/1.8.5.2-GCC-4.8.3

	# -----------------------------------------------------------------------------
	# (1) Parameters
	# -----------------------------------------------------------------------------

	# Base directory for WRF install           # !! USER CHANGE TO LIKING.. !!
	export WRF_BASE_DIR=/home/$USER/WRF

	# WRF version
	export WRF_VERSION=3.8.1

	# WRF build directories
	export SRC_DIR=$WRF_BASE_DIR/SRC
	export WRF_BUILD_DIR=$WRF_BASE_DIR/$WRF_VERSION
	export WRF_LIBS_DIR=$WRF_BUILD_DIR/WRF_LIBS

	# library install directories
	export NETCDF=$WRF_LIBS_DIR/netcdf
	export JASPERLIB=$WRF_LIBS_DIR/grib2/lib
	export JASPERINC=$WRF_LIBS_DIR/grib2/include

	# compile flags
	export LDFLAGS=-L$JASPERLIB
	export CPPFLAGS=-I$JASPERINC

	# path variables
	export PATH=$WRF_LIBS_DIR/netcdf/bin:$WRF_LIBS_DIR/grib2/bin:$PATH
	export LD_LIBRARY_PATH=$WRF_LIBS_DIR/netcdf/lib:$WRF_LIBS_DIR/grib2/lib:$LD_LIBRARY_PATH

	# set sourced 
	export SOURCED=1
else
	echo "I've already been sourced" 

fi 
