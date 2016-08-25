import os
import pandas as pd

RAW = '/cluster/data/raw/'
EXT = '/cluster/data/extended/'

CAACAL='/cluster/caa/calibration/' #caa calibration files directory
DAILYCAL='/cluster/operations/calibration/daily/'#dailycalfile dir
    
def find_entry(filepath,entry_name="START REVOLUTION"):
    with open(filepath,'rb') as f:
        for line in f:
            if entry_name in line:
                return line
    return False

def getcalfile(sc,start_date,cal_dir):
    versions = ['B','K','A']
    dates = pd.date_range(start=start_date-pd.Timedelta(30,'D'),
                          periods=30,freq='D')[::-1]
    for date in dates:
        for version in versions:
            steffile=RAW+date.strftime('%Y/%m/')+'C'+format(3,'1d')+'_'+ \
                    date.strftime('%y%m%d')+'_'+version.upper()+'.STEF'
                    #sc 3 is reference sc!
            if os.path.isfile(steffile):
                if os.stat(steffile).st_size:
                    break
            else:
                print "getcalfile, empty or missing stef file version "+version
        line = find_entry(steffile)
        if line:
            break
        else:
            print "Trying to find START REVOLUTION entry in STEF file for previous day!"
    Year = line[27:32]
    month =line[32:35]
    day  = line[35:38]

    if cal_dir == CAACAL:
        '''
        look for "C'.$sc.'_CC_FGM_CALF__'.$Year.$month.$day.'_*'.'"'
        '''
        files = [file for file in os.listdir(cal_dir) if \
            'C'+format(sc,'1d')+'_CC_FGM_CALF__'+Year+month+day+'_' in file]
    elif cal_dir == DAILYCAL:
        '''
        look for "C'.$sc.'_'.$Year.$month.$day.'_*'.'"'
        '''
        files = [file for file in os.listdir(cal_dir) if \
            'C'+format(sc,'1d')+'_'+Year+month+day+'_' in file]
    '''
    Now select the highest version number, and return this
    '''
    file_versions = [(file,int(file[file.index('_V')+2:'_V'.index(file)+5])) \
                        for file in files]
    return sorted(file_versions,key=lambda entry: entry[1])[0][0]