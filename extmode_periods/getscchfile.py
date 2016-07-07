import os
from datetime import datetime,timedelta

def getscchfile(sc,dt,dir):
    Year=str(dt.year)
    month=dt.month
    day=dt.day
    file_dict = {}
    if int(Year)>=2000:
        year = str(Year)[2:4]
    else:
        year=str(Year)
    month = '{:02d}'.format(month)
    day = '{:02d}'.format(day)
    sc = '{:1d}'.format(sc)
    directory = dir+Year+'/'+month+'/'
    #print year,month,day,sc
    for file in os.listdir(directory):
        if "C"+sc in file and year+month+day in file and ".SCCH" in file:
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
        
def getscchfiles(sc,start_date=datetime(9999,1,1),end_date=datetime(9999,1,1)):
    if end_date == datetime(9999,1,1):    
        dates = [start_date]
    elif (end_date-start_date).days>0:
        dates = [start_date + timedelta(days=i) 
                for i in range(0,((end_date-start_date).days+1))]
    else:
        raise Exception("Enter valid dates")
    dir = 'Z:/data/raw/'
    file_list = []    
    for date in dates:
        file = getscchfile(sc,date,dir)
        if file:
            file_list.append(file)
    return file_list
            
'''
Testing
'''

'''
#print getscchfile(1,2016,1,1,dir)
print getscchfiles(1,datetime(2016,1,1),datetime(2016,1,10))
'''