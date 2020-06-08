import sys
import pathlib as pl
libPathList = ['../']
for libPath in libPathList:
    sys.path.insert(0,libPath)

import accessories as acc
from DataDownload import * 



#for i in list_of_files:
#   sz = i.stat().st_size  * 10**(-6)
#   if sz == 0:
#       print(i, sz)


dlist, filelist, renamelist = CFSR('2002-02-01', '2002-02-03')
acc.multiFileDownloadParallel(dlist, renamelist)

result = acc.check_file_sizes(renamelist)



