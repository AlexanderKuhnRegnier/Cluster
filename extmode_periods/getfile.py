#from datetime import date,time,datetime,timedelta
import os
import pandas as pd
from datetime import datetime,timedelta

def getfile(sc,Year,month,day,directory,ext=False):
    Year = str(Year)
    month = '{0:02d}'.format(month)
    day = '{0:02d}'.format(day)
    directory = directory+Year+'/'+month+'/'
    #print "Getting file:",sc,Year,month,day,directory,ext
    if '/caa/ic_archive/' in directory: 
        return getcaafile(sc,Year,month,day,directory)
    elif '/reference/' in directory:
        if ext:
            return getextreffile(sc,Year,month,day,directory)
        else:    
            return getreffile(sc,Year,month,day,directory)
    else:
        raise Exception("Not valid caa or reference directory")

def getextreffile(sc,Year,month,day,directory):
    '''
    Called by the getfile method - not to be used on its own!
    '''
    year=Year[2:4]
    sc = str(sc)
    for version in ['K','B','A']:
        filepath = directory+'C'+sc+'_'+year+month+day+'_'+version+'.EXT.GSE'    
        if os.path.isfile(filepath):
            return filepath
    return 0

def getreffile(sc,Year,month,day,directory):
    '''
    Called by the getfile method - not to be used on its own!
    '''
    year=Year[2:4]
    sc = str(sc)
    for version in ['K','B','A']:
        filepath = directory+'C'+sc+'_'+year+month+day+'_'+version+'.P.GSE'
        if os.path.isfile(filepath):
            return filepath
    return 0

def dt_to_strings(dt):
    return str(dt.year),format(dt.month,'02d'),format(dt.day,'02d')

def caa_version_filter(file_list):
    assert len(file_list)>2,"File list to be filtered should contain multiple"\
                            +" versions, and thus be longer than 2"
    dummy = {}
    dummy['file_basis'] = [f[0:49] for f in file_list]
    dummy['file_versions'] = [int(f[49:51]) for f in file_list]
    dummy['remainder'] = [f[51:] for f in file_list]
    files = pd.DataFrame(dummy)
    files.sort_values('file_versions',inplace=True,ascending=False)
    files.drop_duplicates(subset=['file_basis'],inplace=True,keep='first')
    files['file_versions']=files['file_versions'].apply(func=lambda x: format(x,'02d'))
    results = files.apply(func=lambda x:''.join(x.values.tolist()),axis=1).values
    assert len(results)<=2,("Filtered list should only contain one or two files"
    "(not {}), one for the orbit end, and one for the start!").format(len(results))
    return results.tolist()

def getcaafile(sc,Year,month,day,directory):   
    '''
    Called by the getfile method - not to be used on its own!
    '''
    sc = str(sc)
    files = [s for s in os.listdir(directory) if 'SPIN' in s and 'C'+sc in s
                                                and 'cef.gz' in s]
    files_string = ''.join(files)
    current_date = datetime(int(Year),int(month),int(day))
    str_start = 'C'+sc+'_CP_FGM_SPIN__'+Year+month+day
    str_end = '_'+Year+month+day+'_'
    results = []
    if current_date.day<4:
        '''
        need to check whether one of our files is in a previous folder!
        '''        
        dir = directory[:-8]
        prev_month = current_date-timedelta(days=5)
        prev_directory = dir+str(prev_month.year)+'/'\
                        +format(prev_month.month,'02d')+'/'
        found = [s for s in os.listdir(prev_directory) if 'SPIN' in s 
                                    and 'C'+sc in s 
                                    and 'cef.gz' in s
                                    and pd.Timestamp(s[32:40])>=current_date]
        if len(found)>1:
            found = caa_version_filter(found)
            assert len(found)==1,("1 file should be found this way," 
                                " not {}!").format(len(found))
        results.extend([prev_directory+s for s in found])  
    '''
    if orbit ends on current date then get two files:
        one that start on the current date, and the one that ends on 
        the current date
    '''
    if str_start in files_string:
        if [s for s in files if str_end in s[31:]]:
            found = [s for s in files if (str_start in s) or (str_end in s[31:])]
            if len(results)>2:
                found = caa_version_filter(found)
            assert len(found)==2,"Two files should be found here"
            results.extend([directory+s for s in found])
            assert len(results)==2,"Two files should have been found by now"
        else:
            assert len(results)==1,"We should only be here if a file has been"\
                                +" found in a previous month's folder!"
            found = [s for s in files if (str_start in s)]
            if len(found)>1:
                found = caa_version_filter(found)
            results.extend([directory+s for s in found])
            assert len(results)==2,"Two files should have been found by now"

    else:
        assert str_end not in files_string,"There is an orbit ending here,"\
                                        +"but no orbit start!" 
        '''
        search for files that start on previous day or up to 2 days before    
        '''
        dates = [current_date-timedelta(days=1)*(i+1) for i in xrange(3)]
        for date in dates:
            Year,month,day = dt_to_strings(date)
            str_start = 'C'+sc+'_CP_FGM_SPIN__'+Year+month+day
            if str_start in files_string:
                found =  [s for s in files if str_start in s]
                if len(found)>1:
                    found = caa_version_filter(found)
                assert len(found)==1,"There should only be one such file!"
                results.extend([directory+s for s in found])
                break
        assert len(results)==1,"One file should have been found by now"
    return results
                
            
'''
Testing
'''
'''
#print "results"
dir = 'Z:/caa/ic_archive/'
#print getfile(1,2016,1,1,dir)
#print getfile(1,2015,12,31,dir)
#refdir = "Z:/data/reference/" 

for i in range(1,20):
    print "new"
    print 2015,1,i
    print getfile(1,2015,1,i,dir)
'''