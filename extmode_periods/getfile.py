#from datetime import date,time,datetime,timedelta
import os

def getfile(sc,Year,month,day,directory, ext=False):
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
    #file_dict = {}
    '''
    if int(Year)>=2000:
        year = str(Year)[2:4]
    else:
        year=str(Year)
    '''
    year=Year[2:4]
    #month = str(month)
    #day = str(day)
    sc = str(sc)
    '''
    #old code previously used in all three methods, now replaced by faster methods!
    for file in os.listdir(directory):
        if "C"+str(sc) in file and year+month+day in file and ".P.GSE" in file:
            version = file[10]  
            #print "version:",version
            file_dict[version]=file
    l = file_dict.keys()
    if len(l):
        #print "number of files:",len(l)
        l.sort()
        #print "final version:",l[-1]
        #print ""
        file = directory+file_dict[l[-1]]
        return file
    else:
        return 0
    '''
    for version in ['K','B','A']:
        filepath = directory+'C'+sc+'_'+year+month+day+'_'+version+'.P.GSE'
        if os.path.isfile(filepath):
            return filepath
    return 0

def getcaafile(sc,Year,month,day,directory):   
    '''
    Called by the getfile method - not to be used on its own!
    '''
    file_dict = {}
    '''
    if int(Year)<2000:
        Year = int(Year)
        Year+=2000
        Year=str(Year)
    else:
        Year=str(Year) 
    '''
    #month = str(month)
    #day = str(day)
    sc = str(sc)
    for file in os.listdir(directory):
        if 'C'+sc+'_CP_FGM_SPIN__'+Year+month+day in file and '.cef.gz' in file:
            version=file[-9:-7]           
            file_dict[version] = file
    l = file_dict.keys()
    if len(l):
        l.sort()
        file = directory+file_dict[l[-1]]
        return file
    else:
        return 0
            
'''
Testing
'''
'''
dir = 'Z:/caa/ic_archive/'
#print getfile(1,2016,1,1,dir)
#print getfile(1,2015,12,31,dir)
#refdir = "Z:/data/reference/" 
for i in range(1,20):
    print getfile(1,2015,1,i,dir)
'''