import numpy as np
#from math import pi
import matplotlib.pyplot as plt
plt.close('all')
f,axarr = plt.subplots(1,figsize=(20,15))
#import time
reset = 5.152
#spin = 4.260732 #Rumba
#spin = 4.168264 #Salsa
#spin =4.210481 #Samba
#spin =4.134934 #Tango

spins=[4.260732,4.168264,4.210481,4.134934]



def func(spin,widthreset=0.08):
    widthspin=spin

    maxi = 415
    #off = np.random.random()*spin
    #print "offset:", off
    x = np.linspace(0,maxi,num=maxi*100)+1.1
    
    #start = time.time()
    #print "Start time:",start
    
    def squarereset(x):
        y = []
        lim = int((max(x)/reset+1))
        #lim = 200
        for s in x:
            for n in range(lim):
                if (reset*n)-widthreset/2. < s < (reset*n)+widthreset/2.:
                    y.append(1)
                    break
                else:
                    if n==lim-1:
                        y.append(0)
        return y
        
    def spinreset(x):
        y = []
        lim = 200
        for s in x:
            for n in range(lim):
                if (spin*n)-widthspin/2 < s < (spin*n)+widthspin/2:
                    y.append(1)
                    break
                else:
                    if n==lim-1:
                        y.append(0)
        return y    
    #print squarereset(x)
    def mean(x,y,interval):
        
        xs = []
        ys = []
        xmeans = []
        ymeans = []
        max_n = int(max(x)/interval) +1
        #print "maxn:", max_n
        for n in range(max_n):
            for i,j in zip(x,y):
                #print i,j
                if interval*n < i < interval*(n+1):
                    #print "2"
                    #print i,j
                    xs.append(i)
                    ys.append(j)
    
            xmeans.append(np.mean(xs))
            ymeans.append(np.mean(ys))
            xs = []
            ys = []   
            
        #n = int(interval/((max(x)-min(x))/len(x)))
        n=415
        print "n:",n,len(x)
        newx = np.asarray(x)
        print len(newx),type(newx)
        newx = newx.reshape(-1,n)
        newxmean = np.mean(newx,axis=1)
        newy = np.asarray(y)
        newy = newy.reshape(-1,n)
        newymean = np.mean(newy,axis=1)
        for a,b,c,d in zip(xmeans,newxmean,ymeans,newymean):
            print a,b,c,d
        return xmeans,ymeans
        
    '''
    axarr[0].scatter(x,squarereset(x))
    #axarr[1].scatter(x,spinreset(x))
    '''
    
    x,y=mean(x,squarereset(x),spin)
    '''
    #print x
    axarr[1].scatter(x,y,c='r',s=300)
    
    for ax in axarr:
        ax.set_ylim((-0.2,1.2))
        ax.set_xlim((-0.2,maxi+0.2))
    axarr[1].set_ylim((-0.05*max(y),1.1*max(y)))
    '''
    
    x_low = []
    for i,j in zip(x,y):
        if j < np.mean(y):
            x_low.append(i)
    print "                           spin:",spin
    print "                     widthreset:",widthreset
    print "product of spin and reset times:", reset*spin
    print "  mean separation of low points:", (max(x_low)-min(x_low))/len(x_low)
    print "                     difference:", reset*spin-(max(x_low)-min(x_low))/len(x_low)
    axarr.scatter(spin,reset*spin-(max(x_low)-min(x_low))/len(x_low))
    '''
    end = time.time()
    print "Duration time:",end-start
    '''
    
for spin in spins:
    func(spin)