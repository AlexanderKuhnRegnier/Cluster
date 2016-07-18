import numpy as np
from numpy import linalg as LA
from datetime import date,time,datetime,timedelta
import os
from getfile import getfile
import gzip
import matplotlib.pyplot as plt
import cPickle as pickle
import csv

prune_start=datetime(1,1,1)
prune_end=datetime(1,1,1)
prune_n=1
prune_value = 0
end_date = ''

class vector:
    def __init__(self):
        self.v = 0
        self.datetime = 0
        self.magnitude = 0
    def assigndatetime(self,dt):
        self.datetime=dt        
    def assignvalue(self,v):
        self.v = v
    def assignmagnitude(self,mag):
        self.magnitude = mag
    def calcmagnitude(self):
        self.magnitude = LA.norm(self.v)
    
class vectorlist:
    def __init__(self,ext=False):
        self.vectors = []
        self.ext=ext
        self.filename = ''
    def mergelist(self,vlist):
        if isinstance(vlist,vectorlist):
            for v in vlist.vectors:
                self.add_vector_entry(v)
                print "Done merging list into current list"
        else:
            raise Exception("Not a vector list")
    def prune(self,n=0,start_date=datetime(1,1,1),end_date=datetime(1,1,1),value=0,greater_than=True):
        print "Before:",len(self.vectors)
        td = end_date-start_date
        if td.days > 0 and td.seconds >= 0:
            self.vectors=[v for v in self.vectors if v.datetime > start_date
                            if v.datetime < end_date]
        elif td.days >= 0 and td.seconds > 0:
            self.vectors=[v for v in self.vectors if v.datetime > start_date
                            if v.datetime < end_date]
        #decrease density of vectors
        if n > 0:
            self.vectors=[v for (i,v) in enumerate(self.vectors) if not i%n] 
        print "After:",len(self.vectors)
        if value > 0:
            if greater_than:
                self.vectors=[v for v in self.vectors if v.magnitude>value]
            else:
                self.vectors=[v for v in self.vectors if v.magnitude<value]
            print "After value pruning:",len(self.vectors)
    def add_vector_entry(self,v):
        if isinstance(v,vector):
            self.vectors.append(v)
        else:
            raise Exception("This is not a vector")
    def read_file(self,filename,limit=-1):
        if '.cef.gz' in filename and '/caa/ic_archive/' in filename: #this is caa file, needs to be read differently!
            self.filename=filename
            #gzip.open(filename) #defaults to 'rb' and 9
            with gzip.open(self.filename, 'rb') as f:
                for line in f:
                    if 'DATA_UNTIL = EOF' in line:
                        co=0
                        for line in f:
                            co+=1
                            if co==limit:
                                break
                            line = line.split(',')
                            v = vector()                            
                            v.assigndatetime(np.datetime64(line[0]))
                            v.assignvalue(np.array(line[2:5],dtype=np.float64))
                            v.assignmagnitude(float(line[5]))
                            self.add_vector_entry(v)
        else:  
            self.filename = filename
            counter = 0
            with open(filename) as f:
                for line in f:
                    try:
                        v = vector()
                        v.assigndatetime(np.datetime64(line[0:24]))
                        x_mag = float(line[24:33])
                        y_mag = float(line[33:42])
                        z_mag = float(line[42:51])
                        v.assignvalue(np.array([x_mag,y_mag,z_mag]))
                        v.calcmagnitude()
                        self.add_vector_entry(v)                 
                    except ValueError:
                        print "Something wrong with line"
                    counter+=1
                    if counter==limit:
                        break
    def returndatetimes(self):
        return [vector.datetime for vector in self.vectors]
    def returnmagnitudes(self):
        return [vector.magnitude for vector in self.vectors]
    def returnx(self):
        return [vector.v[0] for vector in self.vectors]
    def returny(self):
        return [vector.v[1] for vector in self.vectors]
    def returnz(self):
        return [vector.v[2] for vector in self.vectors]
    def plotlists(self,array,scatter=True,log=False):
        global scatter_size
        #labels = [','.join([entry[2],entry[3]]) for entry in array]
        #labels = '-'.join(set(labels))
        #array = [vlist,color,legend,plotwhich]
        f,ax = plt.subplots(1,1)
        min_date = np.datetime64(datetime(9999,1,1))
        max_date = np.datetime64(datetime(1,1,1))
        legend_colour_list = []
        for count,entry in zip(range(len(array)),array):
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
            for i in range(5):
                print dates[i],data[i],self.filename
            '''
            label = legend+' ('+plotwhich+')'
            if scatter:
                if [label,colour] in legend_colour_list:
                    ax.scatter(dates,data,c=colour,
                         s=scatter_size)
                else:
                    ax.scatter(dates,data,c=colour,label=label,
                         s=scatter_size)
                    legend_colour_list.append([label,colour])
            else:
                ax.plot(dates,data,c=colour,label=legend)
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
    def plotstds(self,array,n=10,scatter=True,log=False):
        global scatter_size,sc
        #labels = [','.join([entry[2],entry[3]]) for entry in array]
        #labels = '-'.join(set(labels))
        #array = [vlist,color,legend,plotwhich]
        f,ax = plt.subplots(2,1,sharex=True)
        min_date = np.datetime64(datetime(9999,1,1))
        max_date = np.datetime64(datetime(1,1,1))
        legend_colour_list = []
        legend_colour_list_std = []
        for count,entry in zip(range(len(array)),array):
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
            for i in range(5):
                print dates[i],data[i],self.filename
            '''
            label = legend+' ('+plotwhich+')'
            if scatter:
                if [label,colour] in legend_colour_list:
                    ax[0].scatter(dates,data,c=colour,
                         s=scatter_size)
                else:
                    ax[0].scatter(dates,data,c=colour,label=label,
                         s=scatter_size)
                    legend_colour_list.append([label,colour])
            else:
                ax[0].plot(dates,data,c=colour,label=legend)

            ######################
            '''
            standard deviation calculation below
            '''
            ######################
            std_dates=[]
            stds = []
            length = int((len(data)-len(data)%n))
            for i in range(0,length,n):
                std_dates.append(dates[i])
                stds.append(np.std(data[i:i+n]))
            label = legend+' ('+plotwhich+')'+'std'
            if scatter:
                if [label,colour] in legend_colour_list_std:
                    ax[1].scatter(std_dates,stds,c=colour,
                         s=scatter_size)
                else:
                    ax[1].scatter(std_dates,stds,c=colour,label=label,
                         s=scatter_size)
                    legend_colour_list_std.append([label,colour])
            else:
                ax[1].plot(std_dates,stds,c=colour,label=legend)            
            if min(dates)<min_date:
                min_date = min(dates)
            if max(dates)>max_date:
                max_date = max(dates)
        
        ax[0].set_xlim((min_date.astype(object)-timedelta(hours=2),max_date.astype(object)+timedelta(hours=2)))
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
        figManager = plt.get_current_fig_manager()
        figManager.window.showMaximized()
        plt.gcf().autofmt_xdate()
        plt.show()
    def print_values(self,limit):
        counter = 0
        print "filename:",self.filename
        for vector in self.vectors:
            if counter == limit:
                break            
            counter+=1
            print vector.datetime, vector.v, vector.magnitude
            
class vectorfiles:
    def __init__(self):
        self.array = []
        self.std_dates = []
        self.stds = []
    def add_vectorlist(self,vlist,color='red',legend='data',plotwhich='mag'):
        if not isinstance(vlist, vectorlist):
            raise Exception('Object supplied must be a vector list')
        else:         
            self.array.append([vlist,color,legend,plotwhich])
    def plotfiles(self,scatter=False,log=True,std=False,n=10):
        s = vectorlist()
        if std:
            s.plotstds(self.array,scatter=scatter,log=log,n=n)
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
        for count,entry in zip(range(len(self.array)),self.array):
            #print "entry ",entry
            vlist = entry[0]
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
            for i in range(0,length,n):
                self.std_dates.append(dates[i])
                self.stds.append(np.std(data[i:i+n]))

def process(vfiles,sc,start_date,end_date,input):
    global prune_start,prune_end,prune_n,prune_value,prune_greater_than
    dirs = [[entry[0],entry[1]] for entry in input]
    colours = [entry[2] for entry in input]
    legends = [entry[3] for entry in input]
    plotwhichs=[entry[4] for entry in input] 
    if start_date==end_date or end_date=='':
        dates = start_date
    else:
        dates = [start_date+timedelta(days=1)*i for i in range(abs(end_date-start_date).days)]
    for datev in dates:
        print ""
        print datev.isoformat()
        Year = str(datev.year)
        #year = Year[2:4]
        month = '{0:02d}'.format(datev.month)
        day = '{0:02d}'.format(datev.day)

        for [dir,ext],colour,legend,plotwhich in zip(dirs,colours,legends,plotwhichs):
            directory = dir+Year+'/'+month+'/'
            print "Getting file:",sc,Year,month,day,directory,ext
            file = getfile(sc,Year,month,day,directory,ext=ext)

            if file:
                print "filefound:",file
                vlist = vectorlist()
                vlist.read_file(file)
                vfiles.add_vectorlist(vlist,colour,legend,plotwhich)
                #vlist.print_values(0)
    print "Prune Start"
    if prune_start != datetime(1,1,1) and prune_end != datetime(1,1,1):
        print "Pruning Dates"
        vfiles.prune(start_date=prune_start,end_date=prune_end)
    if prune_n > 1:
        print "Pruning Points"
        vfiles.prune(n=prune_n)
    if prune_value > 0:
        print "Pruning Values"
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
    '''
    if prune_start != datetime(1,1,1) and prune_end != datetime(1,1,1):
        print "Pruning Dates"
        vfiles.prune(start_date=prune_start,end_date=prune_end)
    if prune_n > 1:
        print "Pruning Points"
        vfiles.prune(n=prune_n)
    '''
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
        
        for i in range(5,len(mags)-10,1):
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
refdirahk114 = "Y:/reference/"
refdir = "Z:/data/reference/" 
caadir = 'Z:/caa/ic_archive/'
#refdirahk114 = refdir
sc = 3

'''
#large pickle file!!
start_date = datetime(2010,1,1)
end_date = datetime(2014,8,10)
'''
plt.close('all')

start_date = datetime(2016,1,1)
end_date  = datetime(2016,1,10)
'''
input = [directory,extmode 0 or 1 (off or on), colour, legend, whichdata ('mag','x','y','z')]
'''
input = [
         #[caadir,0,'r','caa','mag'],
         #[refdir,0,'g','def','y'],
         [refdir,1,'b','def','mag']
]
################
'''
pruning of output - fine date selection & point count reduction
'''
#prune_start = datetime(2015,1,1)
#prune_end   = datetime(2015,5,1)
#prune_n     = 20
prune_greater_than = False
prune_value = 40
#################
scatter_size = 50
#################

rm_outliers = 0

#plot(vfiles,sc,start_date,end_date,input)

std_n = 50
PLOT = 1

reprocess = 1

pickling = 0

if prune_start != datetime(1,1,1):
    dt_label_start = prune_start.isoformat()
else:
    dt_label_start = start_date.isoformat()
if prune_start != datetime(1,1,1):
    dt_label_end = prune_end.isoformat()
else:
    dt_label_end = end_date.isoformat()

if pickling: 
    descriptor_string = '_pruningvalue{0:03d}_pruningnumber{1:03d}'.format(prune_value,prune_n)
    pickle_file = dt_label_start+'__'+dt_label_end+descriptor_string+'.pickle'
    pickle_file = pickle_file.replace(':','')
    if rm_outliers != 0 and rm_outliers != 1:
        raise Exception("only use 0 or 1 please")
    pickle_file += format(rm_outliers,'d')

if reprocess:
    process(vfiles,sc,start_date,end_date,input)
    if pickling:
        pickle.dump(vfiles,open(pickle_file,'wb'))

if PLOT:
    if pickling:
        print "Reading from pickle file"
        vfiles = pickle.load(open(pickle_file,'rb'))
    plot(vfiles,sc,start_date,end_date,input,n=std_n)
    #plot(vfiles,sc,start_date,end_date,input)

if rm_outliers:
    if pickle_file in os.listdir(os.getcwd()):
        print "Already removed outliers!"
    else:
        plot(vfiles,sc,start_date,end_date,input,n=std_n)
        remove_outliers()
        if pickling:
            pickle.dump(vfiles,open(pickle_file,'wb'))
    plot(vfiles,sc,start_date,end_date,input,n=std_n)

vfiles.calculate_stds(n=std_n)
print len(vfiles.stds),len(vfiles.std_dates)
plt.figure()
plt.scatter(vfiles.std_dates,vfiles.stds)
plt.show()