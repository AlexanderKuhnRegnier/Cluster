import numpy as np
#import copy
#from numpy import linalg as LA
from datetime import datetime,timedelta
#import os
from getfile import getfile
import gzip
import matplotlib.pyplot as plt
plt.style.use('seaborn-darkgrid')
#import cPickle as pickle
#import pickle
import pandas as pd
#import itertools
#import csv
#import time
pickledir = 'Y:/overlap_stats/'
refdirahk114 = "Y:/reference/"
refdir = "Z:/data/reference/" 
caadir = 'Z:/caa/ic_archive/'
dirs = [refdirahk114,refdir,caadir]
dir_names=['refdirahk114','refdir','caadir']
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
        self.vfiles=None
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
        if len(self.vectors):
            return False
        else:
            return True
    def prune(self,n=0,start_date=datetime(1,1,1),end_date=datetime(1,1,1),value=0,greater_than=True):
        '''
        Removes vectors from vectorlist which do not fit pruning criteria
        '''
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
                self.vectors=self.vectors[start_date:end_date]
            if n > 0:
                #self.vectors=[v for (i,v) in enumerate(self.vectors) if not i%n] 
                self.vectors=self.vectors[::n]
            print "After:",len(self.vectors)
            if value > 0:
                if greater_than:
                    #self.vectors=[v for v in self.vectors if v.magnitude>value]
                    self.vectors=self.vectors[self.vectors['mag']>value]
                else:
                    #self.vectors=[v for v in self.vectors if v.magnitude<value]
                    self.vectors=self.vectors[self.vectors['mag']<value]
                print "After value pruning:",len(self.vectors)

    def read_file(self,filename):
        data_dict = {'datetime':[],'x':[],'y':[],'z':[]}
        if '.cef.gz' in filename and '/caa/ic_archive/' in filename: #this is caa file, needs to be read differently!
            self.filename=filename
            data_dict['mag']=[]
            #gzip.open(filename) #defaults to 'rb' and 9
            with gzip.open(self.filename, 'rb') as f:
                for line in f:
                    if 'DATA_UNTIL = EOF' in line:
                        for line in f:
                            line = line.split(',')   

                            data_dict['datetime'].append(np.datetime64(line[0]))
                            x_mag = float(line[2])
                            y_mag = float(line[3])
                            z_mag = float(line[4])
                            mag = float(line[5])
                            data_dict['x'].append(x_mag)
                            data_dict['y'].append(y_mag)
                            data_dict['z'].append(z_mag)
                            data_dict['mag'].append(mag)
            self.vectors=pd.DataFrame(data_dict,columns=['datetime','x','y','z','mag'])
        else:  
            self.filename = filename
            
            with open(filename) as f:
                for line in f:
                    try:
                        line=line.split(' ')
                        line = [char for char in line if char != '']
                        x_mag = float(line[1])
                        y_mag = float(line[2])
                        z_mag = float(line[3])
                        data_dict['x'].append(x_mag)
                        data_dict['y'].append(y_mag)
                        data_dict['z'].append(z_mag)
                        data_dict['datetime'].append(np.datetime64(line[0]))
                    except ValueError:
                        if "60.000" in line[0]:
                            print "Replacing 60.000 by 59.999"
                            line[0]=line[0].replace('60.000','59.999')
                            line[0]=np.datetime64(line[0])
                            data_dict['datetime'].append(np.datetime64(line[0]))                  
                        else:
                            print "Unknown Error"
            self.vectors=pd.DataFrame(data_dict,columns=['datetime','x','y','z'])
            self.vectors.set_index('datetime',drop=True,inplace=True)
            
            '''
            self.vectors=pd.read_csv(filename,
                                     header=None,
                                     delim_whitespace=True,
                                     index_col=0,
                                     usecols=[0,1,2,3],
                                     engine='c',
                                     dtype={1:np.float64,2:np.float64,3:np.float64},
                                     skip_blank_lines=True,
                                     na_filter=False,
                                     verbose=False,
                                     infer_datetime_format=True,
                                     compression=None,
                                     parse_dates=True,
                                     names=['datetime','x','y','z'])
            '''
            if not self.vectors.empty:
                mag = np.linalg.norm(self.vectors.ix[:,:],axis=1)
                self.vectors['mag'] = mag
                if type(self.vectors.index[0])==str:
                    print "Time format error in file"
                    self.vectors.reset_index(inplace=True)
                    datetimes=self.vectors['datetime']
                    mask = datetimes.str.contains(':60.000')
                    indices_to_replace = self.vectors.ix[mask,'datetime'].index
                    #print indices_to_replace
                    for i in indices_to_replace:
                        #print "i", i, self.vectors.loc[i,'datetime']
                        date_string = self.vectors.loc[i,'datetime']
                        date_string = date_string.replace(':60.000',':59.999')
                        self.vectors.loc[i,'datetime'] = date_string
                    #print "New entry"
                    #print self.vectors.loc[indices_to_replace,'datetime']
                    #print self.vectors.loc[18350:18355]
                    self.vectors.set_index('datetime',drop=True,inplace=True)
                    #print self.vectors
                    self.vectors.index = pd.to_datetime(self.vectors.index)
                    #print self.vectors
                    #raise Exception

            else:
                self.vectors['mag']=[]
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
        min_date = np.datetime64(datetime(9999,1,1))
        max_date = np.datetime64(datetime(1,1,1))
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
                    ax.scatter(dates,data,c=colour,
                         s=scatter_size)
                else:
                    ax.scatter(dates,data,c=colour,label=label,
                         s=scatter_size)
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
                        ax.plot(ds,da,c=colour)
                    else:
                        ax.plot(ds,da,c=colour,label=legend)
                        legend_colour_list_line.append([label,colour]) 
            print "plotted the following",len(dates),len(data)
            print "From:",min(dates).astype(object)
            print "  To:",max(dates).astype(object)
            if min(dates)<min_date:
                min_date = min(dates)
            if max(dates)>max_date:
                max_date = max(dates)

        ax.set_xlim((min_date.astype(object)-timedelta(hours=2),max_date.astype(object)+timedelta(hours=2)))
        legend = ax.legend()
        
        ax.set_xlabel('Time')
        ax.set_ylabel('nT')
        if log:
            ax.set_yscale('log')
        figManager = plt.get_current_fig_manager()
        figManager.window.showMaximized()
        plt.gcf().autofmt_xdate()
        plt.show()
    def plotstds(self,array,n=10,scatter=True,log=False,
                 threshold_std_dates=np.array([]),
                 threshold_std_data=np.array([])):
        '''
        sorting the threshold_std arrays by ascending time in order
        to remove jumps in the plots
        '''
        threshold_std_dates=np.asarray([pd.Timestamp(i).to_datetime() for i in \
                                            threshold_std_dates]).reshape(-1,1)
        threshold_std_data=np.asarray(threshold_std_data).reshape(-1,1)  
        if threshold_std_dates.size != threshold_std_data.size:
            raise Exception("The std threshold data sizes do not match!")
        threshold_data = np.concatenate((threshold_std_dates,threshold_std_data),
                                        axis=1)
        threshold_data = np.asarray(sorted(threshold_data,key=lambda x:x[0]))
        threshold_std_dates = threshold_data[:,0]
        threshold_std_data  = threshold_data[:,1]
        global scatter_size,sc
        #labels = [','.join([entry[2],entry[3]]) for entry in array]
        #labels = '-'.join(set(labels))
        #array = [vlist,color,legend,plotwhich]
        f,ax = plt.subplots(2,1,sharex=True)
        legend_colour_list_scatter = []
        legend_colour_list_line = []
        legend_colour_list_std_scatter = []
        legend_colour_list_std_line = []
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
                ######################
                '''
                standard deviation calculation below
                '''
                ######################
                std_dates=[]
                stds = []
                length = int((len(data)-len(data)%n))
                for i in xrange(0,length,n):
                    std_dates.append(dates[i])
                    stds.append(np.std(data[i:i+n]))
                label = legend+' ('+plotwhich+')'+' std'
                if scatter:
                    if [label,colour] in legend_colour_list_std_scatter:
                        ax[1].plot_date(std_dates,stds,c=colour)
                        ax[1].plot_date(threshold_std_dates,
                                      threshold_std_data,
                                      c='g')
                    else:
                        ax[1].plot_date(std_dates,stds,c=colour,label=label)
                        ax[1].plot_date(threshold_std_dates,
                                      threshold_std_data,c='g')
                        legend_colour_list_std_scatter.append([label,colour])
                else:
                    std_dates_list=[]
                    stds_list=[]
                    '''
                    preprocess data so that for time gaps, a line isn't being drawn
                    -so split the data up into chunks when this happens!
                    '''
                    total_entries=0
                    for i in xrange(len(std_dates)-1):
                        dates2 = std_dates[i:i+2]
                        diff = (np.datetime64(dates2[-1])-np.datetime64(dates2[0])) \
                                            /np.timedelta64(1,'s')
                        if diff<0:
                            raise Exception("Negative diff")
                        if diff>(5*int(n)):#split data at this point!
                            std_dates_list.append(std_dates[total_entries:i+1])
                            stds_list.append(stds[total_entries:i+1])
                            total_entries+=len(std_dates_list[-1])
                    if total_entries != len(std_dates):
                        std_dates_list.append(std_dates[total_entries:])
                        stds_list.append(stds[total_entries:])
                        if len(std_dates_list[-1])!=len(stds_list[-1]):
                            print "Error, last plotted lists not of equal length!!"
                        total_entries+=len(std_dates_list[-1])
                    for ds_std,da_std in zip(std_dates_list,stds_list):
                        if [label,colour] in legend_colour_list_std_line:
                            ax[1].plot_date(ds_std,da_std,c='r',fmt='-.')
                        else:
                            ax[1].plot_date(ds_std,da_std,c='r',label=label,fmt='-.')
                            legend_colour_list_std_line.append([label,colour]) 
                    std_dates_list=[]
                    stds_list=[]
                    '''
                    this time for the threshold data!!
                    preprocess data so that for time gaps, a line isn't being drawn
                    -so split the data up into chunks when this happens!
                    '''
                    total_entries=0
                    for i in xrange(len(threshold_std_dates)-1):
                        dates2 = threshold_std_dates[i:i+2]
                        diff = (np.datetime64(dates2[-1])-np.datetime64(dates2[0]))\
                                                /np.timedelta64(1,'s')
                        if diff>(10*int(n)):#split data at this point!
                            std_dates_list.append(threshold_std_dates[total_entries:i+1])
                            stds_list.append(threshold_std_data[total_entries:i+1])
                            total_entries+=len(std_dates_list[-1])
                    if total_entries != len(threshold_std_dates):
                        std_dates_list.append(threshold_std_dates[total_entries:])
                        stds_list.append(threshold_std_data[total_entries:])
                        if len(std_dates_list[-1])!=len(stds_list[-1]):
                            print "Error, last plotted lists not of equal length!!"
                        total_entries+=len(std_dates_list[-1])
                    for ds_std,da_std in zip(std_dates_list,stds_list):
                        if [label,colour] in legend_colour_list_std_line:
                            ax[1].plot_date(ds_std,da_std,c='g',fmt='-')
                        else:
                            ax[1].plot_date(ds_std,da_std,c='g',label=legend,fmt='-')
                            legend_colour_list_std_line.append([label,colour]) 
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
        self.stds = []
        '''
        4 columns in the threshold_std array
        column 0:start date of interval
        column 1:end date of interval
        column 2:standard deviation over interval
        column 3:raw data for the interval (as (n,2) array)
        '''
        self.std_data_raw =[]
    def add_vectorlist(self,vlist,color='red',legend='data',plotwhich='mag'):
        if not isinstance(vlist, vectorlist):
            raise Exception('Object supplied must be a vector list')
        else:         
            self.array.append([vlist,color,legend,plotwhich])
    def plotfiles(self,scatter=False,log=True,std=False,n=10):
        s = vectorlist()
        if std:
            s.plotstds(self.array,scatter=scatter,log=log,n=n,
                       threshold_std_dates = [self.threshold_std[i][0] for \
                                       i in xrange(len(self.threshold_std))],
                       threshold_std_data = [self.threshold_std[i][2] for  \
                                       i in xrange(len(self.threshold_std))])
        else:
            s.plotlists(self.array,scatter=scatter,log=log)
    def printfiles(self):
        for array in self.array:
            #print array,array[0].filename
            print array[0].filename
    def prune(self,n=0,start_date=datetime(1,1,1),end_date=datetime(1,1,1),value=0,greater_than=True):
        for entry in self.array:
            vlist = entry[0]
            vlist.prune(n=n,start_date=start_date,end_date=end_date,value=value,greater_than=greater_than)
        print "Done Pruning"
    def returnall_magnitudes(self):
        mags=[]
        for entry in self.array:
            vlist = entry[0]
            mags.extend(vlist.returnmagnitudes())
        return mags
    def returnall_dates(self):
        dates=[]
        for entry in self.array:
            vlist = entry[0]
            dates.extend(vlist.returndatetimes())
        return dates
    def calculate_stds(self,n=10,scatter=True,log=False):
        global sc
        print "Spacecraft:",sc
        print "STD samples:",n
        for count,entry in enumerate(self.array):
            #print "entry ",entry
            vlist = entry[0]
            if not vlist.vectors.empty:
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
                ######################
                '''
                standard deviation calculation below
                '''
                ######################
                length = int((len(data)-len(data)%n))
                for i in xrange(0,length,n):
                    self.std_dates.append(dates[i])
                    self.std_end_dates.append(dates[i:i+n+1][-1]) #end date of interval - should this be [i:i+n+1] - yes, since the 
                                                                    #algorithm relies on identical start/end times
                    self.stds.append(np.std(data[i:i+n]))
                    nddata = list(data[i:i+n])
                    nddates = list(dates[i:i+n])
                    raw_data = [nddates,nddata]
                    self.std_data_raw.append(list(raw_data))
    def select_stds(self,threshold):
        self.threshold_std = []
        if threshold==0:    #then don't filter anything out
            for d,end_d,std,raw_std_data in zip(self.std_dates,self.std_end_dates,
                                                self.stds,self.std_data_raw):
                self.threshold_std.append([d,end_d,std,list(raw_std_data)])
        else:        
            for d,end_d,std,raw_std_data in zip(self.std_dates,self.std_end_dates,
                                                self.stds,self.std_data_raw):
                if std<threshold:
                    self.threshold_std.append([d,end_d,std,list(raw_std_data)])        
    def merge_select_stds(self):
        new_threshold_std = []
        if self.threshold_std:
            new_threshold_std.append([self.threshold_std[0][0],
                                      self.threshold_std[0][1],
                                      self.threshold_std[0][2],
                                      [list(self.threshold_std[0][3][0]),
                                       list(self.threshold_std[0][3][1])]])
            for i in xrange(1,len(self.threshold_std)):    
                previous_end_date = new_threshold_std[-1][1]
                this_start_date = self.threshold_std[i][0]
                if previous_end_date == this_start_date:
                    new_threshold_std[-1][1]=self.threshold_std[i][1]
                    new_threshold_std[-1][2]=np.mean((self.threshold_std[i][2],
                                                    new_threshold_std[-1][2]))
                    new_threshold_std[-1][3][0].extend(self.threshold_std[i][3][0])
                    new_threshold_std[-1][3][1].extend(self.threshold_std[i][3][1])
                else:
                    new_threshold_std.append([self.threshold_std[i][0],
                                              self.threshold_std[i][1],
                                              self.threshold_std[i][2],
                                              [list(self.threshold_std[0][3][0]),
                                               list(self.threshold_std[0][3][1])]]) 
        for i in xrange(len(new_threshold_std)):
            new_threshold_std[i][3]=np.asarray(new_threshold_std[i][3]).transpose()
        return new_threshold_std
def process(vfiles,sc,start_date,end_date,input,prune_start=datetime(1,1,1),
            prune_end=datetime(1,1,1),prune_n=0,prune_value=0,
            prune_greater_than=False):
    #global prune_start,prune_end,prune_n,prune_value,prune_greater_than
    dirs = [[entry[0],entry[1]] for entry in input]
    colours = [entry[2] for entry in input]
    legends = [entry[3] for entry in input]
    plotwhichs=[entry[4] for entry in input] 
    if start_date==end_date or end_date=='':
        dates = [start_date]
    else:
        dates = [start_date+timedelta(days=1)*i for i in xrange(abs(end_date-start_date).days+1)]
    for datev in dates:
        print ""
        print datev.isoformat()
        Year = datev.year
        #year = Year[2:4]
        month = datev.month
        day = datev.day

        for [dir,ext],colour,legend,plotwhich in zip(dirs,colours,legends,plotwhichs):
            file = getfile(sc,Year,month,day,dir,ext=ext)
            if file:
                print "filefound:",file
                vlist = vectorlist()
                vlist.read_file(file)
                vfiles.add_vectorlist(vlist,colour,legend,plotwhich)
                #vlist.print_values(0)
    print "Prune Start"
    if prune_start != datetime(1,1,1) and prune_end != datetime(1,1,1):
        print "Pruning Dates:",prune_start,prune_end
        vfiles.prune(start_date=prune_start,end_date=prune_end)
    if prune_n > 1:
        print "Pruning Points",prune_n
        vfiles.prune(n=prune_n)
    if prune_value > 0:
        print "Pruning Values",prune_value
        vfiles.prune(value=prune_value,greater_than=prune_greater_than)

def plot(vfiles,sc,start_date,end_date,input,std=True,scatter=True,n=10):
    #dirs = [[entry[0],entry[1]] for entry in input]
    #colours = [entry[2] for entry in input]
    #legends = [entry[3] for entry in input]
    plotwhichs=[entry[4] for entry in input] 
    #vfiles.printfiles()
    if 'x' in plotwhichs or 'y' in plotwhichs or 'z' in plotwhichs:
        log=False
    else:
        log=True

    vfiles.plotfiles(scatter=scatter,log=log,std=std,n=n)

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
    print "Vfiles before:",len(vfiles.array)
    for entry in vfiles.array:
        vlist = entry[0]
        mags = vlist.returnmagnitudes()
        #dates= vlist.returndatetimes()    
        if len(mags)>1300:
            newvfiles.add_vectorlist(vlist)
    vfiles = newvfiles
    print "Done selecting based on sample length"
    print "Vfiles after:",len(vfiles.array)
    
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
            scatter=False,vectorfile_storage=vfile_store()):
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
    4 'column' list ---
    column 0:start date of interval
    column 1:end date of interval
    column 2:standard deviation over interval
    column 3:raw data for the interval (as (n,2) array)
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
        print "No previous vfiles"
        vfiles=vectorfiles()
        process(vfiles,sc,start_date,end_date,input,prune_start,prune_end,prune_n,prune_value,prune_greater_than)
        if rm_outliers:
            plot(vfiles,sc,start_date,end_date,input,n=std_n,scatter=scatter)
            remove_outliers()
            plot(vfiles,sc,start_date,end_date,input,n=std_n)
            
        vfiles.calculate_stds(n=std_n) 
        print "Storing vfiles",len(vfiles.array)  
        print ""
        vfiles_store.add_vectorfiles(vfiles)
    else:
        vfiles_store=vectorfile_storage
        vfiles=vectorfile_storage.get_vfiles()
        print "Using previous vfiles",len(vfiles.array)
    vfiles.select_stds(threshold=std_threshold)
    if PLOT:
        plot(vfiles,sc,start_date,end_date,input,n=std_n,scatter=scatter)
        #plot(vfiles,sc,start_date,end_date,input)
    new = vfiles.merge_select_stds()
    #return vfiles.threshold_std,new
    return new,vfiles_store

def plot_axis(array,ax):
    legend_colour_list_line = []
    for count,entry in enumerate(array):
        #print "entry ",entry
        vlist = entry[0]
        colour = entry[1]
        legend = entry[2]
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
        label = legend+' ('+plotwhich+')'
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
    legend = ax.legend(loc='best') 
        
def plot_both(sc,start_date,end_date,plotwhich='mag',return_output=False,std_threshold=0,std_n=10):
    '''
    sc can be an int or a list of ints [1,2,3,4]
    '''
    if plotwhich not in ['x','y','z','mag']:
        raise Exception("Please select one of 'x','y','z' or 'mag'")
    input=[[refdir,1,'r','ext mode default',plotwhich],[refdir,0,'b','default',plotwhich]]
    if type(sc)==list:
        for s in sc:
            output = analyse(spacecraft=s,input=input,start_date=start_date,
                     end_date=end_date,std_n=std_n,
                     PLOT=True, scatter=False,std_threshold=std_threshold
                     )       
    elif type(sc)==int:
        output = analyse(spacecraft=3,input=input,start_date=start_date,
                 end_date=end_date,std_n=std_n,
                 PLOT=True, scatter=False,std_threshold=std_threshold
                 )
    else:
        raise Exception("sc(s) has to be int type")
    if return_output:
        return output
               
def plot_xyz(series,save=False,dpi=300,image_type='.pdf',prune=True):
    plt.ioff()
    if not '.' in image_type:
        image_type='.'+image_type
    '''
    Takes a row (so, a series) from the overlap_data DataFrame as its input
    and uses the values contained within to identify which things to plot
    '''
    global vfiles
    plotwhichs=['x','y','z']
    start_date = series.start.normalize().to_datetime()
    end_date = series.end.normalize().to_datetime()
    if not prune:
        prune_start=datetime(1,1,1)
        prune_end=datetime(1,1,1)
    else:
        prune_start = series.start.to_datetime()
        prune_end = series.end.to_datetime()
    f,axarr = plt.subplots(3,1,sharex=True)
    axarr[2].set_xlabel('Time')
    scs=map(int,[series.non_ext_sc+1,series.ext_sc+1])
    legends = ['default','ext mode default']
    colours = ['g','r']
    for ((row,plotwhich),ax) in zip(enumerate(plotwhichs),axarr):
        ax.grid(True,which='major',color='w',linestyle='-')
        ax.grid(True,which='minor',color='w',linestyle='-',alpha=0.5)
        ax.minorticks_on()
        ax.set_ylabel('nT')
        for ((ext_mode,sc),legend,colour) in zip(enumerate(scs),legends,colours):
            input=[[refdir,ext_mode,colour,legend,plotwhich]]
            vfiles=vectorfiles()
            process(vfiles,sc,start_date,end_date,input,prune_start,prune_end)
            plot_axis(vfiles.array,ax)
    
    figManager = plt.get_current_fig_manager()
    figManager.window.showMaximized()
    #plt.gcf().autofmt_xdate() #angles the date labels
    if save:
        filename='xyz_'+prune_start.strftime("%Y%m%dT%H%M%S")+\
                  '__'+prune_end.strftime("%Y%m%dT%H%M%S")+image_type
        f.savefig(pickledir+filename,dpi=dpi)
    plt.show()
    if not prune:
        prune_start=start_date
        prune_end=end_date
    title_string = "From "+prune_start.strftime("%d %B %Y %H:%M:%S")\
                    +" to "+prune_end.strftime("%d %B %Y %H:%M:%S")\
                    +" with Cluster "+str(scs[0])+" in normal mode"\
                    +" and Cluster "+str(scs[1])+" in extended mode"\
                    +"\nSummary Field Data for both Spacecraft Measurements" \
                    +"\nstd: "+format(series['std'],'.3f')\
                    +" mean: "+format(series['mean'],'.3f')\
                    +" min: "+format(series['min'],'.3f')\
                    +" max: "+format(series['max'],'.3f')
    plt.suptitle(title_string,fontsize=15)

def plot_mag_xyz(series,save=False,dpi=300,image_type='.pdf',prune=True):
    plt.ioff()
    if not '.' in image_type:
        image_type='.'+image_type
    '''
    Takes a row (so, a series) from the overlap_data DataFrame as its input
    and uses the values contained within to identify which things to plot
    '''
    global vfiles
    plotwhichs=['x','y','z','mag']
    start_date = series.start.normalize().to_datetime()
    end_date = series.end.normalize().to_datetime()
    if not prune:
        prune_start=datetime(1,1,1)
        prune_end=datetime(1,1,1)
    else:
        prune_start = series.start.to_datetime()
        prune_end = series.end.to_datetime()
    f,axarr = plt.subplots(2,2,sharex=True)
    axarr[0][1].set_xlabel('Time')
    axarr[1][1].set_xlabel('Time')
    axarr[0][0].set_ylabel('nT')
    axarr = np.ravel(axarr)
    scs=map(int,[series.non_ext_sc+1,series.ext_sc+1])
    legends = ['default','ext mode default']
    colours = ['g','r']
    for ((row,plotwhich),ax) in zip(enumerate(plotwhichs),axarr):
        ax.grid(True,which='major',color='w',linestyle='-')
        ax.grid(True,which='minor',color='w',linestyle='-',alpha=0.5)
        ax.minorticks_on()
        for ((ext_mode,sc),legend,colour) in zip(enumerate(scs),legends,colours):
            input=[[refdir,ext_mode,colour,legend,plotwhich]]
            vfiles=vectorfiles()
            process(vfiles,sc,start_date,end_date,input,prune_start,prune_end)
            plot_axis(vfiles.array,ax)
    
    figManager = plt.get_current_fig_manager()
    figManager.window.showMaximized()
    #plt.gcf().autofmt_xdate() #angles the date labels
    if save:
        filename='xyz_'+prune_start.strftime("%Y%m%dT%H%M%S")+\
                  '__'+prune_end.strftime("%Y%m%dT%H%M%S")+image_type
        f.savefig(pickledir+filename,dpi=dpi)
    plt.show()
    if not prune:
        prune_start=start_date
        prune_end=end_date
    title_string = "From "+prune_start.strftime("%d %B %Y %H:%M:%S")\
                    +" to "+prune_end.strftime("%d %B %Y %H:%M:%S")\
                    +" with Cluster "+str(scs[0])+" in normal mode"\
                    +" and Cluster "+str(scs[1])+" in extended mode"\
                    +"\nSummary Field Data for both Spacecraft Measurements" \
                    +"\nstd: "+format(series['std'],'.3f')\
                    +" mean: "+format(series['mean'],'.3f')\
                    +" min: "+format(series['min'],'.3f')\
                    +" max: "+format(series['max'],'.3f')
    plt.suptitle(title_string,fontsize=15)

'''
input=[[refdir,1,'r','ext mode default','mag'],[refdir,0,'b','default','mag']]
output = analyse(spacecraft=3,input=input,start_date=datetime(2015,1,6),
                 end_date=datetime(2015,1,20),std_n=10,
                 PLOT=True, scatter=False,std_threshold=0
                 )
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