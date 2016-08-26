import os
import datetime
import logging
module_logger = logging.getLogger('ExtendedModeProcessing.'+__name__)

def get_scch_file(sc,dt,dir):
    Year=str(dt.year)
    month=dt.month
    day=dt.day
    #file_dict = {}
    if int(Year)>=2000:
        year = str(Year)[2:4]
    else:
        year=str(Year)
    month = '{:02d}'.format(month)
    day = '{:02d}'.format(day)
    sc = '{:1d}'.format(sc)
    directory = dir+Year+'/'+month+'/'
    #print year,month,day,sc
    for version in ['K','B','A']:
        filepath = directory+'C'+sc+'_'+year+month+day+'_'+version+'.SCCH'    
        if os.path.isfile(filepath):
            return filepath
    return 0        
        
def getscchfiles(sc,start_date=0,end_date=0,dir='Z:/data/raw/'):
    if not end_date and start_date:    
        dates = [start_date]
    elif (end_date-start_date).days>0:
        dates = [start_date + datetime.timedelta(days=i) 
                for i in range(0,((end_date-start_date).days+1))]
    else:
        raise Exception("Enter valid dates")
    file_list = []    
    for date in dates:
        file = get_scch_file(sc,date,dir)
        if file:
            file_list.append(file)
        else: #log this/exception?
            module_logger.error("No commanding found for:"+str(date))
    return file_list
            
'''         
print getscchfiles(1,datetime.datetime(2016,5,1))
'''