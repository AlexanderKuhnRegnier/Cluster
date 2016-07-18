import numpy as np
from bokeh.plotting import figure, output_file, show
from numpy import linalg as LA
from datetime import date,time,datetime,timedelta
import os
from getfile import getfile
import gzip

prune_start=datetime(1,1,1)
prune_end=datetime(1,1,1)
prune_n=1
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
    def prune(self,n=0,start_date=datetime(1,1,1),end_date=datetime(1,1,1)):
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
    def add_vectorlist(self,vlist,color,legend,plotwhich='mag'):
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
    def prune(self,n=0,start_date=datetime(1,1,1),end_date=datetime(1,1,1)):
        for entry in self.array:
            vlist = entry[0]
            vlist.prune(n=n,start_date=start_date,end_date=end_date)
        print "Done Pruning"

def plot(vfiles,sc,start_date,end_date,dirs,colours,legends,plotwhichs):
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
            
    #vfiles.printfiles()
    if 'x' in plotwhichs or 'y' in plotwhichs or 'z' in plotwhichs:
        log=False
    else:
        log=True
        
    if prune_start != datetime(1,1,1) and prune_end != datetime(1,1,1):
        print "Pruning Dates"
        vfiles.prune(start_date=prune_start,end_date=prune_end)
    if prune_n > 1:
        print "Pruning Points"
        vfiles.prune(n=prune_n)
    vfiles.plotfiles(scatter=True,log=log)
            
#filename = "Y:/reference/2015/12/C1_151231_B.EXT.GSE"

vfiles = vectorfiles()
refdirahk114 = "Y:/reference/"
refdir = "Z:/data/reference/" 
caadir = 'Z:/caa/ic_archive/'
#refdirahk114 = refdir
sc = 1
start_date = date(2016,01,8)
end_date = date(2016,01,14)
'''
input = [directory,extmode 0 or 1 (off or on), colour, legend, whichdata ('mag','x','y','z')]
'''
input = [[caadir,0,'green','caa','mag'],
         [refdirahk114,1,'red','ext mode caa','mag']
]

################
'''
pruning of output - fine date selection & point count reduction
'''
prune_start = datetime(2016,1,10,20)
prune_end   = datetime(2016,1,10,22)
prune_n     = 1
#################
scatter_size = 6
#################

dirs = [[entry[0],entry[1]] for entry in input]
colours = [entry[2] for entry in input]
legends = [entry[3] for entry in input]
plotwhichs=[entry[4] for entyr in input] 
'''
dirs=[
[caadir,0],
[refdirahk114,1],
[refdirahk114,1],
[refdirahk114,1],
[refdirahk114,1]
]
colours=[
'green',
'red',
'purple',
'blue',
'olive'
]
legends=[
'caa','ext mode caa','x','y','z'
]
plotwhichs=[
'mag',
'mag',
'x',
'y',
'z'
]

for entry in dirs:
    print "entry", entry,len(entry)
    if len(entry)==1:
        entry.append(0)
    elif entry[1]!=1 and entry[1]!=0:
        raise Exception("Invalid Ext mode selection")

print dirs
'''
plot(vfiles,sc,start_date,end_date,dirs,colours,legends,plotwhichs)