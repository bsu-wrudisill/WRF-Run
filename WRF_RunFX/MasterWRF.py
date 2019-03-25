import RunDivide as rd 
import RunWRF as rw
import datetime 

d1 = datetime.datetime(1998, 3, 19, 0, 0)
d2 = datetime.datetime(1998, 3, 28, 0, 0)

timeperiod=rd.wrfChunk(True)                      # restart == True 
timeperiod.DateGenerator(d1,d2)                   # 

runDir = "/scratch/wrudisill/WRFTestDir/Run_HScase"
wrf= rw.WRF_Run(timeperiod, runDir)
wrf.Run()
