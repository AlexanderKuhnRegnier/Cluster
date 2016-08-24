import pandas as pd
import os
from datetime import datetime
import numpy as np

META = 'C:/Users/ahfku/Documents/Magnetometer/clusterdata/META/'#home pc

class meta2:
    def __init__(self,sc,start_date,end_date,dir=META,version='B'):
        '''
        Create entries on two days if needed, since a fragmented packet
        might otherwise 'think' that no data was already there, and this would
        cause all sorts of trouble.
        If extended mode is longer than 2 days, this will obviously not 
        suffice. The code should be easy enough to extend for this case.
        '''
        self.sc = sc
        self.ext_start = start_date
        self.ext_end = end_date
        self.version = version
        self.columns = ['sc','start_date','end_date','version','dump_date',
                        'nr_vectors','spin_period','reset_period']
        if start_date.date() == end_date.date():
            Year = str(start_date.date().year)
            year = Year[2:]
            month = format(start_date.date().month,'02d')
            day = format(start_date.date().day,'02d')
            filename = 'C'+format(sc,'1d')+'_'+year+month+day+'_'+version+'.META2'
            filepath = dir+Year+'/'+month+'/'
            if not os.path.isdir(filepath):
                os.makedirs(filepath)
            self.files = [filepath+filename]
        else:
            Year = str(start_date.date().year)
            year = Year[2:]
            month = format(start_date.date().month,'02d')
            day = format(start_date.date().day,'02d')
            filename1 = 'C'+format(sc,'1d')+'_'+year+month+day+'_'+version+'.META2'
            filepath1 = dir+Year+'/'+month+'/'
            if not os.path.isdir(filepath1):
                os.makedirs(filepath1)
            Year = str(end_date.date().year)
            year = Year[2:]
            month = format(start_date.date().month,'02d')
            day = format(start_date.date().day,'02d')
            filename2 = 'C'+format(sc,'1d')+'_'+year+month+day+'_'+version+'.META2'
            filepath2 = dir+Year+'/'+month+'/'
            if not os.path.isdir(filepath2):
                os.makedirs(filepath2)                
            self.files = [filepath1+filename1,filepath2+filename2]
        self.frames = []
        for file in self.files:
            if os.path.isfile(file):
                '''
                read info into dataframe before any writing is done!
                '''
                self.frames.append(pd.read_csv(file,parse_dates=[1,2,4]))
            else:
                self.frames.append(pd.DataFrame(columns=self.columns))
    def write(self,dump_date,nr_vectors,spin_period,reset_period,
              start_reset,end_reset):  
        for index,file in enumerate(self.files):
            new_row = pd.DataFrame(np.array([self.sc,self.ext_start,self.ext_end,
                                    self.version,dump_date,nr_vectors,
                                    spin_period,reset_period]).reshape(-1,8),
                                    columns = self.columns)
            self.frames[index] = pd.concat((self.frames[index],new_row),
                                            ignore_index=True)
            self.frames[index].drop_duplicates(inplace=True)
            self.frames[index].to_csv(file,index=False)
    def read(self):
        frames = pd.concat((self.frames))      
        frames.reset_index(drop=True,inplace=True)
        frames.drop_duplicates(inplace=True)
        return frames
    
    def overwrite_interval(self,start,end,nr_vectors=0):
        '''
        check whether start and end date are within one of the intervals in the
        meta file!
        A tolerance of 1 hour is applied to the search    
        To overwrite old instance, new number of vectors needs to be at 
        least 100 vectors higher than the old number of vectors! Only if this
        is satisfied, is True returned.
        True if interval not found, False if it is!
        Return True if:
            interval not contained within already present dates
            OR nr_vectors higher (at least 100 more) than already present
                for a matching interval
        otherwise, return False
        '''
        info = self.read()
        start = (info['start_date'].apply(
                                    lambda x:x-pd.Timedelta(60**2,'s')))<start
        end = (info['end_date'].apply(
                                    lambda x:x+pd.Timedelta(60**2,'s')))>end
        together = start & end
        info = info[together]
        if nr_vectors != 0:
            if np.any(info['nr_vectors']<nr_vectors-100):
                more_vectors=True
            else:
                more_vectors=False
        else:
            more_vectors=True #disable check - since it was not selected 
                              #(0 was passed to nr_vectors)
        if np.sum(together):
            if np.sum(together)>1:
                print ("WARNING, more than one interval found in one or more "
                        "META files:"+','.join(self.files))
            if more_vectors:
                return True
            else:
                return False
        else:
            return True

  
sc=1
start_date = datetime(2016,1,4)
end_date = datetime(2016,1,5)

dump_date = datetime(2016,1,6)
nr_vectors = 1000
spin_period = 4.26
reset_period=5.1522208
start_reset = 3000
end_reset=4000

meta = meta2(sc,start_date,end_date)
meta.write(dump_date,nr_vectors,spin_period,reset_period,start_reset,end_reset)
print "reading"
print meta.read()
print meta.overwrite_interval(start_date,end_date,nr_vectors=2000)
