import pandas as pd
import os
import numpy as np
from datetime import datetime
import logging
module_logger = logging.getLogger('ExtendedModeProcessing.'+__name__)
#META = 'C:/Users/ahfku/Documents/Magnetometer/clusterdata/META/'#home pc
META = 'please supply directory manually'
class meta2:
    def __init__(self,sc,combined_data,dir=META,version='B'):
        '''
        Create entries on two days if needed, since a fragmented packet
        might otherwise 'think' that no data was already there, and this would
        cause all sorts of trouble.
        If extended mode is longer than 2 days, this will obviously not 
        suffice. The code should be easy enough to extend for this case.
        '''
        self.sc = sc
        self.nr_vectors = combined_data.shape[0]
        self.start_reset = combined_data['reset'].min()
        self.end_reset = combined_data['reset'].max()
        self.ext_start = combined_data['time'].min()
        self.ext_end = combined_data['time'].max()
        self.version = version
        self.columns = ['processing_time','sc','start_date','end_date',
                        'version','dump_date',
                        'nr_vectors','start_reset','end_reset',
                        'spin_period','reset_period',
                        'initial_reset','initial_scet',
                        'final_reset','final_scet',
                        'reset_diff','scet_diff',
                        'extra_resets']
        self.date_columns = [0,2,3,5,12,14]
        if self.ext_start.date() == self.ext_end.date():
            Year = str(self.ext_start.date().year)
            year = Year[2:]
            month = format(self.ext_start.date().month,'02d')
            day = format(self.ext_start.date().day,'02d')
            filename = 'C'+format(sc,'1d')+'_'+year+month+day+'_'+version+'.META2'
            filepath = dir+Year+'/'+month+'/'
            if not os.path.isdir(filepath):
                os.makedirs(filepath)
            self.files = [filepath+filename]
        else:
            '''
            File for day 1
            '''
            Year = str(self.ext_start.date().year)
            year = Year[2:]
            month = format(self.ext_start.date().month,'02d')
            day = format(self.ext_start.date().day,'02d')
            filename1 = 'C'+format(sc,'1d')+'_'+year+month+day+'_'+version+'.META2'
            filepath1 = dir+Year+'/'+month+'/'
            if not os.path.isdir(filepath1):
                os.makedirs(filepath1)
            '''
            File for day 2
            '''
            Year = str(self.ext_end.date().year)
            year = Year[2:]
            month = format(self.ext_end.date().month,'02d')
            day = format(self.ext_end.date().day,'02d')
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
                self.frames.append(pd.read_csv(file,parse_dates=self.date_columns))
            else:
                self.frames.append(pd.DataFrame(columns=self.columns))
    def write_meta(self,dump_date,spin_period,reset_period,initial_reset,
                   initial_scet,final_reset,final_scet):
        if initial_reset and initial_scet and final_reset and final_scet:
            '''
            checking if they have been assigned to - ie they are not None
            '''
            reset_diff = final_reset-initial_reset
            if reset_diff<0:
                reset_diff += 65536
            scet_diff = (final_scet - initial_scet)/pd.Timedelta(1,'s')
            expected_resets = scet_diff/reset_period
            extra_resets = reset_diff-expected_resets
        else:
            reset_diff = None
            scet_diff = None
            extra_resets = None
            module_logger.error("No reset or SCET info from border packets!")
        for index,file in enumerate(self.files):
            new_row = pd.DataFrame(np.array([datetime.now(),self.sc,
                                    self.ext_start,self.ext_end,
                                    self.version,dump_date,self.nr_vectors,
                                    self.start_reset,self.end_reset,
                                    spin_period,reset_period,
                                    initial_reset,initial_scet,
                                    final_reset,final_scet,
                                    reset_diff,scet_diff,
                                    extra_resets]).reshape(-1,
                                    len(self.columns)),
                                    columns = self.columns)
            self.frames[index] = pd.concat((self.frames[index],new_row),
                                            ignore_index=True)
            self.frames[index].sort_values('processing_time',ascending=False)
            self.frames[index].drop_duplicates(subset=['sc','start_date',
                                        'end_date','version',
                                        'dump_date','nr_vectors','start_reset',
                                        'end_reset'],
                                        inplace=True)
            self.frames[index].to_csv(file,index=False)
    def read(self):
        frames = pd.concat((self.frames))      
        frames.reset_index(drop=True,inplace=True)
        frames.sort_values('processing_time',ascending=False)
        frames.drop_duplicates(subset=['sc','start_date','end_date','version',
                                       'dump_date','nr_vectors','start_reset',
                                       'end_reset'],
                                       inplace=True)
        return frames
    
    def write_interval(self):
        '''
        check whether start and end date are within one of the intervals in the
        meta file!
        A tolerance of 15 minutes is applied to the search    
        To overwrite old instance, new number of vectors needs to be at 
        least 100 vectors higher than the old number of vectors! Only if this
        is satisfied, is True returned.
        True if interval not found, False if it is!
        Return True if:
            interval not contained within already present dates
            OR nr_vectors higher (at least 100 more) than already present
                for a matching interval
        otherwise, return False
        Still need to call write() in order to actually write a META2 file 
        entry!
        '''
        info = self.read()
        start = (info['start_date'].apply(
                                    lambda x:x-pd.Timedelta((60**2)/4.,'s')))<self.ext_start
        end = (info['end_date'].apply(
                                    lambda x:x+pd.Timedelta((60**2)/4.,'s')))>self.ext_end
        together = start & end
        info = info[together]
        if np.any(info['nr_vectors']<self.nr_vectors-100):#np.any in case of 
                                                #multiple entries - noted below
            more_vectors=True
        else:
            more_vectors=False

        if np.sum(together):
            if np.sum(together)>1:
                module_logger.error("WARNING, more than one interval found in one or more "+
                        "META files:"+','.join(self.files))
            if more_vectors:
                return True
            else:
                return False
        else:
            return True

def read_meta_files(sc,start,end,version='BKA',dir=''):
    columns = ['processing_time','sc','start_date','end_date',
                            'version','dump_date',
                            'nr_vectors','start_reset','end_reset',
                            'spin_period','reset_period',
                            'initial_reset','initial_scet',
                            'final_reset','final_scet',
                            'reset_diff','scet_diff',
                            'extra_resets']    
    date_columns = [0,2,3,5,12,14]
    versions = [entry.upper() for entry in version]
    results = []
    for version in versions:
        for date in pd.date_range(start=start,end=end,freq='D'):
            Year = str(date.year)
            year = Year[2:]
            month = format(date.month,'02d')
            day = format(date.day,'02d')        
            filename = 'C'+format(sc,'1d')+'_'+year+month+day+'_'+version+'.META2'
            filepath = dir+Year+'/'+month+'/'  
            file = filepath+filename
            if os.path.isfile(file):
                results.append(pd.read_csv(file,parse_dates=date_columns))
                
    metadata = pd.concat((results),axis=0)
    metadata.drop_duplicates.drop_duplicates(subset=['sc','start_date','end_date','version',
                                       'dump_date','nr_vectors','start_reset',
                                       'end_reset'],
                                       inplace=True)
    return metadata