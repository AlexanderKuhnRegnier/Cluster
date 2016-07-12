import numpy as np
#import matplotlib.pyplot as plt
#import datetime
import math
import subprocess
import os
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
    upperexp = int((exp+127/2.))
    lowerexp = int(exp+127&1)
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
    
#plt.close('all')

#Enfilename = 'Y:/testdata/test.E0'
#EXTfilename = 'Y:/testdata/test.EXT.GSE'
Enfilename = '/home/ahk114/testdata/test.E0'

#generate raw x,y,z data in engineering units
mini = 10
maxi = 65000
t = np.arange(0,10,0.005)
tshift1 = t+np.pi/3.
tshift2 = t+2*np.pi/3.
x = (np.sin(t)+1)
y = (np.sin(tshift1)+1)
z = (np.sin(tshift2)+1)
l=[x,y,z]
for k in range(3):
    l[k] = ((l[k]/np.max(l[k]))*65000)+10
(x,y,z) = l

#10%period
p10 = t.shape[0]/10
rlist = [2,3,4,5,6,7]
c = -1
r = []
for i in range(t.shape[0]):
    if not i%p10:
        c += 1
    if c==len(rlist):
        c = 0
    r.append(rlist[c])
'''
magnitude = np.linalg.norm(np.vstack((x,y,z)),axis=0) #just for testing
#raw data plotting, works as expted 12/07
f,axes = plt.subplots(4,1,figsize=(20,15))
axes[0].scatter(t,x,color='r')
axes[1].scatter(t,y,color='b')
axes[2].scatter(t,z,color='g')
axes[3].scatter(t,magnitude,color='y')
'''
def writeEntest():
    with open(Enfilename,'wb') as f:
        for i in range(t.shape[0]):
            f.write('{0:d} {1:d} {2:d} {3:d} \n'.format(int(x[i]),int(y[i]),int(z[i]),r[i]))
            
writeEntest()
            
###################
'''
Stage3 recreation here
'''
###################
x = x.reshape(-1,1)
y = y.reshape(-1,1)
z = z.reshape(-1,1)
vector = np.hstack((x,y,z))

for v in vector:
    for i in range(3):
        value = v[i]
        if value>32767:
            value = (v[i]-65536.)/scale(r[i])
        else:
            value = (v[i])/scale(r[i])
        v[i] = value
'''
magnitude = np.linalg.norm(vector,axis=1) #just for testing
#raw data plotting, works as expted 12/07
f,axes = plt.subplots(4,1,figsize=(20,15))
axes[0].scatter(t,vector[:,0],color='r')
axes[1].scatter(t,vector[:,1],color='b')
axes[2].scatter(t,vector[:,2],color='g')
axes[3].scatter(t,magnitude,color='y')
'''


'''
All event data pertains to 160611 BS data, on 160609!
'''
EventTime_Unix=1465504194

RAW = '/cluster/data/raw/'
EXT = '/home/ahk114/extended/'
PROC = '/home/ahk114/testdata/'

sattfile=RAW+'2016/06/'+'C'+'1'+'_'+'160609'+'_'+'B'+'.SATT' #Spacecraft Attitude and Spin Rates
stoffile=RAW+'2016/06/'+'C'+'1'+'_'+'160609'+'_'+'B'+'.STOF'
procfile=PROC+'C'+'1'+'_'+'160609'+'_'+'B'+'.EXT.GSE' #Where the data goes - into the reference folder!

#outhandle = open('/home/ahk114/testdata/160609.EXT','wb')
tmp = '/home/ahk114/testdata/ExtProcRaw_123'
tmp2 = '/home/ahk114/testdata/ExtProcDecoded_123'
datahandle = open(tmp,'wb')

for i in range(len(t)):
    #timestring = datetime.datetime.fromtimestamp(EventTime_Unix+1).strftime('%Y-%m-%d\T%H:%M:%S)
    time = EventTime_Unix+i
    hexbx = float2hex(vector[i,0])
    hexby = float2hex(vector[i,1])
    hexbz = float2hex(vector[i,2])
    time1 = integer2hex(time)
    time2 = integer2hex(floatbit(time)*1e9)
    data = [(r[i]<<4)+14,16,128+(1&7),1,
            time1[0],time1[1],time1[2],time1[3],
            time2[0],time2[1],time2[2],time2[3]]
    data.extend(hexbx)
    data.extend(hexby)
    data.extend(hexbz)
    data.extend([0,0,0,0,
                 0,0,0,0])
    for content in data:
        datahandle.write(chr(content))
datahandle.close()

print sattfile
os.system('cat '+sattfile+' | wc')

print os.stat(sattfile)
print stoffile
print os.stat(stoffile)

print tmp
print os.stat(tmp)
print tmp2
print procfile
#exec("FGMPATH=/cluster/operations/calibration/default ; export FGMPATH ; cat ".$tmp." | /cluster/operations/software/dp/bin/fgmhrt -s gse -a ".$sattfile." | /cluster/operations/software/dp/bin/fgmpos -p ".$stoffile." | /cluster/operations/software/dp/bin/igmvec -o ".$tmp2." ; cp ".$tmp2." ".$procfile);
cmd = ('FGMPATH=/cluster/operations/calibration/default ; '
        'export FGMPATH ; cat '+tmp+' | '
        '/cluster/operations/software/dp/bin/fgmhrt -s gse -a '+sattfile+' | ' 
        '/cluster/operations/software/dp/bin/fgmpos -p '+stoffile+' | '
        '/cluster/operations/software/dp/bin/igmvec -o '+tmp2+' ; '
        'cp '+tmp2+' '+procfile+' ;')
#output = subprocess.check_output(cmd,shell=True)
#output = subprocess.Popen(cmd,stdout=subprocess.PIPE).communicate()[0]
#output = subprocess.Popen(cmd)

sample = '/home/ahk114/testdata/sample'
sample2 = '/home/ahk114/testdata/sample2'
sample3 = '/home/ahk114/testdata/sample3'
'''
cmd = ('FGMPATH=/cluster/operations/calibration/default ; '
        'export FGMPATH ; cat '+tmp+' | /cluster/operations/software/dp/bin/fgmhrt -s gse -a '+sattfile+' >> '+sample+' ; '
        'cat '+sample+' | /cluster/operations/software/dp/bin/fgmpos -p '+stoffile+' >> '+sample2+ ' ; '
        'cat '+sample2+' | /cluster/operations/software/dp/bin/igmvec -o '+tmp2+' ; '
        'cp '+tmp2+' '+procfile+' ;')     
'''
print "executing:",cmd
os.system(cmd)