import numpy as np
from bokeh.plotting import figure, output_file, show
from numpy import linalg as LA
from datetime import date,time,datetime,timedelta
import os
from getfile import getfile
import gzip
import numpy.fft as fft
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
    def prune(self,n=0,start_date=datetime(1,1,1),end_date=datetime(1,1,1),value=0):
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
            self.vectors=[v for v in self.vectors if v.magnitude>value]
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
    def plotlist(self,color='blue',legend='magnitude'):#outdated
        dates = self.returndatetimes()
        magnitudes = self.returnmagnitudes()
        # output to static HTML file (with CDN resources)
        output_file("plot"+legend+".html", title="Plotting Default vs Proper Calibration", mode="cdn")
        TOOLS="resize,crosshair,pan,wheel_zoom,box_zoom,reset"
        # create a new plot with the tools above, and explicit ranges
        p = figure(tools=TOOLS, width=1900, height=1000, y_axis_type='log', x_axis_type="datetime")
        p.line(dates, magnitudes, color=color, legend=legend)
        # show the results
        show(p)   
    def plotlists(self,array,scatter=True,log=False):
        global scatter_size
        labels = [','.join([entry[2],entry[3]]) for entry in array]
        labels = '-'.join(set(labels))
        #array = [vlist,color,legend,plotwhich]
        # output to static HTML file (with CDN resources)
        output_file(labels+".html", title="Plotting Cluster II Data", mode="cdn")
        TOOLS="resize,crosshair,pan,wheel_zoom,box_zoom,reset"
        # create a new plot with the tools above, and explicit ranges
        if log:
            p = figure(tools=TOOLS, width=1900, height=1000, y_axis_type='log', x_axis_type="datetime")
        else:
            p = figure(tools=TOOLS, width=1900, height=1000, x_axis_type="datetime")
        for entry in array:
            #print "entry ",entry
            vlist = entry[0]
            color = entry[1]
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
            if scatter:
                p.circle(dates,data,color=color,legend=legend+' ('+plotwhich+')',
                         size=scatter_size)
            else:
                p.line(dates,data,color=color,legend=legend)
        p.xaxis.axis_label = 'Time'
        p.yaxis.axis_label = 'nT'
        show(p)
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
    def add_vectorlist(self,vlist,color='red',legend='data',plotwhich='mag'):
        if not isinstance(vlist, vectorlist):
            raise Exception('Object supplied must be a vector list')
        else:         
            self.array.append([vlist,color,legend,plotwhich])
    def plotfiles(self,scatter=False,log=True):
        s = vectorlist()
        s.plotlists(self.array,scatter,log)
    def printfiles(self):
        for array in self.array:
            #print array,array[0].filename
            print array[0].filename
    def prune(self,n=0,start_date=datetime(1,1,1),end_date=datetime(1,1,1),value=0):
        for entry in self.array:
            vlist = entry[0]
            vlist.prune(n=n,start_date=start_date,end_date=end_date,value=value)
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

def process(vfiles,sc,start_date,end_date,input):
    global prune_start,prune_end,prune_n,prune_value
    dirs = [[entry[0],entry[1]] for entry in input]
    colours = [entry[2] for entry in input]
    legends = [entry[3] for entry in input]
    plotwhichs=[entry[4] for entyr in input] 
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
        vfiles.prune(value=prune_value)

def plot(vfiles,sc,start_date,end_date,input):
    #dirs = [[entry[0],entry[1]] for entry in input]
    #colours = [entry[2] for entry in input]
    #legends = [entry[3] for entry in input]
    plotwhichs=[entry[4] for entry in input] 
    '''
    global prune_start,prune_end,prune_n
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
            if 'Y:' in directory:
                file = getfile(sc,Year,month,day,directory,ext=True)
            else:
                file = getfile(sc,Year,month,day,directory)

            if file:
                print "filefound:",file
                vlist = vectorlist()
                vlist.read_file(file)
                vfiles.add_vectorlist(vlist,colour,legend,plotwhich)
                #vlist.print_values(0)
    '''       
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
    vfiles.plotfiles(scatter=True,log=log)
 
def fftexecute():
    global vfiles
    mags = vfiles.returnall_magnitudes()
    dates =vfiles.returnall_dates()
    
    dt = np.mean(np.diff(dates)/np.timedelta64(1,'s'))
    print "Spin period estimate:",dt
    print "Number of samples:",len(mags),len(dates)
    fftout = fft.fft(mags)
    freq = fft.fftfreq(len(mags))   #frequency bin centers in cycles per unit of the sample spacing
                                    #in this case the spin period (arund 4s) - dt
    #plt.close('all')
    plt.figure()
    #dt = 4.255
    freq = freq/dt #now in cycles per second!!
    plt.scatter(freq[1:],fftout.real[1:],c='r',s=50) #ignoring 0 component
    #plt.scatter(freq,fftout.imag,c='b',s=50)
    plt.title('cumulative')
    plt.show()

def fftexecutedaily():
    global vfiles,ffts
    #plt.close('all')
    plt.figure()
    amplitudes=[]
    freqs = []
    for entry in vfiles.array:
        vlist = entry[0]
        mags = vlist.returnmagnitudes()
        dates= vlist.returndatetimes()
        if len(mags)>800:
            ffts+=1
            dt = np.mean(np.diff(dates)/np.timedelta64(1,'s'))
            print "Spin period estimate:",dt
            print "Number of samples:",len(mags),len(dates)
            fftout = fft.fft(mags)
            freq = fft.fftfreq(len(mags),d=dt)   #frequency bin centers in cycles per unit of the sample spacing
            #in this case the spin period (arund 4s) - dt

            #dt = 4.255
            #freq = freq/dt #now in cycles per second!!
            freqs.extend(freq[1:])
            #fftout_ = fftout.real[1:]
            #fftout_i = fftout.imag[1:]
            #print fftout_[:10]
            #print fftout_i[:10]
            fftout = np.absolute(fftout)
            amplitudes.extend(fftout[1:])#ignoring 0 component
    
    plt.scatter(freqs,amplitudes,c='r',s=50) 
    plt.title('daily')
    #plt.scatter(freq,fftout.imag,c='b',s=50)
    print "distinct periods:",ffts
    plt.show()

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
        
    #plt.figure()
    #plt.scatter(np.linspace(0,len(diffarray),len(diffarray)),diffarray)
    #plt.hist(diffarray,bins=300)   
  
def isolate_pattern():
    global vfiles
    for entry in vfiles.array:
        vlist = entry[0]
        mags = np.asarray(vlist.returnmagnitudes()).reshape(-1,1)
        primary = []
        secondary = []
        diffs = mags[:-1]-mags[1:]
        for i in range(len(diffs)):
            if diffs[i]>0.15:
                secondary.append([i,mags[i+1]])
            else:
                primary.append([i,mags[i+1]])
    plt.figure()
    x=[]
    y=[]
    for i,j in primary:
        x.append(i)
        y.append(j)
    plt.scatter(x,y,c='b')
    x=[]
    y=[]
    for i,j in secondary:
        x.append(i)
        y.append(j)
    plt.scatter(x,y,c='r',s=100)
         
#filename = "Y:/reference/2015/12/C1_151231_B.EXT.GSE"
plt.close('all')
vfiles = vectorfiles()
refdirahk114 = "Y:/reference/"
refdir = "Z:/data/reference/" 
caadir = 'Z:/caa/ic_archive/'
#refdirahk114 = refdir
sc = 1

'''
#large pickle file!!
start_date = datetime(2010,1,1)
end_date = datetime(2014,8,10)
'''


#test date
start_date = datetime(2016,1,4)
end_date  = datetime(2016,1,5)


'''
input = [directory,extmode 0 or 1 (off or on), colour, legend, whichdata ('mag','x','y','z')]
'''
input = [
         [refdir,1,'red','ext mode default','mag']
]

################
'''
pruning of output - fine date selection & point count reduction
'''
#prune_start = datetime(2015,1,1)
#prune_end   = datetime(2015,5,1)
#prune_n     = 20

prune_value = 80
#################
scatter_size = 6
#################

rm_outliers = 0
#plot(vfiles,sc,start_date,end_date,input)

FFT = 0

TEST = 0
ffts = 0
if prune_start != datetime(1,1,1):
    dt_label_start = prune_start.isoformat()
else:
    dt_label_start = start_date.isoformat()
if prune_start != datetime(1,1,1):
    dt_label_end = prune_end.isoformat()
else:
    dt_label_end = end_date.isoformat()
    
descriptor_string = '_pruningvalue{0:03d}_pruningnumber{1:03d}'.format(prune_value,prune_n)
pickle_file = dt_label_start+'__'+dt_label_end+descriptor_string+'.pickle'
pickle_file = pickle_file.replace(':','')

if FFT:
    vfiles = pickle.load(open(pickle_file,'rb'))
    #fftexecute()
    fftexecutedaily()
elif TEST:
    vfiles = pickle.load(open(pickle_file,'rb'))  
    #plot(vfiles,sc,start_date,end_date,input)
else:
    process(vfiles,sc,start_date,end_date,input)
    #plot(vfiles,sc,start_date,end_date,input)
    #pickle.dump(vfiles,open(pickle_file,'wb'))
    
if rm_outliers:
    #plot(vfiles,sc,start_date,end_date,input)
    remove_outliers()
    #plot(vfiles,sc,start_date,end_date,input)
    #pickle.dump(vfiles,open(pickle_file,'wb'))
#else:
    #plot(vfiles,sc,start_date,end_date,input)
    #pickle.dump(vfiles,open(pickle_file,'wb'))

plot_timeseries()

isolate_pattern()

'''
vfiles = pickle.load(open(pickle_file,'rb')) 
with open(pickle_file[0:-6]+'csv','wb') as csvfile:
    print "Starting to write"
    writer = csv.writer(csvfile,delimiter=',')
    for entry in vfiles.array:
        vlist = entry[0]
        for ventry in vlist.vectors:
            mag = ventry.magnitude
            dt  = ventry.datetime.astype(datetime).isoformat()
            writer.writerow([dt,mag])
print "Finished writing"        
'''

'''
Looking for a link between 'beating' of a combination of the spin period and the rest period
spin period varies, usually around 4.2 seconds
reset period is relatively constant at 5.152 seconds
a beating pattern would repeat with a period given by
spin period * reset period
so around 22 seconds, leading to a frequency of around 0.05 Hz.
08/07
SC 1
For 2016,1,10, between 20hours and 22hours,
relatively wide peak at 0.052Hz, close to expected 0.0456 Hz.


##########
Frequency output of fft given in cycles per unit of sample spacing, ie.
cycles per spin period - so in these units, the beating frequency
should show up at a frequency given by the reset period,
ie. (1/5.152s)=0.1940994Hz
-even IF this were true, it would not be of much use when analysing data
over a large time period range, since the spin period changes over time!
##########
08/07
Set threshold at 80 nT, don't analyse anything under that using a FFT,
since there is too much noise and would shroud the desired observations.
'''