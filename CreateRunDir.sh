#!/bin/bash
# create a run directory
name=$1
mkdir $name

cp Run/* $name/.
cp scripts/run_wrf_time_period.sh $name/.
cp scripts/ReRunWRF.sh $name/.
cp scripts/submit.sh.template $name/.
cp scripts/std_funcs.sh $name/.

