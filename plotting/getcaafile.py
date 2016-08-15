from datetime import date,time,datetime,timedelta
import os


def getcaafile(sc,Year,month,day,directory):     
    file_dict = {}
    if int(Year)<2000:
        Year+=2000
    startdate=date(Year,month,day)
    dates = [startdate-timedelta(days=1)*i for i in range(4)]
    for datev in dates:
        file_dict = {}
        sYear= '{0:d}'.format(datev.year)
        smonth='{0:02d}'.format(datev.month)
        sday=  '{0:02d}'.format(datev.day)
        print sYear,smonth,sday
        folder = directory+sYear+'/'+smonth+'/'
        for file in os.listdir(folder):
            if 'C'+str(sc)+'_CP_FGM_SPIN__'+sYear+smonth+sday in file and '.cef.gz' in file:
                version=file[-9:-7]           
                file_dict[version] = file
        l = file_dict.keys()
        if len(l):
            l.sort()
            file = folder+file_dict[l[-1]]
            return file
            
'''
Testing
'''
'''
dir = 'Z:/caa/ic_archive/'
print getcaafile(1,2016,1,1,dir)
print getcaafile(1,2015,12,31,dir)
'''