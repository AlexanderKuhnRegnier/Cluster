import numpy as np
#import time
#from math import pi
import matplotlib.pyplot as plt


def func():
    global n,spin,reset,resetwidth,dt,axarr
    '''
    print n
    print spin
    print reset
    print resetwidth
    print dt
    print spin/dt
    print reset/dt
    print resetwidth/dt
    '''
    '''
    if (spin/dt != int(spin/dt)) or (reset/dt != int(reset/dt)) or (resetwidth/dt != int(resetwidth/dt)) :
        raise Exception("Choose appropriate spin,reset,resetwidth and dt values!")
    '''

    spindt = int(spin/dt)
    resetdt = int(reset/dt)
    resetwidthdt=int(resetwidth/dt)    
    size = n*spindt
    print "size:", size

    
    #start = time.time()
    #print "Start time:",start
    
    
    reset_array = np.array([],dtype=np.float64).reshape(-1,1)
    while(reset_array.shape[0]<size):
        reset_array = np.append(reset_array,np.zeros((resetdt-resetwidthdt,1)))
        reset_array = np.append(reset_array,np.ones((resetwidthdt,1)))
    
    if reset_array.shape[0]>size:
        reset_array = reset_array[:size]
    else:
        raise Exception("Something went wrong with reset array")
        
    y = reset_array
    print "length y:", len(y),y.shape
    y = np.asarray(y)
    y = np.mean(y.reshape(-1,spindt),axis=1)
    x = np.linspace(spin/2.,spin*n+spin/2.,num=n)
    if len(x) != len(y):
        raise Exception("Lengths don't match up",len(x),len(y))
    
    '''
    for i,j in zip(x,y):
        print i,j
    '''
    
    #plt.scatter(x,y,s=100)    

    
    x_low = []
    for i,j in zip(x,y):
        if j < np.mean(y):
            x_low.append(i)
    print "                           spin:",spin
    print "                     widthreset:",resetwidth
    print "product of spin and reset times:", reset*spin
    print "  mean separation of low points:", (max(x_low)-min(x_low))/len(x_low)
    print "                     difference:", reset*spin-(max(x_low)-min(x_low))/len(x_low)
    
    return x,y
    
    
    #end = time.time()
    #print "Duration time:",end-start
    
    

#plt.close('all')
f,axarr = plt.subplots(4,2)

'''
#eg.
axarr[0, 0].plot(x, y)
axarr[0, 0].set_title('Axis [0,0]')
axarr[0, 1].scatter(x, y)
axarr[0, 1].set_title('Axis [0,1]')
axarr[1, 0].plot(x, y ** 2)
axarr[1, 0].set_title('Axis [1,0]')
axarr[1, 1].scatter(x, y ** 2)
axarr[1, 1].set_title('Axis [1,1]')
'''
#import time
reset = 5.152

#spin = 4.260732 #Rumba
#spin = 4.168264 #Salsa
#spin =4.210481 #Samba
#spin =4.134934 #Tango
spin = 0
spins=[4.260732,4.168264,4.210481,4.134934]

spins = [float('{:.3f}'.format(spin)) for spin in spins]

n=2000
#spin=4.261
reset = 5.152
resetwidth = 0.085
dt = 0.001
#func()
'''
for spin in spins:
    func(spin,min_ns,axarr)
'''
f.suptitle('n:{0:04d} dt:{1:0.4f}'.format(n,dt),fontsize = 20)
count = range(len(spins))
for spin,row,c in zip(spins,axarr,count):
    x,y = func()
    print "max",max(x)
    row[0].scatter(x,y,s=100,c='r')
    row[0].set_title('spin:{:.4f}'.format(spin))
    row[0].set_xlim((-max(x)*0.01,max(x)*1.1))   
    freqs = np.fft.fftfreq(len(y),d=spin)[1:len(y)/2]
    row[1].scatter(freqs,np.abs(np.fft.fft(y)[1:len(y)/2]))
    row[1].set_title('FFT (excluding DC component)')
    row[1].set_xlim((-max(freqs)*0.01,max(freqs)*1.1))
    
    if c == count[-1]:
        row[0].set_xlabel('time (s)')
        row[1].set_xlabel('frequency (1/s)')
    