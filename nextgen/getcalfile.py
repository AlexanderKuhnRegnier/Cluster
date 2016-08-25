import os
import pandas as pd

RAW = '/cluster/data/raw/'
CAACAL='/cluster/caa/calibration/' #caa calibration files directory
DAILYCAL='/cluster/operations/calibration/daily/'#dailycalfile dir
  
#RAW = 'Z:/data/raw/'
#CAACAL = 'Z:/caa/calibration/'
#DAILYCAL = 'Z:/operations/calibration/daily/'
  
def find_entry(filepath,entry_name="START REVOLUTION"):
    if os.path.isfile(filepath):
        with open(filepath,'rb') as f:
            for line in f:
                if entry_name in line:
                    return line
    return False

def getcalfile(sc,start_date,cal_dir):
    versions = ['B','K','A']
    dates = pd.date_range(start=start_date-pd.Timedelta(30,'D'),
                          periods=31,freq='D')[::-1]
    #print dates                          
    for date in dates:
        for version in versions:
            steffile=RAW+date.strftime('%Y/%m/')+'C'+format(3,'1d')+'_'+ \
                    date.strftime('%y%m%d')+'_'+version.upper()+'.STEF'
                    #sc 3 is reference sc!
            #print steffile
            if os.path.isfile(steffile):
                if os.stat(steffile).st_size:
                    break
            else:
                print "getcalfile, empty or missing stef file version ",date,version,steffile
        #print "trying to use:",steffile
        line = find_entry(steffile)
        #print "line:",line
        if line:
            break
        else:
            print "Trying to find START REVOLUTION entry in STEF file for previous day!"
    Year = line[27:31]
    month =line[32:34]
    day  = line[35:37]
    files = []
    if cal_dir == CAACAL:
        '''
        look for "C'.$sc.'_CC_FGM_CALF__'.$Year.$month.$day.'_*'.'"'
        '''
        #print "looking for caa:",'C'+format(sc,'1d')+'_CC_FGM_CALF__'+Year+month+day+'_'
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
    #print "found:",files
    file_versions = [(file,int(file[file.index('_V')+2:file.index('_V')+4])) \
                        for file in files]
    #print "found:", file_versions      
    #print "return:",sorted(file_versions,key=lambda entry: entry[1])[0][0]                         
    return cal_dir+sorted(file_versions,key=lambda entry: entry[1])[0][0]