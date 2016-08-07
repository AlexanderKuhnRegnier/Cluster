import numpy as np
import matplotlib.pyplot as plt
import datetime
import math
import os
import pickle


'''
Needs to create .E0 raw data files:
raw x,y,z values in engineering units, plus a range
eg.
Z:/data/extended/2014/04/C1_140402_B.E0 
['61881', '3834', '62604', '2', '2553', 'WHOLE', 'EVEN', '11\n']

Also need to create .EXT.GSE files, converted from engineering units, and passed through the 
processing pipeline, in order to see what effect this has on known data!
eg.
Z:/data/reference/2014/04/C1_140402_B.EXT.GSE 
['2014-04-02T12:00:49.107Z', '6.0933', '13.8797', '12.6923', '72802.2', '-15094.5', '-75324.1', '\n']
'''
def float2hex(f):
    if f==0:
        return [0,0,0,0]
    if f>0:
        sign = 0
    else:
        sign = 1
    f = abs(f)
    exp = int(math.log10(f)/math.log10(2))
    remainder = int(8388608*((f/math.pow(2,exp))-1))
    upperexp = int(((exp+127)/2.))
    lowerexp = int((exp+127)&1)
    return [remainder&255,(remainder>>8)&255,
            (lowerexp*128)+((remainder>>16)&127),
            (sign*128)+upperexp]

def floatbit(f):
    return f-int(f)

def integer2hex(i):
    i = int(i)
    return [i&255,(i>>8)&255,(i>>16)&255,i>>24]


def scale(r):
    scale_list = [1024.,256.,64.,16.,4.,1.,.25]
    return scale_list[r-1]
    
'''
#reset counter
f = open('Y:/Cluster/plotting/filenumber','w')
f.write(str(0))
f.close()  
'''
'''
fn = 0
f = open('Y:/Cluster/plotting/filenumber','r')
fn = int(f.read())
f.close()
f = open('Y:/Cluster/plotting/filenumber','w')
f.write(str(int(fn+1)))
f.close()
'''
testdata = 'Y:/testdata/'  
for f in os.listdir(testdata):
    if '.pickle' in f:
        fn = f.split('pickle')[-1]
        print "Found pickle file:",f," filenumber:",fn
        break
#print "Filenumber:",fn
#fn = str(fn)
    

#testdata = '/home/ahk114/testdata/'

#plt.close('all')
#os.system('python /home/ahk114/Cluster/plotting/plotting_verification_stage1and3.py')

picklefilename = testdata+'t_data.pickle'+fn
print "Trying to open:",picklefilename
f = open(picklefilename,'r')
t = pickle.load(f)
f.close()
print "Loaded t data, length:",len(t)

picklefilename = testdata+'r_data.pickle'+fn
print "Trying to open:",picklefilename
f = open(picklefilename,'r')
r = pickle.load(f)
f.close()
print "Loaded r data, len:",len(r)

picklefilename = testdata+'vectors_raw.pickle'+fn
print "Trying to open:",picklefilename
f = open(picklefilename,'r')
vectors = pickle.load(f)
f.close()
print "Loaded raw vectors, shape:",vectors.shape

picklefilename = testdata+'magnitude_raw.pickle'+fn
print "Trying to open:",picklefilename
f = open(picklefilename,'r')
magnitude_raw =  pickle.load(f)
f.close()
print "Loaded raw mags, shape:",magnitude_raw.shape

'''
f,axes = plt.subplots(4,1,figsize=(20,15))
axes[0].scatter(t,vectors[:,0],color='r')
axes[0].set_title(list(set(vectors[:,0]))[:8])
axes[1].scatter(t,vectors[:,1],color='b')
axes[1].set_title(list(set(vectors[:,1]))[:8])
axes[2].scatter(t,vectors[:,2],color='g')
axes[2].set_title(list(set(vectors[:,2]))[:8])
axes[3].scatter(t,magnitude_raw,color='y')
axes[3].set_title(list(set(magnitude_raw))[:8])
f.canvas.set_window_title('Raw')
'''
###################
'''
Stage3 recreation here
'''
###################

picklefilename = testdata+'vector_scaled.pickle'+fn
print "Trying to open:",picklefilename
f = open(picklefilename,'r')
vector=pickle.load(f)
f.close()
print "Loaded scaled vector, shape:",vector.shape

picklefilename = testdata+'magnitude_scaled.pickle'+fn
print "Trying to open:",picklefilename
f = open(picklefilename,'r')
magnitude= pickle.load(f)
f.close()
print "Loaded scaled mags, shape:",magnitude.shape
'''
f,axes = plt.subplots(4,1,figsize=(20,15))
axes[0].scatter(t,vector[:,0],color='r')
axes[0].set_title(list(set(vector[:,0]))[:8])
axes[1].scatter(t,vector[:,1],color='b')
axes[1].set_title(list(set(vector[:,1]))[:8])
axes[2].scatter(t,vector[:,2],color='g')
axes[2].set_title(list(set(vector[:,2]))[:8])
axes[3].scatter(t,magnitude,color='y')
axes[3].set_title(list(set(magnitude))[:8])
f.canvas.set_window_title('Converted')
'''
#PROC = '/home/ahk114/testdata/'
PROC = 'Y:/testdata/'
procfile=PROC+'C'+'1'+'_'+'160122'+'_'+'B'+'.EXT.GSE'+fn #Where the data goes - into the reference folder!

extvector = np.array([],dtype=np.float64).reshape(-1,3)
extmags = np.array([],dtype=np.float64)

with open(procfile,'r') as f:
	count = 0
	for line in f:
		#print "line", line
		count += 1
		try:
			array = [i for i in line.split(" ") if i != '']
			#if 10<count<20:
				#print "EXT GSE array",array
			extvector=np.vstack((extvector,np.array([float(array[1]),float(array[2]),float(array[3])])))
			extmags = np.append(extmags,np.linalg.norm(extvector[-1:][0]))
		except ValueError:
			print "Something wrong with line"
   
print "Read procfile:",procfile
print "extvector, shape:",extvector.shape
print "extmags,shape:",extmags.shape

'''
f,axes = plt.subplots(4,1,figsize=(20,15))
axes[0].scatter(t,extvector[:,0],color='r')
axes[0].set_title(list(set(extvector[:,0]))[:3])
axes[2].scatter(t,extvector[:,1],color='b')
axes[2].set_title(list(set(extvector[:,1]))[:3])
axes[1].scatter(t,extvector[:,2],color='g')
axes[1].set_title(list(set(extvector[:,2]))[:3])
axes[3].scatter(t,extmags,color='y')
axes[3].set_title(str(list(set(extmags))[:3])+' '+str(len(set(extmags))))
f.canvas.set_window_title('After DP pipeline, caution: axes matched to raw data axes')			
f.savefig(testdata+'10.0timestep1000.15input.png')
'''
plt.close('all')

picklefilename = testdata+'dt.pickle'
print "Trying to open:",picklefilename
f = open(picklefilename+fn,'r')
dt = pickle.load(f)
f.close()
print "Loaded dt, value:",dt

timesd = [datetime.datetime(1,1,1,0,0,0)+i*datetime.timedelta(seconds=dt) for i in range(t.shape[0])]
#print times
times = [ti.time() for ti in timesd]
#print times

scattersize = 100

mod = 1 #if zoomed in or not!!

save = 1
filename = 'sine test1'

if mod:
    fig,axes = plt.subplots(4,3,figsize=(20,15))

    min_scale = 0.999
    max_scale = 1.001

    start = 0
    end = len(times)
    #start=18
    #end = 20
 
    axes[1,0].scatter(times[start:end],extvector[:,0][start:end],color='r',s=scattersize)
    axes[1,0].set_ylim((np.min(extvector[:,0][start:end])*min_scale,np.max(extvector[:,0][start:end])*max_scale))
    #axes[1,2].set_title(sorted(list(set(extvector[:,0]))[:1],key=abs))
    axes[2,0].scatter(times[start:end],-1*extvector[:,1][start:end],color='b',s=scattersize)
    axes[2,0].set_ylim((np.min(-1*extvector[:,1][start:end])*min_scale,np.max(-1*extvector[:,1][start:end])*max_scale))
    #axes[2,2].set_title(sorted(list(set(extvector[:,1]))[:1],key=abs))
    axes[0,0].scatter(times[start:end],-1*extvector[:,2][start:end],color='g',s=scattersize)
    axes[0,0].set_ylim((np.min(-1*extvector[:,2][start:end])*min_scale,np.max(-1*extvector[:,2][start:end])*max_scale))
    #axes[0,2].set_title(sorted(list(set(extvector[:,2]))[:1],key=abs))
    axes[3,0].scatter(times[start:end],extmags[start:end],color='y',s=scattersize)
    axes[3,0].set_ylim((np.min(extmags[start:end])*min_scale,np.max(extmags[start:end])*max_scale))
    #axes[3,2].set_title(str(sorted(list(set(extmags))[:1]))+' '+str(len(set(extmags))))
    
    start = 0
    end = len(times)
    start=20
    end = 30
    
    axes[1,1].scatter(times[start:end],extvector[:,0][start:end],color='r',s=scattersize)
    axes[1,1].set_ylim((np.min(extvector[:,0][start:end])*min_scale,np.max(extvector[:,0][start:end])*max_scale))
    #axes[1,2].set_title(sorted(list(set(extvector[:,0]))[:1],key=abs))
    axes[2,1].scatter(times[start:end],-1*extvector[:,1][start:end],color='b',s=scattersize)
    axes[2,1].set_ylim((np.min(-1*extvector[:,1][start:end])*min_scale,np.max(-1*extvector[:,1][start:end])*max_scale))
    #axes[2,2].set_title(sorted(list(set(extvector[:,1]))[:1],key=abs))
    axes[0,1].scatter(times[start:end],-1*extvector[:,2][start:end],color='g',s=scattersize)
    axes[0,1].set_ylim((np.min(-1*extvector[:,2][start:end])*min_scale,np.max(-1*extvector[:,2][start:end])*max_scale))
    #axes[0,2].set_title(sorted(list(set(extvector[:,2]))[:1],key=abs))
    axes[3,1].scatter(times[start:end],extmags[start:end],color='y',s=scattersize)
    axes[3,1].set_ylim((np.min(extmags[start:end])*min_scale,np.max(extmags[start:end])*max_scale))
    #axes[3,2].set_title(str(sorted(list(set(extmags))[:1]))+' '+str(len(set(extmags))))

    start = 0
    end = len(times)
    start=28
    end = 30    
    
    axes[1,2].scatter(times[start:end],extvector[:,0][start:end],color='r',s=scattersize)
    axes[1,2].set_ylim((np.min(extvector[:,0][start:end])*min_scale,np.max(extvector[:,0][start:end])*max_scale))
    #axes[1,2].set_title(sorted(list(set(extvector[:,0]))[:1],key=abs))
    axes[2,2].scatter(times[start:end],-1*extvector[:,1][start:end],color='b',s=scattersize)
    axes[2,2].set_ylim((np.min(-1*extvector[:,1][start:end])*min_scale,np.max(-1*extvector[:,1][start:end])*max_scale))
    #axes[2,2].set_title(sorted(list(set(extvector[:,1]))[:1],key=abs))
    axes[0,2].scatter(times[start:end],-1*extvector[:,2][start:end],color='g',s=scattersize)
    axes[0,2].set_ylim((np.min(-1*extvector[:,2][start:end])*min_scale,np.max(-1*extvector[:,2][start:end])*max_scale))
    #axes[0,2].set_title(sorted(list(set(extvector[:,2]))[:1],key=abs))
    axes[3,2].scatter(times[start:end],extmags[start:end],color='y',s=scattersize)
    axes[3,2].set_ylim((np.min(extmags[start:end])*min_scale,np.max(extmags[start:end])*max_scale))
    #axes[3,2].set_title(str(sorted(list(set(extmags))[:1]))+' '+str(len(set(extmags))))

if not mod:
    fig,axes = plt.subplots(4,3,figsize=(20,15))
    
    axes[0,0].scatter(times,vectors[:,0],color='r',s=scattersize)
    #axes[0,0].set_title(sorted(list(set(vectors[:,0]))[:1]))
    axes[1,0].scatter(times,vectors[:,1],color='b',s=scattersize)
    #axes[1,0].set_title(sorted(list(set(vectors[:,1]))[:1]))
    axes[2,0].scatter(times,vectors[:,2],color='g',s=scattersize)
    #axes[2,0].set_title(sorted(list(set(vectors[:,2]))[:1]))
    axes[3,0].scatter(times,magnitude_raw,color='y',s=scattersize)
    #axes[3,0].set_title(sorted(list(set(magnitude_raw))[:1]))
    
    
    axes[0,1].scatter(times,vector[:,0],color='r',s=scattersize)
    #axes[0,1].set_title(sorted(list(set(vector[:,0]))[:1]))
    axes[1,1].scatter(times,vector[:,1],color='b',s=scattersize)
    #axes[1,1].set_title(sorted(list(set(vector[:,1]))[:1]))
    axes[2,1].scatter(times,vector[:,2],color='g',s=scattersize)
    #axes[2,1].set_title(sorted(list(set(vector[:,2]))[:1]))
    axes[3,1].scatter(times,magnitude,color='y',s=scattersize)
    #axes[3,1].set_title(sorted(list(set(magnitude))[:1]))
    
    start = 0
    end = len(times)
    axes[1,2].scatter(times[start:end],extvector[:,0][start:end],color='r',s=scattersize)
    axes[1,2].set_ylim((np.min(extvector[:,0][start:end]),np.max(extvector[:,0][start:end])))
    #axes[1,2].set_title(sorted(list(set(extvector[:,0]))[:1],key=abs))
    axes[2,2].scatter(times[start:end],-1*extvector[:,1][start:end],color='b',s=scattersize)
    axes[2,2].set_ylim((np.min(-1*extvector[:,1][start:end]),np.max(-1*extvector[:,1][start:end])))
    #axes[2,2].set_title(sorted(list(set(extvector[:,1]))[:1],key=abs))
    axes[0,2].scatter(times[start:end],-1*extvector[:,2][start:end],color='g',s=scattersize)
    axes[0,2].set_ylim((np.min(-1*extvector[:,2][start:end]),np.max(-1*extvector[:,2][start:end])))
    #axes[0,2].set_title(sorted(list(set(extvector[:,2]))[:1],key=abs))
    axes[3,2].scatter(times[start:end],extmags[start:end],color='y',s=scattersize)
    axes[3,2].set_ylim((np.min(extmags[start:end]),np.max(extmags[start:end])))
    #axes[3,2].set_title(str(sorted(list(set(extmags))[:1]))+' '+str(len(set(extmags))))
 

for i in range(4):
    if not mod:
        axes[i,0].set_ylabel('engineering units')
    else:
        axes[i,0].set_ylabel('m-field (nT)')
    axes[i,1].set_ylabel('m-field (nT)')
    axes[i,2].set_ylabel('m-field (nT)')

axes[0,2].set_ylabel('m-field (nT) x-1')
axes[2,2].set_ylabel('m-field (nT) x-1')

if mod:
    axes[0,1].set_ylabel('m-field (nT) x-1')
    axes[2,1].set_ylabel('m-field (nT) x-1')
    axes[0,0].set_ylabel('m-field (nT) x-1')
    axes[2,0].set_ylabel('m-field (nT) x-1')    
if not mod:
    arr = vectors[:,0]
    axes[0,0].set_title('Engineering Units\nx'+'  range: '+format(np.ptp(arr),'.3e'))
    arr = vector[:,0]
    axes[0,1].set_title('Scaled Engineering Units -> nT\nx'+'  range: '+format(np.ptp(arr),'.3e'))
    arr = -1*extvector[:,2][start:end]
    axes[0,2].set_title('Magnetic Field in GSE (nT)\nz'+'  range: '+format(np.ptp(arr),'.3e'))
    arr = vectors[:,1]
    axes[1,0].set_title('y'+'  range: '+format(np.ptp(arr),'.3e'))
    arr = vector[:,1]
    axes[1,1].set_title('y'+'  range: '+format(np.ptp(arr),'.3e'))
    arr = extvector[:,0][start:end]
    axes[1,2].set_title('x'+'  range: '+format(np.ptp(arr),'.3e'))
    arr = vectors[:,2]
    axes[2,0].set_title('z'+'  range: '+format(np.ptp(arr),'.3e'))
    arr = vector[:,2]
    axes[2,1].set_title('z'+'  range: '+format(np.ptp(arr),'.3e'))
    arr = -1*extvector[:,1][start:end]
    axes[2,2].set_title('y'+'  range: '+format(np.ptp(arr),'.3e'))
    arr = magnitude_raw
    axes[3,0].set_title('mag'+'  range: '+format(np.ptp(arr),'.3e'))
    arr = magnitude
    axes[3,1].set_title('mag'+'  range: '+format(np.ptp(arr),'.3e'))
    arr = extmags[start:end]
    axes[3,2].set_title('mag'+'  range: '+format(np.ptp(arr),'.3e'))
if mod:
    arr = vectors[:,0]
    #axes[0,0].set_title('Magnetic Field in GSE (nT)\nz'+'  range: '+format(np.ptp(arr),'.3e'))
    axes[0,0].set_title('Magnetic Field in GSE (nT)\nz')
    arr = vector[:,0]
    #axes[0,1].set_title('Magnetic Field in GSE (nT)\nz'+'  range: '+format(np.ptp(arr),'.3e'))
    axes[0,1].set_title('Magnetic Field in GSE (nT)\nz')
    arr = -1*extvector[:,2][start:end]
    #axes[0,2].set_title('Magnetic Field in GSE (nT)\nz'+'  range: '+format(np.ptp(arr),'.3e'))
    axes[0,2].set_title('Magnetic Field in GSE (nT)\nz')
    
    axes[1,0].set_title('x')
    axes[1,1].set_title('x')
    axes[1,2].set_title('x')
    axes[2,0].set_title('y')
    axes[2,1].set_title('y')
    axes[2,2].set_title('y')
    axes[3,0].set_title('mag')
    axes[3,1].set_title('mag')
    axes[3,2].set_title('mag')
    
plt.gcf().autofmt_xdate()
#f.canvas.set_window_title('')
figManager = plt.get_current_fig_manager()
figManager.window.showMaximized()
suptitle_string = ('Passing two dots into the software does not prove to cause '
            'any problems, with low or large time difference'
            '\n')
suptitle_opt= (' timestep:'+format(dt,'.2f')+' number of points:'+format(len(times),'05d')+
            ' total time difference:'
            +str(timesd[-1]-timesd[0]))
fig.suptitle(suptitle_string+suptitle_opt,fontsize = 16)
plt.show()

print len(times)
print len(vector[:,0])
print "timestep:",dt
print timesd[-1]-timesd[0]

from shutil import copy
if save:
    try:
        new_dir = 'Y:/testdata/'+filename.replace(' ','')
        os.mkdir(new_dir)
        copy('Y:/Cluster/plotting/plotting_verification_stage1and3_matplotlib.py',new_dir)
        copy('Y:/Cluster/plotting/plotting_verification_stage1and3.py',new_dir)
        print "Saved Python scripts for future reference!"
    except OSError:
        print "Warning: directory Already created, not saving scripts again!"


if save:
    if mod:
        filename += ' zoom '
    else:
        filename += ' no zoom '
    filename += suptitle_opt.replace(':',' ')
    while filename in os.listdir(testdata):
        filename += '1'
    filename += '.png'
    fig.savefig(testdata+filename,dpi=280)#
