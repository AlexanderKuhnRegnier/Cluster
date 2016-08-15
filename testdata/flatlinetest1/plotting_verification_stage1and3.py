import numpy as np
import math
import os
import pickle
import datetime
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
    
#plt.close('all')

#Enfilename = 'Y:/testdata/test.E0'
#EXTfilename = 'Y:/testdata/test.EXT.GSE'

#generate raw x,y,z data in engineering units

'''
#reset counter
f = open('/home/ahk114/testdata/filenumber','w')
f.write(str(0))
f.close()  
'''

fn = 0
f = open('/home/ahk114/testdata/filenumber','r')
fn = int(f.read())
f.close()
f = open('/home/ahk114/testdata/filenumber','w')
f.write(str(int(fn+1)))
f.close()

print "Filenumber:",fn
fn = str(fn)
'''
filenamelist = ('C1_160122_B.EXT.GSE'+str(int(fn)-1),
                'dt.pickle'+str(int(fn)-1),
                'ExtProcDecoded_123',
                'ExtProcRaw_123',
                'magnitude_raw.pickle'+str(int(fn)-1),
                'magnitude_scaled.pickle'+str(int(fn)-1),
                'r_data.pickle'+str(int(fn)-1),
                't_data.pickle'+str(int(fn)-1),
                'test.E0',
                'vector_scaled.pickle'+str(int(fn)-1),
                'vectors_raw.pickle'+str(int(fn)-1))
'''
for f in os.listdir('/home/ahk114/testdata/'):
    if '.EXT.GSE' in f or '.pickle' in f:
        print "Removing:",f
        os.remove(os.path.join('/home/ahk114/testdata/',f))

print "Previous files removed!"


mini = 10
maxi = 2000

dt = 10.
t = np.linspace(3.6,4,num=100)

tshift1 = t+np.pi/3.
tshift2 = t+2*np.pi/3.

sin=False

if sin==True:
    x = (np.sin(t)+1).reshape(t.shape[0],1)*5000
    y = (np.sin(tshift1)+1).reshape(t.shape[0],1)*5000
    z = (np.sin(tshift2)+1).reshape(t.shape[0],1)*5000
else:
    num = t.shape[0]
    gradient = 0
    offset =10
    scalex=20
    scaley=10
    scalez=10
    scales = [scalex,scaley,scalez]
    if abs(np.max(scales)*(gradient)*num+offset) > 65000:
        raise Exception("Gradient,scale and offset are too large")
    x = scalex*(np.linspace(0,gradient*num,num=num)+offset).reshape(-1,1)
    y = scaley*(np.linspace(0,gradient*num,num=num)+offset).reshape(-1,1)
    z = scalez*(np.linspace(0,gradient*num,num=num)+offset).reshape(-1,1)

print "max, min values:"
print np.max(x),np.min(x)
print np.max(y),np.min(y)
print np.max(z),np.min(z)

#10%period
div = 1  #the higher div, the more range changes there are!!
p10 = t.shape[0]/int(div)
rlist = [2,3,4,5,6,7]
c = -1
r = []
for i in range(t.shape[0]):
    if not i%p10:
        c += 1
    if c==len(rlist):
        c = 0
    r.append(rlist[c])


testdata = '/home/ahk114/testdata/'

picklefilename = testdata+'t_data.pickle'
f = open(picklefilename+fn,'w')
pickle.dump(t,f)
f.close()

picklefilename = testdata+'r_data.pickle'
f = open(picklefilename+fn,'w')
pickle.dump(r,f)
f.close()

vectors_raw = np.hstack((x,y,z))
magnitude_raw = np.array([],dtype=np.float64).reshape(1,0)
for i in range(vectors_raw.shape[0]):
    magnitude_raw = np.append(magnitude_raw,np.linalg.norm(vectors_raw[i,:]))
picklefilename = testdata+'vectors_raw.pickle'
f = open(picklefilename+fn,'w')
pickle.dump(vectors_raw,f)
f.close()
picklefilename = testdata+'magnitude_raw.pickle'
f = open(picklefilename+fn,'w')
pickle.dump(magnitude_raw,f)
f.close()

Enfilename = '/home/ahk114/testdata/test.E0'
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
r_prev = 0
count = 0
for rvalue,v in zip(r,vector):
    count += 1
    r_now = rvalue
    if r_now != r_prev:
        r_prev = r_now
        print "Range:",count,r_now
    for i in range(3):
        value = v[i]
        if value>32767:
            #print "negative"
            value = (v[i]-65536.)/scale(rvalue)
        else:
            value = (v[i])/scale(rvalue)
        v[i] = value

magnitude = np.array([],dtype=np.float64).reshape(1,0)
for i in range(vector.shape[0]):
    magnitude = np.append(magnitude,np.linalg.norm(vector[i,:]))
picklefilename = testdata+'vector_scaled.pickle'
f = open(picklefilename+fn,'w')
pickle.dump(vector,f)
f.close()
picklefilename = testdata+'magnitude_scaled.pickle'
f = open(picklefilename+fn,'w')
pickle.dump(magnitude,f)
f.close()

'''
All event data pertains to 160123 BS data, on 160122!
'''
EventTime_Unix=1453435194

RAW = '/cluster/data/raw/'
EXT = '/home/ahk114/extended/'
PROC = '/home/ahk114/testdata/'

sattfile=RAW+'2016/01/'+'C'+'1'+'_'+'160122'+'_'+'B'+'.SATT' #Spacecraft Attitude and Spin Rates
stoffile=RAW+'2016/01/'+'C'+'1'+'_'+'160122'+'_'+'B'+'.STOF'
procfile=PROC+'C'+'1'+'_'+'160122'+'_'+'B'+'.EXT.GSE'+fn #Where the data goes - into the reference folder!


tmp = '/home/ahk114/testdata/ExtProcRaw_123'
tmp2 = '/home/ahk114/testdata/ExtProcDecoded_123'
datahandle = open(tmp,'wb')


picklefilename = testdata+'dt.pickle'
f = open(picklefilename+fn,'w')
pickle.dump(dt,f)
f.close()


print "Start time:",datetime.datetime.fromtimestamp(EventTime_Unix).strftime('%Y-%m-%dT%H:%M:%S')
print "End time:",datetime.datetime.fromtimestamp(EventTime_Unix+dt*len(t)).strftime('%Y-%m-%dT%H:%M:%S')

for i in range(len(t)):
    #timestring = datetime.datetime.fromtimestamp(EventTime_Unix+1).strftime('%Y-%m-%dT%H:%M:%S')
    time = EventTime_Unix+i*dt
    hexbx = float2hex(vector[i,0])
    hexby = float2hex(vector[i,1])
    hexbz = float2hex(vector[i,2])
    time1 = integer2hex(time)
    time2 = integer2hex(floatbit(time)*1e9)
    data = [(r[i]<<4)+14,16,128+(1&7),1,
            time1[0],time1[1],time1[2],time1[3],
            time2[0],time2[1],time2[2],time2[3]]  
    #testing only
    #if i<15:
        #value = [204, 76, 200, 69] #100.15
    #else:
        #value = [204, 76, 72, 70]#200.3
    '''
    value = float2hex(1000.15)
    hexbx = value
    hexby = value
    hexbz = value
    '''
    
    data.extend(hexbx)
    data.extend(hexby)
    data.extend(hexbz)
    data.extend([0,0,0,0,0,0,0,0])
    for content in data:
        datahandle.write(chr(content))	
datahandle.close()

#tmp = '/home/ahk114/testdata/ExtProcRaw_1'

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
		
print ""
print "executing:",cmd
print ""	
os.system(cmd)
print ""
print "Finished Executing"
print ""
print "dt:",dt," sine:",sin," length:",t.shape[0]
#output = subprocess.check_output(cmd,shell=True)
#output = subprocess.Popen(cmd,stdout=subprocess.PIPE).communicate()[0]
#output = subprocess.Popen(cmd)