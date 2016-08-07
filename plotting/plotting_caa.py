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
        self.x=0
        self.y=0
        self.z=0
    def assigndatetime(self,datetime):
        self.datetime=datetime        
    def assignvalue(self,v):
        self.v = v
        self.x=v[0]
        self.y=v[1]
        self.z=v[2]
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
    def returnx(self):
        return [vector.x for vector in self.vectors]
    def returny(self):
        return [vector.y for vector in self.vectors]
    def returnz(self):
        return [vector.z for vector in self.vectors]
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
        output_file("plotcaa.html", title="Plotting Cluster II Data, CAA CAL", mode="cdn")
        
        TOOLS="resize,crosshair,pan,wheel_zoom,box_zoom,reset"
        
        # create a new plot with the tools above, and explicit ranges
        if log:
            p = figure(tools=TOOLS, width=1900, height=1000, y_axis_type='log', x_axis_type="datetime")
        else:
            p = figure(tools=TOOLS, width=1900, height=1000, x_axis_type="datetime")
        for entry in array:
            print "entry ",entry
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
            print "data"
            for i in range(20):
                print dates[i],data[i]
            if scatter:
                p.circle(dates,data,color=color,legend=legend,size=1)
            else:
                p.line(dates,data,color=color,legend=legend)
        p.xaxis.axis_label = 'Time'
        p.yaxis.axis_label = 'nT'
        show(p)
    def print_values(self,limit):
        counter = 0
        for vector in self.vectors:
            print vector.datetime, vector.magnitude, vector.x, vector.y,vector.z
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
            
filename = "Y:/reference/2015/12/CAAC1_151231_B.EXT.GSE"

vlist = vectorlist()
vlist.read_file(filename)
vlist.print_values(30)
vlist.plotlists([[vlist,'purple','x','x'],[vlist,'green','y','y'],[vlist,'red','z','z'],[vlist,'blue','mag','mag']],log=False)

'''

vfiles = vectorfiles()

l.sort()
file = folder+file_dict[l[-1]]
vlist = vectorlist()
vlist.read_file(file)
vfiles.add_vectorlist(vlist)
    

vfiles.printfiles()
vfiles.plotfiles(scatter=True)
'''