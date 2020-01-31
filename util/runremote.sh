#/bin/bash

# run the submit command by issuing it to screen w/o entering screen 
wateryear=$1
month=$2
conda activate runwrf 

screen -dmS WY-$wateryear_$month -c "python month.py $wateryear $month; exec sh"
