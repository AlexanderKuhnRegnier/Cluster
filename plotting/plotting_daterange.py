import numpy as np
from bokeh.plotting import figure, output_file, show
from numpy import linalg as LA
from datetime import date,time,datetime,timedelta
import os

class vector:
    def __init__(self):
        self.v = 0
        self.datetime = 0
        self.magnitude = 0
    def assigndatetime(self,datetime):
        self.datetime=datetime        
    def assignvalue(self,v):
        self.v = v
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
    def add_vector_entry(self,v):
        if isinstance(v,vector):
            self.vectors.append(v)
        else:
            raise Exception("This is not a vector")
    def read_file(self,filename,limit=-1): 
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
    def plotlists(self,array,scatter=False,log=True):
        # output to static HTML file (with CDN resources)
        output_file("plot.html", title="Plotting Cluster II Data", mode="cdn")
        
        TOOLS="resize,crosshair,pan,wheel_zoom,box_zoom,reset"
        
        # create a new plot with the tools above, and explicit ranges
        if log:
            p = figure(tools=TOOLS, width=1900, height=1000, y_axis_type='log', x_axis_type="datetime")
        else:
            p = figure(tools=TOOLS, width=1900, height=1000, x_axis_type="datetime")
        for entry in array:
            vlist = entry[0]
            color = entry[1]
            legend = entry[2]
            #checks could be done here
            #for now, just assume everything will be ok
            dates = vlist.returndatetimes()
            magnitudes = vlist.returnmagnitudes()
            if scatter:
                p.circle(dates,magnitudes,color=color,legend=legend,size=1)
            else:
                p.line(dates,magnitudes,color=color,legend=legend)
        p.xaxis.axis_label = 'Time'
        p.yaxis.axis_label = 'nT'
        show(p)
    def print_values(self,limit):
        counter = 0
        for vector in self.vectors:
            print vector.datetime, vector.magnitude
            counter+=1
            if counter == limit:
                break
class vectorfiles:
    def __init__(self):
        self.array = []
        
    def add_vectorlist(self,vlist):
        if not isinstance(vlist, vectorlist):
            raise Exception('Object supplied must be a vector list')
        else:
            if (vlist.ext):
                colour = 'red'
                legend = 'ext mode'
            else:
                colour = 'green'
                legend = 'normal'           
            self.array.append([vlist,colour,legend])
    def plotfiles(self,scatter=False,log=True):
        s = vectorlist()
        s.plotlists(self.array,scatter,log)
    def printfiles(self):
        for array in self.array:
            #print array,array[0].filename
            print array[0].filename
            
#filename = "Y:/reference/2015/12/C1_151231_B.EXT.GSE"
'''
filename = "default.GSE"

vlist1 = vectorlist()
vlist1.read_file(filename)
#vlist1.plotlist(color='red',legend='default')

filename = "cal.GSE"

vlist2 = vectorlist()
vlist2.read_file(filename)
#vlist2.plotlist(color='green',legend='caa')

vlist2.plotlists([[vlist2,'green','caa'],[vlist1,'red','default']])
'''
vfiles = vectorfiles()
reffolderahk114 = "Y:/reference/"
reffolder = "Z:/data/reference/"
sc = 1
start_date = date(2016,01,01)
end_date = date(2016,01,5)
dates = [start_date+timedelta(days=1)*i for i in range(abs(end_date-start_date).days)]
for datev in dates:
    file_dict = {}
    Year = str(datev.year)
    year = Year[2:4]
    month = '{0:02d}'.format(datev.month)
    day = '{0:02d}'.format(datev.day)
    
    folderahk114 = reffolderahk114+Year+'/'+month+'/'
    folder = reffolder+Year+'/'+month+'/'
    
    for file in os.listdir(folder):
        if "C"+str(sc) in file and year+month+day in file and ".P.GSE" in file:
            version = file[10]  
            #print "version:",version
            file_dict[version]=file
    l = file_dict.keys()
    if len(l):
        #print "number of files:",len(l)
        l.sort()
        #print "final version:",l[-1]
        #print ""
        file = folder+file_dict[l[-1]]
        vlist = vectorlist()
        vlist.read_file(file)
        vfiles.add_vectorlist(vlist)
    
    file_dict = {}
    for file in os.listdir(folderahk114):
        if "C"+str(sc) in file and year+month+day in file and ".EXT.GSE" in file:
            version = file[10]            
            file_dict[version]=file
            
    l = file_dict.keys()
    if len(l):
        l.sort()
        file = folderahk114+file_dict[l[-1]]
        vlist = vectorlist(ext=True)
        vlist.read_file(file)
        vfiles.add_vectorlist(vlist)   

vfiles.printfiles()
vfiles.plotfiles(scatter=True)