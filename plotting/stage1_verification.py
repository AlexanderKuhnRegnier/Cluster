import numpy as np
from bokeh.plotting import figure, output_file, show
from numpy import linalg as LA
from datetime import date,time,datetime,timedelta
import os
from getfile import getfile
import gzip
import matplotlib.pyplot as plt

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
        self.filename = filename
        with open(filename,'rb') as f:
            if 'EXT.GSE' in filename:
                count = 0
                for line in f:
                    #print "line", line
                    count += 1
                    try:
                        v = vector()
                        array = [i for i in line.split(" ") if i != '']
                        #print "array",array
                        
                        v.assigndatetime(count)
                        v.assignvalue(np.array([float(array[1]),float(array[2]),float(array[3])]))
                        v.calcmagnitude()
                        self.add_vector_entry(v)                 
                    except ValueError:
                        print "Something wrong with line"
            else:
                count = 0
                for line in f:
                    #print "line", line
                    count += 1
                    try:
                        v = vector()
                        array = [i for i in line.split(" ") if i != '']
                        #print "array",array
                        
                        v.assigndatetime(count)
                        v.assignvalue(np.array([float(array[0]),float(array[1]),float(array[2])]))
                        v.calcmagnitude()
                        self.add_vector_entry(v)                 
                    except ValueError:
                        print "Something wrong with line"

    def returndatetimes(self,start=0,end=len(self.vectors)):
        for i in range(start,len(end)):
            return self.vectors[i].datetime
        #return [vector.datetime for vector in self.vectors]
    def returnmagnitudes(self,start=0,end=len(self.vectors)):
        for i in range(start,len(end)):
            return self.vectors[i].magnitude
        #return [vector.magnitude for vector in self.vectors]
    def returnx(self,start=0,end=len(self.vectors)):
        for i in range(start,len(end)):
            return self.vectors[i].v[0]
        #return [vector.v[0] for vector in self.vectors]
    def returny(self,start=0,end=len(self.vectors)):
        for i in range(start,len(end)):
            return self.vectors[i].v[1]
        #return [vector.v[1] for vector in self.vectors]
    def returnz(self,start=0,end=len(self.vectors)):
        for i in range(start,len(end)):
            return self.vectors[i].v[2]
        #return [vector.v[2] for vector in self.vectors]

    def plot(self):
        f,axarr = plt.subplots(2,2) 
        axarr[0,0].scatter(self.returndatetimes(),self.returnmagnitudes(),s=100,c='r')
        axarr[0,0].set_title('mag')
        axarr[0,1].scatter(self.returndatetimes(),self.returnx(),s=100,c='r')
        axarr[0,1].set_title('x')
        axarr[1,0].scatter(self.returndatetimes(),self.returny(),s=100,c='r')
        axarr[1,0].set_title('y')
        axarr[1,1].scatter(self.returndatetimes(),self.returnz(),s=100,c='r')
        axarr[1,1].set_title('z')
        #ax.set_yscale('log')
        f.suptitle(self.filename)

    def plot2(self,vlist1,vlist2,start=100):
        global filename1,filename2
        f,axarr = plt.subplots(2,4,figsize=(35,25))
        f1 = filename1.split('/')[-1]
        f2 = filename2.split('/')[-1]
        #scale_factor = np.mean(vlist1.returnmagnitudes())/np.mean(vlist2.returnmagnitudes())        
        '''
        axarr[0,0].scatter(vlist2.returndatetimes(),np.array(vlist2.returnmagnitudes())*scale_factor,s=100,c='b')
        axarr[0,0].set_title('mag')
        axarr[0,1].scatter(vlist2.returndatetimes(),np.array(vlist2.returnx())*scale_factor,s=100,c='b')
        axarr[0,1].set_title('x')
        axarr[1,0].scatter(vlist2.returndatetimes(),np.array(vlist2.returny())*scale_factor,s=100,c='b')
        axarr[1,0].set_title('y')
        axarr[1,1].scatter(vlist2.returndatetimes(),np.array(vlist2.returnz())*scale_factor,s=100,c='b')
        axarr[1,1].set_title('z')
        #ax.set_yscale('log')
        '''
        #plot 45 entries at a time!
        end = start+45
        dt1  = vlist1.returndatetimes(start,end)
        mag1 = vlist1.returnmagnitudes(start,end)
        x1   = vlist1.returnx(start,end)
        y1   = vlist1.returny(start,end)
        z1   = vlist1.returnz(start,end)
    
        axarr[0,0].scatter(dt1,mag1,s=100,c='r')
        axarr[0,0].set_title('mag')
        axarr[0,1].scatter(dt1,x1,s=100,c='r')
        axarr[0,1].set_title('x')
        axarr[0,2].scatter(dt1,y1,s=100,c='r')
        axarr[0,2].set_title('y')
        axarr[0,3].scatter(dt1,z1,s=100,c='r')
        axarr[0,3].set_title('z')      

        dt2  = vlist2.returndatetimes(start,end)
        if dt1 != dt2:
            raise Exception("Lines don't match up!")
        mag2 = vlist2.returnmagnitudes(start,end)
        x2   = vlist2.returnx(start,end)
        y2   = vlist2.returny(start,end)
        z2   = vlist2.returnz(start,end)
        
        axarr[1,0].scatter(dt2,mag2,s=100,c='r')
        axarr[1,0].set_title('mag')
        axarr[1,1].scatter(dt2,x2,s=100,c='r')
        axarr[1,1].set_title('x')
        axarr[1,2].scatter(dt2,y2,s=100,c='r')
        axarr[1,2].set_title('y')
        axarr[1,3].scatter(dt2,z2,s=100,c='r')
        axarr[1,3].set_title('z')            
        
        f.suptitle(f1+'(r)'+' '+f2+'(b)',fontsize = 20)
        
        f.savefig('Y:/comparisons/'+f1+'-'+f2+'.png')

    def print_values(self,limit):
        counter = 0
        print "filename:",self.filename
        for vector in self.vectors:
            if counter == limit:
                break            
            counter+=1
            print vector.datetime, vector.v, vector.magnitude
            
#filename = 'Y:/extended/2016/01/C1_160101_B.E1'
#filename1 = 'Z:/data/extended/2006/01/C1_060113_B.E0'
#filename2 = 'Z:/data/reference/2006/01/C1_060113_B.EXT.GSE'
plt.close('all')
filename1 = 'Z:/data/extended/2016/01/C1_160114_B.E0'
filename2 = 'Z:/data/reference/2016/01/C1_160113_B.EXT.GSE'
vlist1 = vectorlist()
vlist1.read_file(filename1)
#vlist1.print_values(10)
#vlist.plot()
vlist2 = vectorlist()
vlist2.read_file(filename2)
#vlist2.print_values(10)

vlist = vectorlist()

#vlist.plot2(vlist1,vlist2)
vlist1.plot()
vlist2.plot()