'''
Restart a WRF-Run from the last avaliable restart file. Assumes that the
metgrid and geogrid files already exist somewhere in the file structure
'''
import sys


# Point to a directory
# Case 1: User configurate file already exists 
# Case 2: Old version, no config file
