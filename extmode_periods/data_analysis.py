import numpy as np
#import copy
#from numpy import linalg as LA
from datetime import datetime,timedelta
import copy
import os
from getfile import getfile
import gzip
import bz2
import matplotlib.pyplot as plt
plt.style.use('classic')
import cPickle as pickle
#import pickle
import pandas as pd
from collections import OrderedDict
#import itertools
#import csv
#import time
logdir = 'Y:/logs/data_analysis/'
VERBOSE=False
PLOT_VERBOSE=False

pickledir = 'Y:/overlap_stats/'
imagedir=pickledir+'images/'
refdirahk114 = 'Y:/reference/'
refdirahk114caa = 'Y:/referencecaa/'
refdir = 'Z:/data/reference/'
caadir = 'Z:/caa/ic_archive/'
dirs = [refdirahk114,refdir,caadir,refdirahk114caa]
dir_names=['refdirahk114','refdir','caadir','refdirahk114caa']
prune_start=datetime(1,1,1)
prune_end=datetime(1,1,1)
prune_n=1
prune_value = 0
end_date = ''
    
class vfile_store:
    def __init__(self,start_date=datetime(1,1,1),
                 end_date=datetime(1,1,1),
                    prune_start=datetime(1,1,1),
                    prune_end=datetime(1,1,1),
                    prune_value=0,
                    input=[],
                    prune_greater_than=False,
                    std_n=0):
        self.contents=[start_date,end_date,prune_start,prune_end,
                       prune_value,input,prune_greater_than,std_n]
        self.vfiles=''
    def add_vectorfiles(self,vfiles):
        if not isinstance(vfiles,vectorfiles):
            raise Exception("Not a vectorfiles instance")
        self.vfiles=vfiles
    def get_vfiles(self):
        return self.vfiles
    def get_contents(self):
        return self.contents
    def is_equal(self,vectorfile_store):
        if not isinstance(vectorfile_store,vfile_store):
            raise Exception("Not a vfile_store instance")
        return vectorfile_store.get_contents()==self.contents
    '''
    def load_vfiles(self):
        picklef = self.make_pickle_filename()
        if os.path.isfile(picklef):
            with open(picklef,'rb') as f:
                vf = pickle.load(f)
            return vf
        else:
            return False
    def store_vfiles_pickle(self,vfiles):
        if not isinstance(vfiles,vectorfiles):
            raise Exception("Not a vectorfiles instance")
        picklef = self.make_pickle_filename()
        f = open(picklef,'wb')
        pickle.dump(vfiles,f)
        f.close()
        return f.closed
    def make_pickle_filename(self):
        str1 = self.contents[0].strftime('%Y%m%dT%H%M%S')
        if self.contents[1]=='':
            str2 = '_1_day_'
        else:
            str2 = self.contents[1].strftime('%Y%m%dT%H%M%S')        
        if self.contents[2]==datetime(1,1,1):
            str3 = 'no_prune_start'
        else:
            str3 = self.contents[2].strftime('%Y%m%dT%H%M%S')
        if self.contents[3]==datetime(1,1,1):
            str4 = 'no_prune_end'
        else:
            str4 = self.contents[3].strftime('%Y%m%dT%H%M%S')
        str5 = format(self.contents[4],'04d')
        str6 = '-'.join(map(str,list(itertools.chain(*self.contents[5]))))
        for dir,dir_name in zip(dirs,dir_names):
            if dir in str6:
                str6 = str6.replace(dir,dir_name)
        str7 = str(self.contents[6])
        str8 = format(self.contents[7],'04d')
        return pickledir+'__'.join([str1,str2,str3,str4,str5,str6,str7,str8]) 
    '''
    
class vectorlist:
    def __init__(self,ext=False):
        self.ext=ext
        self.filename = ''
    def isempty(self):
        if not self.vectors.empty:
            return False
        else:
            return True
    def prune(self,n=0,start_date=datetime(1,1,1),end_date=datetime(1,1,1),value=0,greater_than=True):
        '''
        Removes vectors from vectorlist which do not fit pruning criteria
        '''
        if VERBOSE:
            print "Before:",len(self.vectors)
        '''
        td = end_date-start_date
        if td.days > 0 and td.seconds >= 0:
            self.vectors=[v for v in self.vectors if v.datetime > start_date
                            if v.datetime < end_date]
        elif td.days >= 0 and td.seconds > 0:
            self.vectors=[v for v in self.vectors if v.datetime > start_date
                            if v.datetime < end_date]
        #decrease density of vectors
        '''
        if not self.vectors.empty:
            if start_date != datetime(1,1,1) and end_date != datetime(1,1,1):
                #self.vectors.drop_duplicates(inplace=True)
                #self.vectors.sort_index(inplace=True)
                self.vectors=self.vectors[start_date:end_date]
            if n > 0:
                #self.vectors=[v for (i,v) in enumerate(self.vectors) if not i%n] 
                self.vectors=self.vectors[::n]
            if VERBOSE:
                print "After:",len(self.vectors)
            if value > 0:
                if greater_than:
                    #self.vectors=[v for v in self.vectors if v.magnitude>value]
                    self.vectors=self.vectors[self.vectors['mag']>value]
                else:
                    #self.vectors=[v for v in self.vectors if v.magnitude<value]
                    self.vectors=self.vectors[self.vectors['mag']<value]
                if VERBOSE:
                    print "After value pruning:",len(self.vectors)

    def read_file(self,filename):
        data_dict = {'datetime':[],'x':[],'y':[],'z':[],'x_pos_gse':[],
                                                 'y_pos_gse':[],'z_pos_gse':[]}
        self.filename=filename
        if ('.cef.gz' in filename) and ('/caa/ic_archive/' in filename):
            data_dict['mag']=[]
            #this is caa file, needs to be read differently!
            #gzip.open(filename) #defaults to 'rb' and 9
            with gzip.open(filename,'rb') as f:
                for line in f:
                    if 'DATA_UNTIL = EOF' in line:
                        for line in f:
                            line = line.split(',')   
                            data_dict['datetime'].append(np.datetime64(line[0]))
                            x_mag = float(line[2])
                            y_mag = float(line[3])
                            z_mag = float(line[4])
                            mag = float(line[5])
                            x_pos_gse = float(line[6])
                            y_pos_gse = float(line[7])
                            z_pos_gse = float(line[8])                            
                            sc_range = int(line[9])
                            data_dict['x'].append(x_mag)
                            data_dict['y'].append(y_mag)
                            data_dict['z'].append(z_mag)
                            data_dict['mag'].append(mag)
                            data_dict['x_pos_gse'].append(x_pos_gse)
                            data_dict['y_pos_gse'].append(y_pos_gse)
                            data_dict['z_pos_gse'].append(z_pos_gse)
            self.vectors=pd.DataFrame(data_dict,columns=['datetime','x','y','z',
            'mag','x_pos_gse','y_pos_gse','z_pos_gse'])
            self.vectors.set_index('datetime',drop=True,inplace=True)
            self.vectors.drop_duplicates(inplace=True)
            self.vectors.sort_index(inplace=True)
        elif ('.cef.bz2' in filename) and ('/caa/ic_archive/' in filename):
            data_dict['mag']=[]
            #this is caa file, needs to be read differently!
            #gzip.open(filename) #defaults to 'rb' and 9
            with bz2.BZ2File(filename,'rb') as f:
                for line in f:
                    if 'DATA_UNTIL = EOF' in line:
                        for line in f:
                            line = line.split(',')   
                            data_dict['datetime'].append(np.datetime64(line[0]))
                            x_mag = float(line[2])
                            y_mag = float(line[3])
                            z_mag = float(line[4])
                            mag = float(line[5])
                            x_pos_gse = float(line[6])
                            y_pos_gse = float(line[7])
                            z_pos_gse = float(line[8])  
                            sc_range = int(line[9])
                            '''
                            can the range be plotted as well somehow??
                            can it be included as an optional parameter
                            without influencing the rest of the code?
                            '''
                            data_dict['x'].append(x_mag)
                            data_dict['y'].append(y_mag)
                            data_dict['z'].append(z_mag)
                            data_dict['mag'].append(mag)
                            data_dict['x_pos_gse'].append(x_pos_gse)
                            data_dict['y_pos_gse'].append(y_pos_gse)
                            data_dict['z_pos_gse'].append(z_pos_gse)
            self.vectors=pd.DataFrame(data_dict,columns=['datetime','x','y','z',
            'mag','x_pos_gse','y_pos_gse','z_pos_gse'])
            self.vectors.set_index('datetime',drop=True,inplace=True)
            self.vectors.drop_duplicates(inplace=True)
            self.vectors.sort_index(inplace=True)
        else:  
            with open(filename) as f:
                for line in f:
                    try:
                        line=line.split(' ')
                        line = [char for char in line if char != '']
                        x_mag = float(line[1])
                        y_mag = float(line[2])
                        z_mag = float(line[3])
                        x_pos_gse = float(line[4])
                        y_pos_gse = float(line[5])
                        z_pos_gse = float(line[6])  
                        data_dict['x'].append(x_mag)
                        data_dict['y'].append(y_mag)
                        data_dict['z'].append(z_mag)
                        data_dict['x_pos_gse'].append(x_pos_gse)
                        data_dict['y_pos_gse'].append(y_pos_gse)
                        data_dict['z_pos_gse'].append(z_pos_gse)
                        data_dict['datetime'].append(np.datetime64(line[0]))
                        #np.datetime64 conversion needs to be last so that
                        #the other assignments are still carried out in the 
                        #case of a ValueError
                    except ValueError:
                        if "60.000" in line[0]:
                            print "Replacing 60.000 by 59.999"
                            line[0]=line[0].replace('60.000','59.999')
                            line[0]=np.datetime64(line[0])
                            data_dict['datetime'].append(np.datetime64(line[0]))                  
                        else:
                            print "Unknown Error"
            self.vectors=pd.DataFrame(data_dict,columns=['datetime','x','y','z',
            'x_pos_gse','y_pos_gse','z_pos_gse'])
            self.vectors.set_index('datetime',drop=True,inplace=True)
            self.vectors.drop_duplicates(inplace=True)
            self.vectors.sort_index(inplace=True)
            if not self.vectors.empty:
                mag = np.linalg.norm(self.vectors.ix[:,['x','y','z']],axis=1)
                self.vectors['mag'] = mag
            else:
                self.vectors['mag']=[]
            self.vectors = self.vectors[['x','y','z',
                                 'mag','x_pos_gse','y_pos_gse','z_pos_gse']]
    def returndatetimes(self):
        '''
        return np.asarray(self.vectors['datetime'])
        '''
        return np.asarray(self.vectors.index)
    def returnmagnitudes(self):
        return np.asarray(self.vectors['mag'])
    def returnx(self):
        return np.asarray(self.vectors['x'])
    def returny(self):
        return np.asarray(self.vectors['y'])
    def returnz(self):
        return np.asarray(self.vectors['z'])
    def plotlists(self,array,scatter=True,log=False):
        global scatter_size
        #labels = [','.join([entry[2],entry[3]]) for entry in array]
        #labels = '-'.join(set(labels))
        #array = [vlist,color,legend,plotwhich]
        f,ax = plt.subplots(1,1)
        legend_colour_list_scatter = []
        legend_colour_list_line = []
        for count,entry in enumerate(array):
            #print "entry ",entry
            vlist = entry[0]
            colour = entry[1]
            legend = entry[2]
            if len(entry)==4:
                plotwhich= entry[3]
            else:
                plotwhich = ''
            #checks could be done here
            #for now, just assume everything will be ok
            dates = vlist.returndatetimes()
            if plotwhich=='mag':
                data = vlist.returnmagnitudes()
            elif plotwhich=='x':
                data = vlist.returnx()
            elif plotwhich=='y':
                data=vlist.returny()
            elif plotwhich=='z':
                data=vlist.returnz()
            else:
                data=vlist.returnmagnitudes()
            '''
            print "data excerpt"
            for i in xrange(5):
                print dates[i],data[i],self.filename
            '''
            label = legend+' ('+plotwhich+')'
            if scatter:
                if [label,colour] in legend_colour_list_scatter:
                    ax.plot_date(dates,data,c=colour)
                else:
                    ax.plot_date(dates,data,c=colour,label=label)
                    legend_colour_list_scatter.append([label,colour])
            else: #ie. if line plot is selected
                dates_list=[]
                data_list=[]
                '''
                preprocess data so that for time gaps, a line isn't being drawn
                -so split the data up into chunks when this happens!
                '''
                total_entries=0
                for i in xrange(len(dates)-1):
                    dates2 = dates[i:i+2]
                    diff = (dates2[-1]-dates2[0])/np.timedelta64(1,'s')
                    if diff>100:#split data at this point!
                        dates_list.append(dates[total_entries:i+1])
                        data_list.append(data[total_entries:i+1])
                        total_entries+=len(dates_list[-1])
                if total_entries != len(dates):
                    dates_list.append(dates[total_entries:])
                    data_list.append(data[total_entries:])
                    if len(dates_list[-1])!=len(data_list[-1]):
                        print "Error, last plotted lists not of equal length!!"
                    total_entries+=len(dates_list[-1])
                for ds,da in zip(dates_list,data_list):
                    if [label,colour] in legend_colour_list_line:
                        ax.plot_date(ds,da,c=colour,fmt='-')
                    else:
                        ax.plot_date(ds,da,c=colour,label=legend,fmt='-')
                        legend_colour_list_line.append([label,colour]) 
        legend = ax.legend()
        ax.set_xlabel('Time')
        ax.set_ylabel('nT')
        if log:
            ax.set_yscale('log')
        figManager = plt.get_current_fig_manager()
        figManager.window.showMaximized()
        plt.gcf().autofmt_xdate()
        plt.show()
    def plotstds(self,vfiles,array,n=10,scatter=True,log=False,
                 threshold=0.5):
        global scatter_size,sc
        if VERBOSE:
            print "plotting stds"
            print "threshold:",threshold

        std_plot_lists = []
        std_frame = vfiles.stds.dropna()
        mask = std_frame['data']<threshold
        above_threshold = std_frame[~mask]
        below_threshold = std_frame[mask]
        if not above_threshold.empty:
            if VERBOSE:
                print "Above threshold not empty"
            above_threshold = above_threshold.sort_index()
            above_threshold = above_threshold[~above_threshold.index.duplicated()]
            #needed for processing the caa file this way for some reason
            #maybe overlapping data from two different orbits in the same file?
            index_times=above_threshold.index.values
            diffs=pd.Series(data=index_times[1:]-index_times[:-1],
                            index=index_times[1:])
            above_threshold['diffs']=diffs
            above_threshold['delta']=above_threshold['diffs']/pd.Timedelta(1,'s')
            interval_mask = above_threshold['delta']>5
            break_times = above_threshold[interval_mask].index
            std_plot_list_above = []
            for i in xrange(break_times.shape[0]):
                mask = above_threshold.index<break_times[i]
                std_plot_list_above.append(above_threshold[mask][['data']]) 
                mask2=above_threshold.index >= break_times[i]
                above_threshold = above_threshold[mask2]
            std_plot_list_above.append(above_threshold[['data']])
            #[[]] since 'data'
            #label needs to be retained for plotting
            std_plot_lists.append([std_plot_list_above,'r'])
    
        if not below_threshold.empty:
            if VERBOSE:
                print "Below threshold not empty"
            below_threshold = below_threshold.sort_index()
            below_threshold = below_threshold[~below_threshold.index.duplicated()]
            index_times=below_threshold.index.values
            diffs=pd.Series(data=index_times[1:]-index_times[:-1],
                            index=index_times[1:])
            below_threshold['diffs']=diffs
            below_threshold['delta']=below_threshold['diffs']/pd.Timedelta(1,'s')
            interval_mask = below_threshold['delta']>5
            break_times = below_threshold[interval_mask].index
            std_plot_list_below = []
            for i in xrange(break_times.shape[0]):
                mask = below_threshold.index<break_times[i]
                std_plot_list_below.append(below_threshold[mask][['data']]) 
                mask2 = below_threshold.index>=break_times[i]
                below_threshold = below_threshold[mask2]
            std_plot_list_below.append(below_threshold[['data']])
            std_plot_lists.append([std_plot_list_below,'g'])

        #labels = [','.join([entry[2],entry[3]]) for entry in array]
        #labels = '-'.join(set(labels))
        #array = [vlist,color,legend,plotwhich]
        f,ax = plt.subplots(2,1,sharex=True)
        legend_colour_list_scatter = []
        legend_colour_list_line = []
        legend_list_std_line = []
        std_label = 'std'
        for plot_list in std_plot_lists:
            frame_list = plot_list[0]
            colour = plot_list[1]
            for frame in frame_list:
                ds_std = frame.index.values
                da_std = frame['data'].values
                if PLOT_VERBOSE:
                    print "plotting"
                    print ds_std
                if std_label in legend_list_std_line:
                    ax[1].plot_date(ds_std,da_std,c=colour,fmt='-')
                else:
                    ax[1].plot_date(ds_std,da_std,c=colour,label=std_label,fmt='-')
                    legend_list_std_line.append(std_label) 
                
        for count,entry in enumerate(array):
            #print "entry ",entry
            vlist = entry[0]
            colour = entry[1]
            legend = entry[2]
            if len(entry)==4:
                plotwhich= entry[3]
            else:
                plotwhich = ''
            #checks could be done here
            #for now, just assume everything will be ok
            dates = vlist.returndatetimes()
            if len(dates):
                if plotwhich=='mag':
                    data = vlist.returnmagnitudes()
                elif plotwhich=='x':
                    data = vlist.returnx()
                elif plotwhich=='y':
                    data=vlist.returny()
                elif plotwhich=='z':
                    data=vlist.returnz()
                else:
                    data=vlist.returnmagnitudes()
                '''
                print "data excerpt"
                for i in xrange(5):
                    print dates[i],data[i],self.filename
                '''
                label = legend+' ('+plotwhich+')'
                if scatter:
                    if [label,colour] in legend_colour_list_scatter:
                        ax[0].plot_date(dates,data,c=colour)
                    else:
                        ax[0].plot_date(dates,data,c=colour,label=label)
                        legend_colour_list_scatter.append([label,colour])
                else: #ie. if line plot is selected
                    dates_list=[]
                    data_list=[]
                    '''
                    preprocess data so that for time gaps, a line isn't being drawn
                    -so split the data up into chunks when this happens!
                    '''
                    total_entries=0
                    for i in xrange(len(dates)-1):
                        dates2 = dates[i:i+2]
                        diff = (dates2[-1]-dates2[0])/np.timedelta64(1,'s')
                        if diff>100:#split data at this point!
                            dates_list.append(dates[total_entries:i+1])
                            data_list.append(data[total_entries:i+1])
                            total_entries+=len(dates_list[-1])
                    if total_entries != len(dates):
                        dates_list.append(dates[total_entries:])
                        data_list.append(data[total_entries:])
                        if len(dates_list[-1])!=len(data_list[-1]):
                            print "Error, last plotted lists not of equal length!!"
                        total_entries+=len(dates_list[-1])
                    for ds,da in zip(dates_list,data_list):
                        if [label,colour] in legend_colour_list_line:
                            ax[0].plot_date(ds,da,c=colour,fmt='-')
                        else:
                            ax[0].plot_date(ds,da,c=colour,label=label,fmt='-')
                            legend_colour_list_line.append([label,colour]) 
        
        legend = ax[0].legend()
        legend = ax[1].legend()
        
        ax[0].set_xlabel('Time')
        ax[0].set_ylabel('nT')
        ax[1].set_ylabel('nT')
        
        if log:
            ax[0].set_yscale('log')
            #ax[1].set_yscale('log')
        ax[0].set_title('Data for Spacecraft '+str(sc))
        ax[1].set_title('Standard Deviations of above data, over '+str(n)+' samples')
        plt.show()
        figManager = plt.get_current_fig_manager()
        figManager.window.showMaximized()
        plt.gcf().autofmt_xdate()
    def print_values(self,limit):
        print "filename:",self.filename
        print self.vectors.ix[:limit]
            
class vectorfiles:
    def __init__(self):
        self.array = []
        self.std_dates = []
        self.std_end_dates = []
        self.stds_list = []
        '''
        2 columns in the threshold_std dataframe
        column 0:start date of interval
        column 1:end date of interval
        '''
        self.std_data_raw =[]
        self.stds=pd.DataFrame()
    def isempty(self):
        for entry in self.array:
            vlist = entry[0 ]
            if not vlist.isempty():
                return False
        return True
    def add_vectorlist(self,vlist,color='red',legend='data',plotwhich='mag'):
        if not isinstance(vlist, vectorlist):
            raise Exception('Object supplied must be a vector list')
        else:         
            self.array.append([vlist,color,legend,plotwhich])
    def plotfiles(self,scatter=False,log=True,std=False,n=10,threshold=0.5):
        s = vectorlist()
        if std:
            s.plotstds(self,self.array,scatter=scatter,log=log,n=n,
                       threshold=threshold)
        else:
            s.plotlists(self.array,scatter=scatter,log=log)
    def printfiles(self):
        for array in self.array:
            print array[0].filename
    def prune(self,n=0,start_date=datetime(1,1,1),end_date=datetime(1,1,1),value=0,
              greater_than=False,
              inplace=True):
        if inplace:
            for entry in self.array:
                vlist = entry[0]
                vlist.prune(n=n,start_date=start_date,end_date=end_date,value=value,greater_than=greater_than)
            if VERBOSE:
                print "Done Pruning"
            return True
        else:
            vfile_copy = copy.deepcopy(self)
            for entry in vfile_copy.array:
                vlist = entry[0]
                vlist.prune(n=n,start_date=start_date,end_date=end_date,value=value,greater_than=greater_than)
            if VERBOSE:
                print "Done Pruning"
            return vfile_copy
    def return_vectors(self):
        vectors = pd.DataFrame()
        for entry in self.array:
            vlist = entry[0]
            vectors=pd.concat((vectors,vlist.vectors),axis=0)
        return vectors
    def write_to_csv(self,filepath):
        f = open(filepath,'wb')
        vectors = self.return_vectors()
        vectors.to_csv(f,date_format='%d/%m/%Y %H:%M:%S')
        f.close()
        return f.closed
    def calculate_stds(self,n=10,scatter=True,log=False):
        global sc
        if VERBOSE:
            print "Spacecraft:",sc
            print "STD samples:",n
        for count,entry in enumerate(self.array):
            #print "entry ",entry
            vlist = entry[0]
            if not vlist.vectors.empty:
                plotwhich= entry[3]
                vecs = vlist.vectors
                dummy = pd.DataFrame()
                dummy['times']=vecs.index
                dummy['times shifted']=dummy['times'].shift()
                dummy['delta']=(dummy['times']-dummy['times shifted'])/\
                                                pd.Timedelta(1,'s')
                mask = dummy['delta']>6
                indices = [0]
                indices.extend(dummy[mask].index.values.tolist())
                indices.append(dummy.index.max()+1)
                indices_list = [(i,j) for (i,j) in zip(indices[:-1],indices[1:]) if (j-i)>5*n]
                for (starti,endi) in indices_list:
                    #need to use iloc!!!
                    ######################
                    '''
                    standard deviation calculation below
                    '''
                    ######################
                    std_data = pd.DataFrame({'data':vecs[plotwhich].iloc[
                                            starti:endi]})
                    window_std=pd.rolling_std(std_data,window=n)
                    self.stds_list.append(window_std)
                    self.stds = pd.concat((self.stds,window_std),
                                          axis=0)
                    '''
                    index is the END DATE of the sampling window!!
                    '''
        self.stds.sort_index(inplace=True)          
        if VERBOSE:
            print "stds"
            print self.stds.head(20)
    def select_stds(self,threshold):
        if VERBOSE:
            print "threshold:",threshold
        if threshold==0:
            threshold=1e10
        threshold_std=pd.DataFrame()
        for stds in self.stds_list:
            stds=stds<threshold
            stds_shift_down = stds.shift(1)
            stds_shift_up = stds.shift(-1)
            mask_start = stds!=stds_shift_down
            mask_start= mask_start.values
            mask_end = stds!=stds_shift_up
            mask_end = mask_end.values
            if stds.iat[0,0]==False:
                start_dates = stds[mask_start].index.values[1::2]       
                end_dates = stds[mask_end].index.values[1::2]
            #the first value is never True since the first values in the stds
            #list are nans
            threshold_std_dict={'start':start_dates,'end':end_dates}
            new_entry_threshold_std = pd.DataFrame(threshold_std_dict,columns=[
                                                    'start','end'])
            threshold_std = pd.concat((threshold_std,new_entry_threshold_std),
                                      axis=0)
        if threshold_std.size:
            threshold_std.sort_values('start',inplace=True)
            threshold_std.reset_index(drop=True,inplace=True)
            return threshold_std,self.return_vectors() 
        else:
            print "No overlaps could be selected"
            return threshold_std,threshold_std

def write_to_logfile(errormsg,logdir=logdir):
    current_time = datetime.now().isoformat()
    errormsg=str(errormsg)
    filepath = logdir+'data_analysis.log'
    with open(filepath,'a') as f:
        f.write(current_time+' '+errormsg+'\n')
        
def process(vfiles,sc,start_date,end_date,input,prune_start=datetime(1,1,1),
            prune_end=datetime(1,1,1),prune_n=0,prune_value=0,
            prune_greater_than=False):
    #global prune_start,prune_end,prune_n,prune_value,prune_greater_than
    dirs = [[entry[0],entry[1]] for entry in input]
    colours = [entry[2] for entry in input]
    legends = [entry[3] for entry in input]
    plotwhichs=[entry[4] for entry in input] 
    dates = [start_date+timedelta(days=1)*i for i in xrange(abs((end_date-start_date).days)+1)]
    if VERBOSE:
        print "processing dates"
        print dates
    files = []
    for datev in dates:
        if VERBOSE:
            print ""
            print "processing, date"
            print datev.isoformat()
        Year = datev.year
        month = datev.month
        day = datev.day
        '''
        in case of caa files, files(s) are returned in a list, which is
        handled in the read_file function, which assumes caa data in the 
        case of the input being a list rather than a string
        '''
        for [dir,ext],colour,legend,plotwhich in zip(dirs,colours,legends,plotwhichs):
            if VERBOSE:
                print "getting file for"
                print sc,Year,month,day,dir,ext
            file = getfile(sc,Year,month,day,dir,ext=ext) #may return a list!
            if file:
                if VERBOSE:
                    print "filefound:",file
                if dir != caadir:
                    vlist = vectorlist()
                    vlist.read_file(file)
                    vfiles.add_vectorlist(vlist,colour,legend,plotwhich) 
                else:#ie. if caadir is directory!
                    for f in file:
                        if f not in files:
                            if VERBOSE:
                                print file
                                print "caa, already read: ",files
                                print "now reading: ",f
                            vlist = vectorlist()
                            vlist.read_file(f)
                            vfiles.add_vectorlist(vlist,colour,legend,plotwhich)                                       
                            files.append(f)
            else:
                errormsg = "No file(s) for the following input: "
                errormsg += "Directory: "+dir
                errormsg += " Extende Mode: "+str(ext)
                errormsg += " Date: "+datev.date().isoformat()
                write_to_logfile(errormsg)
    if vfiles.isempty():
        errormsg = "Couldn't find any data for the following [dir,ext_mode] "
        errormsg+=str(dirs)
        errormsg+= " Dates: "
        errormsg+=', '.join([d.date().isoformat() for d in dates])
        write_to_logfile(errormsg)
            
    if files and prune_start == datetime(1,1,1) and prune_end == datetime(1,1,1):
        if VERBOSE:
            print "Seting prune start and end in order to trim "\
                    +"to start and end times (due to caa)"
        prune_start=start_date
        prune_end=end_date+timedelta(days=1)
    if VERBOSE:
        print "Prune Start"
    if prune_start != datetime(1,1,1) and prune_end != datetime(1,1,1):
        if VERBOSE:
            print "Pruning Dates:",prune_start,prune_end
            vecs =vfiles.return_vectors()
            print vecs.head()
            print vecs.tail()
        vfiles.prune(start_date=prune_start,end_date=prune_end)
    if prune_n > 1:
        if VERBOSE:
            print "Pruning Points",prune_n
        vfiles.prune(n=prune_n)
    if prune_value > 0:
        if VERBOSE:
            print "Pruning Values",prune_value
        vfiles.prune(value=prune_value,greater_than=prune_greater_than)

def plot(vfiles,sc,start_date,end_date,input,std=True,scatter=True,n=10,
         threshold=0.5):
    #dirs = [[entry[0],entry[1]] for entry in input]
    #colours = [entry[2] for entry in input]
    #legends = [entry[3] for entry in input]
    plotwhichs=[entry[4] for entry in input] 
    #vfiles.printfiles()
    if 'x' in plotwhichs or 'y' in plotwhichs or 'z' in plotwhichs:
        log=False
    else:
        log=True
    vfiles.plotfiles(scatter=scatter,log=log,std=std,n=n,threshold=threshold)

def plot_timeseries():
    global vfiles
    plt.figure()
    mags=[]
    for entry in vfiles.array:
        vlist = entry[0]
        mags.extend(vlist.returnmagnitudes())   
    plt.scatter(np.linspace(0,len(mags),len(mags)),mags,s=80,c='r')
    ax = plt.gca()
    ax.set_yscale('log')
def remove_outliers():
    global vfiles
    newvfiles = vectorfiles()
    '''
    remove outlying values by filtering out the number of values in one ext mode
    data set, setting an upper limit - eg. 800 points per day for example
    
    if this is not enough, one could compile a list of the differences in the 
    mag field values, and if the differences between two points are too large,
    replace the point with something suitable, like the previous value
    + the previous normal difference, and then go from there.
    '''
    if VERBOSE:
        print "Vfiles before:",len(vfiles.array)
    for entry in vfiles.array:
        vlist = entry[0]
        mags = vlist.returnmagnitudes()
        #dates= vlist.returndatetimes()    
        if len(mags)>1300:
            newvfiles.add_vectorlist(vlist)
    vfiles = newvfiles
    if VERBOSE:
        print "Done selecting based on sample length"
        print "Vfiles after:",len(vfiles.array)
    if VERBOSE:
        print "Now selecting based on differences"
    diffarray = np.array([],dtype=np.float64).reshape(0,1)
    for entry in vfiles.array:
        vlist = entry[0]
        mags = vlist.returnmagnitudes()
        
        for i in xrange(5,len(mags)-10,1):
            mags[i]
            if abs(mags[i]-mags[i-1]) > 100 and abs(mags[i]-mags[i+1])>100:
                    mags[i] = np.mean(mags[i-5:i]+mags[i+1:i+10])
                    
        for mag,v in zip(mags,vlist.vectors):
            v.magnitude = mag
        vlist.vectors = vlist.vectors[5:]
        
    plt.figure()
    #plt.scatter(np.linspace(0,len(diffarray),len(diffarray)),diffarray)
    plt.hist(diffarray,bins=300)   
           
#filename = "Y:/reference/2015/12/C1_151231_B.EXT.GSE"
vfiles = vectorfiles()

sc=0
scatter_size = 10

def analyse(spacecraft=1,start_date=datetime(2016,1,1),end_date='',
            prune_start=datetime(1,1,1),prune_end=datetime(1,1,1),prune_n=0,
            prune_value = 0,input=[[refdir,1,'b','default','mag']],
            scatter_s=50,prune_greater_than=False,
            std_threshold=0,rm_outliers=0,std_n=50,PLOT=0,reprocess=1,
            scatter=False,vectorfile_storage=vfile_store(),plot_std=True):
    '''
    spacecraft    = spacecraft (1,2,3,4)    
    input = [[directory,extmode 0 or 1 (off or on), colour, legend (string), 
             whichdata ('mag','x','y','z')],[],[],...]
             available directories are: 
                        refdirahk114 = 'Y:/reference/'
                        refdir       = 'Z:/data/reference/' 
                        caadir       = 'Z:/caa/ic_archive/'
    start_date = time to start data analysis
    end_date   = time to end data analysis. If not supplied, only data for the start
                    date is analysed
    prune_start,prune_end variables allow for finer control of processed data
    after it has been collected
    
    all dates (ie. start_date, end_date, prune_start, prune_end) are expected
    to be given as a python datetime.datetime object.
    
    prune_n = minimum number of vectors in a given day
    prune_value = sets magnetic field value threshold (see below)
    prune_greater_than = True or False. If set to True, all datapoints above 
                        prune_value threshold are selected. If set to False,
                        all values below the threshold are selected
    scatter_s = an integer controlling the size of the scatter points plotted
    PLOT = plots scatter graphs of different stages of the data processing
    scatter = True or False - plot scatter or line plot
    rm_outliers = 0 or 1, depending on if outlying values should be removed
                for a smoother data set
    reprocess = 0 or 1, if set to 1 takes in new data depending on the dates
                selected.
    pickling = 0 or 1. If pickling is set to 1 and reprocess is set to 1,
                the program will write the collected data to a pickle file
                which can then be reloaded for faster data analysis should
                other parameters be changed afterwards. Thus, the second time 
                around, reprocess should be set to 0, and pickling should
                remain set at 1, so that the program loads the collected data
                from the pickle file instead of looking for the raw file.
                If data is pruned, this will be reflected in the pickle file
                as well, so
                
    In general, if the default parameter is not changed, the corresponding
    action will not be performed.
    #########################################################################
    Output:
    -dataframe containing start & end dates of intervals
    -all the vector data associated with the probed interval
    -the vectorfile_storage instance containing the vectofiles and 
    associated metadata for future use
    '''
    #global prune_start,prune_end,prune_n,prune_value,prune_greater_than
    #global refdirahk114,refdir,caadir
    global vfiles,sc,scatter_size
    sc=spacecraft
    scatter_size = scatter_s
    
    vfiles_store = vfile_store(start_date,end_date,prune_start,prune_end,prune_value,
                               input,prune_greater_than,std_n)
    ###############################################################################
    '''
    #default arguments
    prune_start=datetime(1,1,1)
    prune_end=datetime(1,1,1)
    prune_n=0
    prune_value = 0
    end_date = ''
    '''
    #User Input Variables
    #refdirahk114 = refdir
    #sc = sc
    '''
    #large pickle file!!
    start_date = datetime(2010,1,1)
    end_date = datetime(2014,8,10)
    '''
    #plt.close('all')
    
    #start_date = datetime(2016,1,2)
    #end_date  = datetime(2016,1,3)
    '''
    input = [directory,extmode 0 or 1 (off or on), colour, legend, whichdata ('mag','x','y','z')]
    '''
    '''
    input = [
             #[caadir,0,'r','caa','mag'],
             #[refdir,0,'g','def','y'],
             [refdir,1,'b','def','mag']
    ]
    '''
    ################
    '''
    pruning of output - fine date selection & point count reduction
    '''
    '''
    #prune_start = datetime(2015,1,1)
    #prune_end   = datetime(2015,5,1)
    #prune_n     = 20
    prune_greater_than = False
    prune_value = 40
    #################
    scatter_size = 50
    #################
    
    std_threshold = 1.2

    rm_outliers = 0
    
    #plot(vfiles,sc,start_date,end_date,input)
    
    std_n = 50
    PLOT = 1
    
    reprocess = 1
    
    pickling = 0
    '''
    ###############################################################################   
    if not vfiles_store.is_equal(vectorfile_storage):
        if VERBOSE:
            print "No previous vfiles"
        vfiles=vectorfiles()
        process(vfiles,sc,start_date,end_date,input,prune_start,prune_end,
                prune_n,prune_value,prune_greater_than)
        if vfiles.isempty():
            print "No vector data found for the following parameters:"
            print "sc:",spacecraft
            print "start:",start_date," (",prune_start,")"
            print "end:",end_date," (",prune_end,")"
            print "prunevalue:",prune_value
            print input         
        if rm_outliers:
            plot(vfiles,sc,start_date,end_date,input,n=std_n,scatter=scatter)
            remove_outliers()
            plot(vfiles,sc,start_date,end_date,input,n=std_n)
            
        vfiles.calculate_stds(n=std_n) 
        if VERBOSE:
            print "Storing vfiles",len(vfiles.array)  
            print ""
        vfiles_store.add_vectorfiles(vfiles)
    else:
        vfiles_store=vectorfile_storage
        vfiles=vectorfile_storage.get_vfiles()
        if VERBOSE:
            print "Using previous vfiles",len(vfiles.array)
    std_periods,vectors = vfiles.select_stds(threshold=std_threshold)
    if PLOT and not vfiles.isempty():
        plot(vfiles,sc,start_date,end_date,input,n=std_n,scatter=scatter,
             threshold=std_threshold,std=plot_std)
        #plot(vfiles,sc,start_date,end_date,input)
    #return vfiles.threshold_std,new
    return std_periods,vectors,vfiles_store

def generate_dataframe_plotting_list(dataframe):
    plot_list = []
    if not dataframe.empty:
        dataframe = dataframe.sort_index()
        times = dataframe.index.values
        diffs=pd.Series(data=times[1:]-times[:-1],
                        index=times[1:])
        delta = diffs/pd.Timedelta(1,'s')
        dataframe['delta']=delta
        interval_mask = dataframe['delta']>5
        break_times = dataframe[interval_mask].index
        plot_list = []
        for i in xrange(break_times.shape[0]):
            mask = dataframe.index<break_times[i]
            plot_list.append(dataframe[mask])
            dataframe = dataframe[~mask]
        plot_list.append(dataframe)
    return plot_list

def plot_x_pos_mag(scs,start,end,save_dir=imagedir,image_type='.pdf',save=False,
                   show=True,source='caa',dpi=330):
    assert len(scs)==2,"Need two spacecraft to compare!"
    if not '.' in image_type:
        image_type='.'+image_type
    dirs=[]
    if source=='default':
        dirs.append(refdir)
        dirs.append(refdir)
    elif source=='caa':
        dirs.append(caadir)
        dirs.append(refdirahk114caa)
    else:
        raise Exception("Select either 'default' or 'caa' as source")
    '''
    data collection
    '''
    start_date = pd.Timestamp(start).normalize().to_datetime()
    end_date = pd.Timestamp(end).normalize().to_datetime()
    prune_start = pd.Timestamp(start).to_datetime()
    prune_end = pd.Timestamp(end).to_datetime()
    vfiles = [vectorfiles(),vectorfiles()]
    for sc,vfile in zip(scs,vfiles):
        input = [[dirs[0],0,'','',''],[dirs[1],1,'','','']]
        process(vfile,sc,start_date,end_date,input,prune_start,prune_end,
                prune_value=0)
    if vfiles[0].isempty() or vfiles[1].isempty():
        print "No data could be collected - see log"
        return 0
    colour_dict = {'C1':'k','C2':'r','C3':'ForestGreen','C4':'Magenta'}
    plt.ioff()
    plt.style.use('classic')
    f,axes = plt.subplots(2,1,sharex=True,figsize=(23,13))
    labelsize=17.5
    axes[1].set_xlabel(r'$\mathrm{Time \ UTC}$',fontsize=labelsize)
    for vfile,axis in zip(vfiles,axes):
        axis2 = axis.twinx()
        axis2.set_ylabel(r'$\mathrm{GSE \ X \ (km)}$',
                                    fontsize=labelsize)
        axis.tick_params(axis='both',which='major',labelsize=14,pad=20)
        axis2.tick_params(axis='both',which='major',labelsize=14,pad=20)
        axis.set_ylabel(r'$\mathrm{\vert B \vert \ (nT)}$',fontsize=labelsize)
        axis.minorticks_on()
        axis2.minorticks_on()
        sc_string = vfile.array[0][0].filename.split('/')[-1][:2]
        axis.set_title('Cluster '+sc_string[1])
        vectors = vfile.return_vectors()
        dataframe = vectors[['mag','x_pos_gse']]
        if not dataframe.empty:
            dataframe = dataframe.sort_index()
            times = dataframe.index.values
            diffs=pd.Series(data=times[1:]-times[:-1],
                            index=times[1:])
            delta = diffs/pd.Timedelta(1,'s')
            dataframe['delta']=delta
            interval_mask = dataframe['delta']>5
            break_times = dataframe[interval_mask].index
            plot_list = []
            for i in xrange(break_times.shape[0]):
                mask = dataframe.index<break_times[i]
                plot_list.append(dataframe[mask])
                dataframe = dataframe[~mask]
            plot_list.append(dataframe)
            for frame in plot_list:
                axis.plot_date(frame.index,frame['mag'],fmt='-',
                               c=colour_dict[sc_string])
                axis2.plot_date(frame.index,frame['x_pos_gse'],fmt='-',
                                c='b')
            axis.set_yscale('log')
            for tl in axis.get_yticklabels():
                tl.set_color(colour_dict[sc_string])
            for tl in axis2.get_yticklabels():
                tl.set_color('b')
    if save:
        filename='mag_gse_x_'+prune_start.strftime("%Y%m%dT%H%M%S")+\
                  '__'+prune_end.strftime("%Y%m%dT%H%M%S")+image_type
        plt.savefig(save_dir+filename,dpi=dpi,bbox_inches='tight',pad_inches=0.4)
    if show:
        figManager = plt.get_current_fig_manager()
        figManager.window.showMaximized()
        plt.show()
    else:
        plt.close()
def plot_axis(array,ax,plotwhich_override=''):
    legend_colour_list_line = []
    for count,entry in enumerate(array):
        #print "entry ",entry
        vlist = entry[0]
        colour = entry[1]
        legend = entry[2]
        if plotwhich_override != '':
            plotwhich = plotwhich_override
        else:
            plotwhich= entry[3]
        dates = vlist.returndatetimes()
        if plotwhich=='mag':
            data = vlist.returnmagnitudes()
        elif plotwhich=='x':
            data = vlist.returnx()
        elif plotwhich=='y':
            data=vlist.returny()
        elif plotwhich=='z':
            data=vlist.returnz()
        else:
            raise Exception("I need to know what to plot")
        #label = legend+' ('+plotwhich+')'+' mean: '+format(np.mean(data),'.3e')
        label = (legend+'mean: '+format(np.mean(data),'.2e')+' nT'
                ', std: '+format(np.std(data),'.2e')+' nT')
        dates_list=[]
        data_list=[]
        '''
        preprocess data so that for time gaps, a line isn't being drawn
        -so split the data up into chunks when this happens!
        '''
        total_entries=0
        for i in xrange(len(dates)-1):
            dates2 = dates[i:i+2]
            diff = (dates2[-1]-dates2[0])/np.timedelta64(1,'s')
            if diff>20:#split data at this point!
                dates_list.append(dates[total_entries:i+1])
                data_list.append(data[total_entries:i+1])
                total_entries+=len(dates_list[-1])
        if total_entries != len(dates):
            dates_list.append(dates[total_entries:])
            data_list.append(data[total_entries:])
            if len(dates_list[-1])!=len(data_list[-1]):
                print "Error, last plotted lists not of equal length!!"
            total_entries+=len(dates_list[-1])
        for ds,da in zip(dates_list,data_list):
            if [label,colour] in legend_colour_list_line:
                ax.plot_date(ds,da,c=colour,fmt='-')
            else:
                ax.plot_date(ds,da,c=colour,label=label,fmt='-')
                legend_colour_list_line.append([label,colour])            
    legend = ax.legend(loc='best',fontsize=14) 
        
def plotting(scs,start_date,end_date,plotwhichs,source='caa'):  
    plt.ioff()
    colour_dict = {1:'Black',2:'Red',3:'Green',4:'Magenta'}
    if type(scs) == int or type(scs) == float:
        scs = [int(scs)]
    if plotwhichs == 'all' or plotwhichs =='ALL':
        plotwhichs = ['x','y','z','mag']
    elif type(plotwhichs)==str:
        plotwhichs=[plotwhichs]

    start = pd.Timestamp(start_date).normalize().to_datetime()
    end = pd.Timestamp(end_date).normalize().to_datetime()
    prune_start = start_date
    if start_date==end_date:
        prune_end = end_date+timedelta(days=1)
    else:
        prune_end = end_date
        
    if source=='default':
        ext_dir = refdir
        norm_dir = refdir
    elif source=='caa':
        ext_dir = refdirahk114caa
        norm_dir = caadir
    else:
        raise Exception("Select either 'default' or 'caa' as source")
    vfiles = {}
    for sc in scs:
        for ext_mode,dir in enumerate([norm_dir,ext_dir]):
            input = [[dir,ext_mode,'','','']]
            vfile = vectorfiles()
            process(vfile,sc,start,end,input,prune_start,prune_end)
            vfiles[str(sc)+str(ext_mode)]=vfile
    rows = len(plotwhichs)
    columns = len(scs)
    labelsize=17.5
    #fig, axarr = plt.subplots(rows,columns,sharex=True,sharey=True,figsize=(23,13))
    fig = plt.figure()
    if rows==1 and columns==1:
        axarr = fig.add_subplot(1,1,1)
    elif rows==1:
        axarr = []
        for i in range(columns):
            if i==0:
                axarr.append(fig.add_subplot(1,columns,i+1))
            else:
                axarr.append(fig.add_subplot(1,columns,i+1,sharex=axarr[0]
                                                        ,sharey=axarr[0]))
    elif columns==1:
        axarr = []
        for i in range(rows):
            if i==0:
                axarr.append(fig.add_subplot(rows,1,i+1))
            else:
                axarr.append(fig.add_subplot(rows,1,i+1,sharex=axarr[0]))
    else:
        axarr=[]
        axarr_count = 1
        for i in range(rows):
            axarr.append([])
            for j in range(columns):
                if j==0 and i==0:
                    axarr[-1].append(fig.add_subplot(rows,columns,axarr_count))
                elif j==0:
                    axarr[-1].append(fig.add_subplot(rows,columns,axarr_count,
                                                            sharex=axarr[0][0]))
                else:
                    axarr[-1].append(fig.add_subplot(rows,columns,axarr_count,
                                        sharex=axarr[0][0],sharey=axarr[-1][0]))
                axarr_count += 1
    if rows ==1 and columns==1:
        ax = axarr
        plotwhich = plotwhichs[0]
        ax.set_xlabel(r'$\mathrm{Time \ UTC}$',fontsize=labelsize)
        if plotwhich == 'x':
            ax.set_ylabel(r'$\mathrm{B_x \ (nT)}$',fontsize=labelsize)
        elif plotwhich == 'y':
            ax.set_ylabel(r'$\mathrm{B_y \ (nT)}$',fontsize=labelsize)
        elif plotwhich == 'z':
            ax.set_ylabel(r'$\mathrm{B_z \ (nT)}$',fontsize=labelsize)
        elif plotwhich == 'mag':
            ax.set_ylabel(r'$\mathrm{\vert B \vert \ (nT)}$',
                        fontsize=labelsize)
    elif rows == 1:
        for ax in axarr:
            ax.set_xlabel(r'$\mathrm{Time \ UTC}$',fontsize=labelsize) 
        ax = axarr[0]
        plotwhich = plotwhichs[0]
        ax.set_xlabel(r'$\mathrm{Time \ UTC}$',fontsize=labelsize)
        if plotwhich == 'x':
            ax.set_ylabel(r'$\mathrm{B_x \ (nT)}$',fontsize=labelsize)
        elif plotwhich == 'y':
            ax.set_ylabel(r'$\mathrm{B_y \ (nT)}$',fontsize=labelsize)
        elif plotwhich == 'z':
            ax.set_ylabel(r'$\mathrm{B_z \ (nT)}$',fontsize=labelsize)
        elif plotwhich == 'mag':
            ax.set_ylabel(r'$\mathrm{\vert B \vert \ (nT)}$',
                        fontsize=labelsize)     
    elif columns==1:
        ax = axarr[-1]
        ax.set_xlabel(r'$\mathrm{Time \ UTC}$',fontsize=labelsize)
        for ax,plotwhich in zip(axarr,plotwhichs):
            if plotwhich == 'x':
                ax.set_ylabel(r'$\mathrm{B_x \ (nT)}$',fontsize=labelsize)
            elif plotwhich == 'y':
                ax.set_ylabel(r'$\mathrm{B_y \ (nT)}$',fontsize=labelsize)
            elif plotwhich == 'z':
                ax.set_ylabel(r'$\mathrm{B_z \ (nT)}$',fontsize=labelsize)
            elif plotwhich == 'mag':
                ax.set_ylabel(r'$\mathrm{\vert B \vert \ (nT)}$',
                            fontsize=labelsize)
    else:
        for ax in axarr[-1]:
            ax.set_xlabel(r'$\mathrm{Time \ UTC}$',fontsize=labelsize)
        first_columns_axes = [axes[0] for axes in axarr]
        for ax,plotwhich in zip(first_columns_axes,plotwhichs):
            if plotwhich == 'x':
                ax.set_ylabel(r'$\mathrm{B_x \ (nT)}$',fontsize=labelsize)
            elif plotwhich == 'y':
                ax.set_ylabel(r'$\mathrm{B_y \ (nT)}$',fontsize=labelsize)
            elif plotwhich == 'z':
                ax.set_ylabel(r'$\mathrm{B_z \ (nT)}$',fontsize=labelsize)
            elif plotwhich == 'mag':
                ax.set_ylabel(r'$\mathrm{\vert B \vert \ (nT)}$',
                            fontsize=labelsize)
    #axarr indexed via [row][column]
    
    for column,sc in enumerate(scs):
        for row,plotwhich in enumerate(plotwhichs):
            if columns==1 and rows==1:
                ax=axarr
            elif columns==1:
                ax=axarr[row]
            elif rows==1:
                ax=axarr[column]
            else:
                ax=axarr[row][column]
            lines = []
            labels = []
            for ext_mode in range(2):
                vfile_index = str(sc)+str(ext_mode)
                vfile = vfiles[vfile_index]
                vectors = vfile.return_vectors()
                if ext_mode:
                    label = 'ext mode'
                    colour = 'DarkOrange'
                else:
                    label = 'normal mode'
                    colour = colour_dict[sc]
                plotting_list = generate_dataframe_plotting_list(vectors)
                for frame in plotting_list:
                    line,=ax.plot_date(frame.index.values,
                            frame[plotwhich],fmt='-',c=colour)
                if plotting_list:
                    lines.append(line)
                    labels.append(label)
            '''
            if lines and labels:
                if len(lines)==1 and len(labels)==1:
                    lines = (lines[0],)
                    labels = (labels[0],)
                ax.legend((lines),(labels),loc='best')
            '''
    
    #plt.tight_layout()
    figManager = plt.get_current_fig_manager()
    figManager.window.showMaximized()
    plt.show()
    
def plot_xyz(series,save=False,dpi=300,image_type='.pdf',prune=True,show=True,
             source='caa',save_dir=imagedir):
    '''
    Takes a row (so, a series) from the overlap_data DataFrame as its input
    and uses the values contained within to identify which things to plot
    '''
    plt.ioff()
    plt.style.use('classic')
    if not '.' in image_type:
        image_type='.'+image_type
    plotwhichs=['x','y','z']
    start_date = series.start.normalize().to_datetime()
    end_date = series.end.normalize().to_datetime()
    dirs=[]
    if not prune:
        prune_start=datetime(1,1,1)
        prune_end=datetime(1,1,1)
    else:
        prune_start = series.start.to_datetime()
        prune_end = series.end.to_datetime()        
    if source=='default':
        legends = ['default','ext mode default']
        dirs.append(refdir)
        dirs.append(refdir)
    elif source=='caa':
        dirs.append(caadir)
        dirs.append(refdirahk114caa)
        legends = ['','ext mode ']
    else:
        raise Exception("Select either 'default' or 'caa' as source")
    colours = ['g','r']
    scs=map(int,[series.non_ext_sc+1,series.ext_sc+1])
    vfiles = [vectorfiles(),vectorfiles()]
    '''
    data collection
    '''
    for (ext_mode,(dir,vfile,sc,colour,legend)) in enumerate(zip(dirs,vfiles,
                                                        scs,colours,legends)):
        input = [[dir,ext_mode,colour,legend,'']]
        process(vfile,sc,start_date,end_date,input,prune_start,prune_end)
    if vfiles[0].isempty() or vfiles[1].isempty():
        print "No data could be collected - see log"
        return 0
    '''
    difference of mean calculation
    '''
    non_ext_mode_vecs = vfiles[0].return_vectors()
    ext_mode_vecs = vfiles[1].return_vectors()
    differences = []
    for plotwhich in plotwhichs:
        difference = np.mean(non_ext_mode_vecs[plotwhich])-\
                        np.mean(ext_mode_vecs[plotwhich])
        differences.append(difference)
    f,axarr = plt.subplots(3,1,sharex=True,figsize=(23,13))
    labelsize=17.5
    axarr[2].set_xlabel(r'$\mathrm{Time \ UTC}$',fontsize=labelsize)
    axarr[0].set_ylabel(r'$\mathrm{B_x \ (nT)}$',fontsize=labelsize)
    axarr[1].set_ylabel(r'$\mathrm{B_y \ (nT)}$',fontsize=labelsize)
    axarr[2].set_ylabel(r'$\mathrm{B_z \ (nT)}$',fontsize=labelsize)
    for (plotwhich,ax,difference) in zip(plotwhichs,axarr,differences):
        ax.grid(True,which='major',color='0.6',linestyle='-',
                alpha=0.7,axis='y')
        #ax.grid(True,which='minor',color='k',linestyle='-',alpha=0.1)
        ax.tick_params(axis='both',which='major',labelsize=14,pad=20)
        ax.minorticks_on()
        ax.set_title(('mean difference (normal-ext): '
                                '{:.3e} nT').format(difference),fontsize=16)
        plot_axis(vfiles[0].array,ax,plotwhich_override=plotwhich)
        plot_axis(vfiles[1].array,ax,plotwhich_override=plotwhich)
    #plt.gcf().autofmt_xdate() #angles the date labels
    if not prune:
        prune_start=start_date
        prune_end=end_date
        if prune_start == prune_end:
            prune_end += timedelta(days=1)
    title_string = "From "+prune_start.strftime("%d %B %Y %H:%M:%S")\
                    +" to "+prune_end.strftime("%d %B %Y %H:%M:%S")\
                    +" with Cluster "+str(scs[0])+" in normal mode"\
                    +" and Cluster "+str(scs[1])+" in extended mode"\
                    +" ("+source+" calibration)"
    plt.suptitle(title_string,fontsize=15.5)
    if save:
        filename='xyz_'+prune_start.strftime("%Y%m%dT%H%M%S")+\
                  '__'+prune_end.strftime("%Y%m%dT%H%M%S")+image_type
        f.savefig(save_dir+filename,dpi=dpi,bbox_inches='tight',pad_inches=0.4)
    if show:
        figManager = plt.get_current_fig_manager()
        figManager.window.showMaximized()
        plt.show()
    else:
        plt.close()

def plot_mag_xyz(series,save=False,dpi=300,image_type='.pdf',prune=True,
                 show=True,source='caa',save_dir=imagedir):
    '''
    Takes a row (so, a series) from the overlap_data DataFrame as its input
    and uses the values contained within to identify which things to plot
    '''
    plt.ioff()
    plt.style.use('classic')
    if not '.' in image_type:
        image_type='.'+image_type
    plotwhichs=['x','y','z','mag']
    start_date = series.start.normalize().to_datetime()
    end_date = series.end.normalize().to_datetime()
    dirs=[]
    if not prune:
        prune_start=datetime(1,1,1)
        prune_end=datetime(1,1,1)
    else:
        prune_start = series.start.to_datetime()
        prune_end = series.end.to_datetime()        
    if source=='default':
        legends = ['default','ext mode default']
        dirs.append(refdir)
        dirs.append(refdir)
    elif source=='caa':
        dirs.append(caadir)
        dirs.append(refdirahk114caa)
        legends = ['','ext mode ']
    else:
        raise Exception("Select either 'default' or 'caa' as source")
    colours = ['g','r']
    scs=map(int,[series.non_ext_sc+1,series.ext_sc+1])
    vfiles = [vectorfiles(),vectorfiles()]
    '''
    data collection
    '''
    for (ext_mode,(dir,vfile,sc,colour,legend)) in enumerate(zip(dirs,vfiles,
                                                        scs,colours,legends)):
        input = [[dir,ext_mode,colour,legend,'']]
        process(vfile,sc,start_date,end_date,input,prune_start,prune_end)
    if vfiles[0].isempty() or vfiles[1].isempty():
        print "No data could be collected - see log"
        return 0    
    '''
    difference of mean calculation
    '''
    non_ext_mode_vecs = vfiles[0].return_vectors()
    ext_mode_vecs = vfiles[1].return_vectors()
    differences = []
    for plotwhich in plotwhichs:
        difference = np.mean(non_ext_mode_vecs[plotwhich])-\
                        np.mean(ext_mode_vecs[plotwhich])
        differences.append(difference)
    f,axarr = plt.subplots(2,2,sharex=True,figsize=(23,13))
    labelsize=17.5
    axarr[1][0].set_xlabel(r'$\mathrm{Time \ UTC}$',fontsize=labelsize)
    axarr[1][1].set_xlabel(r'$\mathrm{Time \ UTC}$',fontsize=labelsize)
    axarr = np.ravel(axarr)
    axarr[0].set_ylabel(r'$\mathrm{B_x \ (nT)}$',fontsize=labelsize)
    axarr[1].set_ylabel(r'$\mathrm{B_y \ (nT)}$',fontsize=labelsize)
    axarr[2].set_ylabel(r'$\mathrm{B_z \ (nT)}$',fontsize=labelsize)
    axarr[3].set_ylabel(r'$\mathrm{\vert B \vert \ (nT)}$',fontsize=labelsize)
    for (plotwhich,ax,difference) in zip(plotwhichs,axarr,differences):
        ax.grid(True,which='major',color='0.6',linestyle='-',
                alpha=0.7,axis='y')
        #ax.grid(True,which='minor',color='k',linestyle='-',alpha=0.1)
        ax.tick_params(axis='both',which='major',labelsize=14,pad=20)
        ax.minorticks_on()
        ax.set_title(('mean difference (normal-ext): '
                                '{:.3e} nT').format(difference),fontsize=16)
        plot_axis(vfiles[0].array,ax,plotwhich_override=plotwhich)
        plot_axis(vfiles[1].array,ax,plotwhich_override=plotwhich)
    #plt.gcf().autofmt_xdate() #angles the date labels
    if not prune:
        prune_start=start_date
        prune_end=end_date
        if prune_start == prune_end:
            prune_end += timedelta(days=1)
    title_string = "From "+prune_start.strftime("%d %B %Y %H:%M:%S")\
                    +" to "+prune_end.strftime("%d %B %Y %H:%M:%S")\
                    +" with Cluster "+str(scs[0])+" in normal mode"\
                    +" and Cluster "+str(scs[1])+" in extended mode"\
                    +" ("+source+" calibration)"
    plt.suptitle(title_string,fontsize=15.5)
    #plt.tight_layout()
    if save:
        filename='mag_xyz_'+prune_start.strftime("%Y%m%dT%H%M%S")+\
                  '__'+prune_end.strftime("%Y%m%dT%H%M%S")+image_type
        f.savefig(save_dir+filename,dpi=dpi,bbox_inches='tight',pad_inches=0.4)
    if show:
        figManager = plt.get_current_fig_manager()
        figManager.window.showMaximized()
        plt.show()
    else:
        plt.close()

def return_ext_data(sc,start_date,end_date,source='caa'):
    start = pd.Timestamp(start_date).normalize().to_datetime()
    end = pd.Timestamp(end_date).normalize().to_datetime()
    prune_start=start_date
    prune_end = end_date
    if source=='caa':
        input=[[refdirahk114caa,1,'','','']]
    else:
        raise Exception("Only caa source supported")
    vfiles=vectorfiles()
    process(vfiles,sc,start,end,input,prune_start,prune_end)
    return vfiles.return_vectors()
  
def return_normal_data(sc,start_date,end_date,source='caa'):
    start = pd.Timestamp(start_date).normalize().to_datetime()
    end = pd.Timestamp(end_date).normalize().to_datetime()
    prune_start=start_date
    prune_end = end_date
    if source=='caa':
        input=[[caadir,0,'','','']]
    else:
        raise Exception("Only caa source supported")
    vfiles=vectorfiles()
    process(vfiles,sc,start,end,input,prune_start,prune_end)
    return vfiles.return_vectors()
    
def return_vectors_from_vfiles(vfiles,start='',end=''):
    if type(vfiles) != list:
        vfiles = [vfiles]
    vecs=pd.DataFrame()
    for vfile in vfiles:
        if start != '' and end != '':
            vfile.prune(start_date=start,end_date=end)
        vecs = pd.concat((vecs,vfile.return_vectors()),axis=0)
    return vecs
    
def update_interval_files(series,result_dir,differences,coords):
    diff_keys = ['x_mean_diff_(normal-ext)','y_mean_diff_(normal-ext)',
                 'z_mean_diff_(normal-ext)','mag_mean_diff_(normal-ext)']
    coord_keys = coords.index.tolist()
    interval_file = 'intervals.xlsx'
    interval_frame = 'intervals.pickle'
    pickle_path = result_dir+interval_frame
    path = result_dir+interval_file
    if os.path.isfile(path):
        intervals = pd.read_excel(path)
        intervals.columns = ['start',
                             'end',
                             'duration (h)',
                             'std',
                             'max',
                             'min',
                             'mean',
                             'ext_sc',
                             'non_ext_sc']+diff_keys+coord_keys
    else:
        intervals = pd.DataFrame()
    use = ['start',
         'end',
         'duration (h)',
         'std',
         'max',
         'min',
         'mean',
         'ext_sc',
         'non_ext_sc']
    series = series[use]
    series.set_value('ext_sc',series['ext_sc']+1)
    series.set_value('non_ext_sc',series['non_ext_sc']+1)
    series = series.append(pd.Series(differences,index=diff_keys))
    series = series.append(coords)
    intervals = intervals.append(series,ignore_index=True)
    intervals.drop_duplicates(inplace=True,subset=['start','end',
                                                   'ext_sc','non_ext_sc'])
    intervals.sort_values('start',inplace=True)
    #intervals.reset_index(drop=True,inplace=True)
    intervals.to_excel(path,sheet_name='Intervals',
                       index=False,header=['start',
                             'end',
                             'duration (h)',
                             'std (DEFAULT CAL) (nT)',
                             'max (DEFAULT CAL) (nT)',
                             'min (DEFAULT CAL) (nT)',
                             'mean (DEFAULT CAL) (nT)',
                             'ext_sc',
                             'non_ext_sc']
                             +[key+' (nT)' for key in diff_keys]
                             +[key+' (km)' for key in coord_keys],
                            columns=['start',
                             'end',
                             'duration (h)',
                             'std',
                             'max',
                             'min',
                             'mean',
                             'ext_sc',
                             'non_ext_sc']+diff_keys+coord_keys)  
    '''
    for legacy reasons, need to reset the spacecraft numbers to comply with
    the methods that all add 1. This should be changed in future revisions!
    '''
    intervals['ext_sc'] = intervals['ext_sc'].add(-1)
    intervals['non_ext_sc'] = intervals['non_ext_sc'].add(-1)
    with open(pickle_path,'wb') as f:    
        pickle.dump(intervals,f,protocol=2)
        
def dt_to_strings(dt):
    return str(dt.year),format(dt.month,'02d'),format(dt.day,'02d')

def dt_time_to_strings(dt):
    return format(dt.hour,'02d')+'-'+format(dt.minute,'02d')+'-'+format(dt.second,'02d')
    
def package_data(series,dpi=300,image_type='.pdf',source='caa',
                 result_dir='Y:/overlap_stats/results_caa/'):
    '''
    Takes a row (so, a series) from the overlap_data DataFrame as its input
    and uses the values contained within to identify which things to plot,
    both using the plot_xyz and the plot_mag_xyz functions. The relevant data
    is also written to two files, for the extended mode and normal mode data.
    The two figure files and two data files are saved in their own 
    directory.
    '''
    start_date = series.start.normalize().to_datetime()
    end_date = series.end.normalize().to_datetime()
    dirs=[]
    prune_start = series.start.to_datetime()
    prune_end = series.end.to_datetime()        
    if source=='default':
        legends = ['','']
        dirs.append(refdir)
        dirs.append(refdir)
    elif source=='caa':
        dirs.append(caadir)
        dirs.append(refdirahk114caa)
        legends = ['','']
    else:
        raise Exception("Select either 'default' or 'caa' as source")
    colours = ['','']
    plotwhichs=['x','y','z','mag']
    scs=map(int,[series.non_ext_sc+1,series.ext_sc+1])
    vfiles = [vectorfiles(),vectorfiles()]
    '''
    data collection
    '''
    for (ext_mode,(dir,vfile,sc,colour,legend)) in enumerate(zip(dirs,vfiles,
                                                        scs,colours,legends)):
        input = [[dir,ext_mode,colour,legend,'']]
        process(vfile,sc,start_date,end_date,input,prune_start,prune_end)
    if vfiles[0].isempty() or vfiles[1].isempty():
        print "No data could be collected - see log"
        return 0    
    '''
    difference of mean calculation
    '''
    non_ext_mode_vecs = vfiles[0].return_vectors()
    ext_mode_vecs = vfiles[1].return_vectors()
    differences = []
    for plotwhich in plotwhichs:
        difference = np.mean(non_ext_mode_vecs[plotwhich])-\
                        np.mean(ext_mode_vecs[plotwhich])
        differences.append(difference)   
    coords = OrderedDict()
    for coord in ['x_pos_gse','y_pos_gse','z_pos_gse']:
        coords[coord+'_non_ext_mean'] = np.mean(non_ext_mode_vecs[coord])
        coords[coord+'_non_ext_max'] = np.max(non_ext_mode_vecs[coord])
        coords[coord+'_non_ext_min'] = np.min(non_ext_mode_vecs[coord])
        coords[coord+'_ext_mean'] = np.mean(ext_mode_vecs[coord])
        coords[coord+'_ext_max'] = np.max(ext_mode_vecs[coord])
        coords[coord+'_ext_min'] = np.min(ext_mode_vecs[coord])
        coords[coord+'_mean_diff_(normal-ext)'] = coords[coord+'_non_ext_mean']-\
                                coords[coord+'_ext_mean']
    coords = pd.Series(coords)
    Year,month,day = dt_to_strings(prune_start)
    directory = result_dir+Year+'/'+month+'/'
    for i in range(0,100):
        newdir = directory+format(i,'03d')+'__'+Year+'_'+month+'_'+day+'T'+\
                                        dt_time_to_strings(prune_start)+'/'
        if not os.path.isdir(newdir):
            os.makedirs(newdir)
            break
    directory=newdir
    plot_xyz(series,save=True,dpi=dpi,image_type=image_type,show=False,
             source=source,save_dir=directory)
    plot_mag_xyz(series,save=True,dpi=dpi,image_type=image_type,show=False,
             source=source,save_dir=directory) 
    plot_x_pos_mag(scs,prune_start-timedelta(days=3),prune_end,
                   save_dir=directory,image_type=image_type,show=False,
                   save=True,dpi=dpi,source=source)
    for ((ext_mode,dir),vfile) in zip(enumerate(dirs),vfiles):
        if ext_mode:
            ext_mode_label = 'extended_mode'
        else:
            ext_mode_label = 'normal_mode'
        filename = ext_mode_label+'_'+source+'_'+prune_start.strftime("%Y%m%dT%H%M%S")+\
                  '__'+prune_end.strftime("%Y%m%dT%H%M%S")
        vfile.write_to_csv(directory+filename+'.csv')
    update_interval_files(series,result_dir,differences,coords)

def surrounding_data_plot(series,dpi=300,image_type='.pdf',source='caa',
                 result_dir='Y:/overlap_stats/results_caa/'):
    '''
    2 hours around interval!
    '''
    colour_dict = {1:'k',2:'r',3:'ForestGreen',4:'Magenta'}
    if source=='default':
        dir = refdir
    elif source=='caa':
        dir = caadir
    else:
        raise Exception("Select either 'default' or 'caa' as source")
    
    start_date = series.start.normalize().to_datetime()-timedelta(days=1)
    end_date = series.end.normalize().to_datetime()+timedelta(days=1)
    prune_start = series.start.to_datetime()
    prune_end = series.end.to_datetime()
    Year,month,day = dt_to_strings(prune_start)
    directory = result_dir+Year+'/'+month+'/'
    for i in range(0,100):
        newdir = directory+format(i,'03d')+'__'+Year+'_'+month+'_'+day+'T'+\
                                        dt_time_to_strings(prune_start)+'/'
        if not os.path.isdir(newdir):
            os.makedirs(newdir)
            break
    directory=newdir      
    plotwhichs=['x','y','z']
    ext_mode = 0
    scs=range(1,5)
    
    start=prune_end
    end = prune_end+timedelta(hours=10)
    
    labelsize=17.5
    fig,axarr = plt.subplots(3,1,sharex=True,figsize = (23,13))
    fig.suptitle('Normal Mode Data after ('+source+' cal)')
    axarr[2].set_xlabel(r'$\mathrm{Time \ UTC}$',fontsize=labelsize)
    axarr[0].set_ylabel(r'$\mathrm{B_x \ (nT)}$',fontsize=labelsize)
    axarr[1].set_ylabel(r'$\mathrm{B_y \ (nT)}$',fontsize=labelsize)
    axarr[2].set_ylabel(r'$\mathrm{B_z \ (nT)}$',fontsize=labelsize)
    for sc in scs:
        vfile = vectorfiles()
        input = [[dir,ext_mode,'','','']]
        process(vfile,sc,start_date,end_date,input,prune_start=start,
                                                    prune_end=end)  
        vecs = vfile.return_vectors()
        times = vecs.index.values
        for ax,coord in zip(axarr,plotwhichs):
            ax.plot_date(times,vecs[coord],fmt='-',c=colour_dict[sc])
            ax.grid(True,which='major',color='0.6',linestyle='-',
                    alpha=0.7,axis='y')
            #ax.grid(True,which='minor',color='k',linestyle='-',alpha=0.1)
            ax.tick_params(axis='both',which='major',labelsize=14,pad=20)
            ax.minorticks_on()
    
    start=prune_start-timedelta(hours=10)
    end = prune_start
    
    labelsize=17.5
    fig,axarr = plt.subplots(3,1,sharex=True,figsize = (23,13))
    fig.suptitle('Normal Mode Data before ('+source+' cal)')
    axarr[2].set_xlabel(r'$\mathrm{Time \ UTC}$',fontsize=labelsize)
    axarr[0].set_ylabel(r'$\mathrm{B_x \ (nT)}$',fontsize=labelsize)
    axarr[1].set_ylabel(r'$\mathrm{B_y \ (nT)}$',fontsize=labelsize)
    axarr[2].set_ylabel(r'$\mathrm{B_z \ (nT)}$',fontsize=labelsize)
    for sc in scs:
        vfile = vectorfiles()
        input = [[dir,ext_mode,'','','']]
        process(vfile,sc,start_date,end_date,input,prune_start=start,
                                                    prune_end=end)  
        vecs = vfile.return_vectors()
        times = vecs.index.values
        for ax,coord in zip(axarr,plotwhichs):
            ax.plot_date(times,vecs[coord],fmt='-',c=colour_dict[sc])
            ax.grid(True,which='major',color='0.6',linestyle='-',
                    alpha=0.7,axis='y')
            #ax.grid(True,which='minor',color='k',linestyle='-',alpha=0.1)
            ax.tick_params(axis='both',which='major',labelsize=14,pad=20)
            ax.minorticks_on()           
    plt.show()
            
#prune_start = datetime(2015,12,21,10,0,0)
#prune_end = datetime(2015,12,21,19,0,0)
#to get all of the relevant caa data, need to start from 3-4 days 
#earlier than the first day of interest in extreme cases, since the
#caa data is grouped by orbit times
#this is now done in the process function
'''
input=[[caadir,0,'g','caa','mag'],[refdirahk114caa,1,'r','ext mode caa','mag']]
output = analyse(spacecraft=3,input=input,start_date=datetime(2015,12,20),
                 end_date=datetime(2015,12,26),std_n=10,
                 PLOT=True, scatter=False,std_threshold=1.,
                 prune_value = 0,prune_start=prune_start,prune_end=prune_end
                 )

input=[[refdir,1,'r','ext mode default','mag'],[refdir,0,'b','default','mag']]
output = analyse(spacecraft=3,input=input,start_date=datetime(2015,12,20),
                 end_date=datetime(2015,12,26),std_n=10,
                 PLOT=True, scatter=False,std_threshold=1.,
                 prune_value = 0,prune_start=prune_start,prune_end=prune_end
                 )
'''
'''
input=[[caadir,0,'g','caa','mag'],[refdirahk114caa,1,'r','caa ext mode','mag']]
output = analyse(spacecraft=3,input=input,start_date=datetime(2008,5,8),
                 end_date=datetime(2008,5,15),std_n=10,
                 PLOT=True, scatter=False,std_threshold=1.,
                 prune_value = 0
                 )
#print output
'''

'''
#print output[:,2], min(output[:,2])
#print output.shape
start = time.clock()
#was used for benchmarking
plt.close('all')
input=[[refdir,1,'r','ext mode default','mag'],[refdir,0,'b','default','mag']]
output,vfiles_store = analyse(spacecraft=3,input=input,start_date=datetime(2014,2,1),
                 end_date=datetime(2014,2,10),std_n=10,
                 PLOT=False, scatter=False,std_threshold=2
                 )
print "Duration1:", time.clock()-start

start = time.clock()
output2,vfiles_store = analyse(spacecraft=3,input=input,start_date=datetime(2014,2,1),
                 end_date=datetime(2014,2,10),std_n=10,
                 PLOT=False, scatter=False,std_threshold=1.5,
                 vectorfile_storage=vfiles_store
                 )

print "Duration2:", time.clock()-start

start = time.clock()
output3,vfiles_store = analyse(spacecraft=3,input=input,start_date=datetime(2014,2,1),
                 end_date=datetime(2014,2,10),std_n=100,
                 PLOT=False, scatter=False,std_threshold=0.01,
                 vectorfile_storage=vfiles_store
                 )

print "Duration3:", time.clock()-start
'''
'''
#was used for benchmarking
plt.close('all')
input=[[refdir,1,'r','ext mode default','mag'],[refdir,0,'b','default','mag']]
output,vfiles_store = analyse(spacecraft=3,input=input,start_date=datetime(2014,2,1),
                 end_date=datetime(2014,2,10),std_n=10,
                 PLOT=False, scatter=False,std_threshold=2
                 )
'''