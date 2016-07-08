#from datetime import date,time,datetime,timedelta
import os

def getfile(sc,Year,month,day,directory, ext=False):
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
    file_dict = {}
    if int(Year)>=2000:
        year = str(Year[2:4])
    else:
        year=str(Year)
    month = str(month)
    day = str(day)
    sc = str(sc)
    for file in os.listdir(directory):
        if "C"+str(sc) in file and year+month+day in file and ".EXT.GSE" in file:
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

def getreffile(sc,Year,month,day,directory):
    file_dict = {}
    if int(Year)>=2000:
        year = str(Year[2:4])
    else:
        year=str(Year)
    month = str(month)
    day = str(day)
    sc = str(sc)
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

def getcaafile(sc,Year,month,day,directory):     
    file_dict = {}
    if int(Year)<2000:
        Year = int(Year)
        Year+=2000
        Year=str(Year)
    else:
        Year=str(Year) 
    month = str(month)
    day = str(day)
    sc = str(sc)
    for file in os.listdir(directory):
        if 'C'+str(sc)+'_CP_FGM_SPIN__'+Year+month+day in file and '.cef.gz' in file:
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
print getcaafile(1,2016,1,1,dir)
print getcaafile(1,2015,12,31,dir)
'''