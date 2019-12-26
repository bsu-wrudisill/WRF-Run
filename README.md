# BETA
# Description and motivation
WRF-Run is a collection of Python scripts designed to facilitate running the Weather Research and Forecasting (WRF, https://www.mmm.ucar.edu/weather-research-and-forecasting-model). Essentially, running a WRF simulation entails running 3-4 fortran programs in sequence. The goal of this workflow is to 'wrap' the process without modifying the underlying WRF codebase to make it easier to spin up, run, and evaluate simulations. WRF is typically run on large clusters or university HPC systems with a 'job scheduler' system (PBS or Slurm, as far as I know). Both job scheduler options are currently supported.

# Interacting with WRF-Run
There are two goals of WRF-Run: 
1) Make it easy to run WRF simulations for long periods of time, as 'hands off' as possible
2) Provide a flexible API for creating new workflows

Adn the ancilliary goals include:
1) Making the code fail as fast as possible, meaning that errors get caught in the input arguments before getting passed off to WRF. 
2) Creating a generalizeable-enough framework so that the codebase can be easily updated as new versions of WRF become available
