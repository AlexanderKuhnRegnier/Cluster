import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import RawData
from datetime import datetime
from numba import jit

@jit
def extrapolate_timing(spin_period,reset_period,time,
                       first_diff_HF,initial_reset):
    '''
    Times in seconds, unless otherwise stated. HF clock freq is 4096 Hz.
    The first difference refers to the time between the most recent sun pulse
    and the packet time for a certain (usually NS) packet before the extended
    mode starts.
    '''
    if first_diff_HF<0:
        first_diff_HF += 2**16
    first_diff_time = first_diff_HF/4096.

    '''
    The index of the timing extrapolation is going to be a spin, so every
    spin period for the time period specified. Using the first difference 
    provided, the remaining pattern can be calculated, assuming that
    reset period and spin period do not drift too much, which should not be
    the case in a couple of hours (unless there is a maneouvre).
    Either way, the spin period should be obtained by averaging spin periods
    before, on and after extended mode, so even this should be considered 
    somehow.
    
    First spin is at time 0, the first reset is 'first_diff_' afterwards.    
    '''
    spin_times = np.arange(0,time,spin_period)
    reset_times = np.arange(first_diff_time-reset_period,time,reset_period)
    reset_counter = np.arange(initial_reset-1,
                              initial_reset+reset_times.shape[0]-1,1)
    '''
    -1 in the end value, to compensate for the increased length of the
    reset times array, which has grown by 1 due to the subtraction of the
    reset period - which is done so that the 'first' reset occurs before
    the first spin, so that we have a reset counter value for that.
    '''
    '''
    but in extended, mode, only the top 12 bits of the reset counter is 
    registered, so this measure only increases every 16 reset counts.
    '''    
    if reset_counter[0]<0:
        reset_counter[0]+=2**16
    #seen_resets = reset_counter>>4
    spin_resets = np.empty(np.shape(spin_times),dtype=np.int64)
    i=0
    index = 0
    for spin_time in spin_times:
        if spin_time>reset_times[i+1]:
            i+=1
        spin_resets[index]=reset_counter[i]
        index+=1
    seen_spin_resets = spin_resets>>4
    return spin_times,spin_resets,seen_spin_resets,reset_times,reset_counter
            
'''
ext_date = datetime(2016,1,4) #tbd
sc = 1
RAW = 'C:/Users/ahfku/Documents/Magnetometer/clusterdata/'#home pc
day_delta = pd.Timedelta('1 day')
dates=[ext_date-day_delta, ext_date, ext_date+day_delta]
modes= ['NS','BS']
spin_periods = []
reset_periods = []
for date in dates:
    for mode in modes:
        packetdata = RawData.RawDataHeader(sc,date,mode,dir=RAW).packet_info
        spin_periods.append(packetdata['Spin Period (s)'].mean())
        reset_periods.append(packetdata['Reset Period (s)'].mean())
                            
spin_period = np.mean(spin_periods)
reset_period = np.mean(reset_periods)
print "spin period:",spin_period
print "reset period:",reset_period    
'''  
spin_period = 4.2607927059690756
reset_period = 5.1522209199771503 

spin = spin_period
reset = reset_period
spins = 10000
first_diff_HF = (34866-23540)
initial_reset = 58028
time = spins*spin

spins = extrapolate_timing(spin_period=spin,reset_period=reset,time=time,
                   first_diff_HF=first_diff_HF,initial_reset=initial_reset)


f = plt.figure() 
#ax = f.add_subplot(111)           
plt.plot(spins[0],spins[2],c='b',label='simulated')

plt.scatter(spins[0],spins[1]/16.,c='g',label='real spin resets',s=100)
plt.scatter(spins[3],spins[4]/16.,c='k',label='actual resets',s=100)
#plt.figure()
#spins.groupby('reset').size().plot(title='number of vectors at reset',c='b')
#print spins.groupby('reset').size().mean()
#print spins.groupby('reset').size().std()


'''
aim for
mean: 19.304177545691907
std:  0.8797850538542629
'''

import cPickle as pickle
pickledir = 'C:/Users/ahfku/Documents/Magnetometer/clusterdata/'#home pc
picklefile = pickledir+'extdata.pickle'
with open(picklefile,'rb') as f:
    combined_data = pickle.load(f)

combined_data['time'] = spin_period*np.arange(0,combined_data.shape[0],1)

plt.plot(combined_data['time']+2*spin_period,combined_data['reset'],c='r',
         label='real, time+2 spins')
plt.title('seen reset')
plt.legend()
plt.show()
