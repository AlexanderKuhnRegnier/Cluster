import numpy as np
import matplotlib.pyplot as plt
#import datetime
import math
import os
import cPickle as pickle


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
    
testdata = 'Y:/testdata/'  
#testdata = '/home/ahk114/testdata/'

plt.close('all')
#os.system('python /home/ahk114/Cluster/plotting/plotting_verification_stage1and3.py')


picklefilename = testdata+'t_data.pickle'
t = pickle.load(open(picklefilename,'rb'))
picklefilename = testdata+'r_data.pickle'
r = pickle.load(open(picklefilename,'rb'))
picklefilename = testdata+'vectors_raw.pickle'
vectors = pickle.load(open(picklefilename,'rb'))
picklefilename = testdata+'magnitude_raw.pickle'
magnitude_raw =  pickle.load(open(picklefilename,'rb'))


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

###################
'''
Stage3 recreation here
'''
###################

picklefilename = testdata+'vector_scaled.pickle'
vector=pickle.load(open(picklefilename,'rb'))
picklefilename = testdata+'magnitude_scaled.pickle'
magnitude= pickle.load(open(picklefilename,'rb'))

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

#PROC = '/home/ahk114/testdata/'
PROC = 'Y:/testdata/'
procfile=PROC+'C'+'1'+'_'+'160122'+'_'+'B'+'.EXT.GSE' #Where the data goes - into the reference folder!

extvector = np.array([],dtype=np.float64).reshape(-1,3)
extmags = np.array([],dtype=np.float64)

with open(procfile,'rb') as f:
	count = 0
	for line in f:
		#print "line", line
		count += 1
		try:
			array = [i for i in line.split(" ") if i != '']
			if 10<count<20:
				print "EXT GSE array",array
			extvector=np.vstack((extvector,np.array([float(array[1]),float(array[2]),float(array[3])])))
			extmags = np.append(extmags,np.linalg.norm(extvector[-1:][0]))
		except ValueError:
			print "Something wrong with line"


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
#f.savefig(testdata+'0.02improvedtimestep100.15input.png')


f,axes = plt.subplots(4,3,figsize=(20,15))
axes[0,0].scatter(t,vectors[:,0],color='r')
axes[0,0].set_title(sorted(list(set(vectors[:,0]))[:8]))
axes[1,0].scatter(t,vectors[:,1],color='b')
axes[1,0].set_title(sorted(list(set(vectors[:,1]))[:8]))
axes[2,0].scatter(t,vectors[:,2],color='g')
axes[2,0].set_title(sorted(list(set(vectors[:,2]))[:8]))
axes[3,0].scatter(t,magnitude_raw,color='y')
axes[3,0].set_title(sorted(list(set(magnitude_raw))[:8]))
#f.canvas.set_window_title('Raw')

axes[0,1].scatter(t,vector[:,0],color='r')
axes[0,1].set_title(sorted(list(set(vector[:,0]))[:8]))
axes[1,1].scatter(t,vector[:,1],color='b')
axes[1,1].set_title(sorted(list(set(vector[:,1]))[:8]))
axes[2,1].scatter(t,vector[:,2],color='g')
axes[2,1].set_title(sorted(list(set(vector[:,2]))[:8]))
axes[3,1].scatter(t,magnitude,color='y')
axes[3,1].set_title(sorted(list(set(magnitude))[:8]))
#f.canvas.set_window_title('Converted')

axes[1,2].scatter(t,extvector[:,0],color='r')
axes[1,2].set_title(sorted(list(set(extvector[:,0]))[:3],key=abs))
axes[2,2].scatter(t,extvector[:,1],color='b')
axes[2,2].set_title(sorted(list(set(extvector[:,1]))[:3],key=abs))
axes[0,2].scatter(t,extvector[:,2],color='g')
axes[0,2].set_title(sorted(list(set(extvector[:,2]))[:3],key=abs))
axes[3,2].scatter(t,extmags,color='y')
axes[3,2].set_title(str(sorted(list(set(extmags))[:3]))+' '+str(len(set(extmags))))
f.canvas.set_window_title('Raw   ----     Converted   -----   After DP pipeline, caution: axes matched to raw data axes')			
figManager = plt.get_current_fig_manager()
figManager.window.showMaximized()

plt.show()