import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
def extrapolate_timing(spin_period=False,reset_period=False,time=False,
                       spins=False,resets=False,first_diff_HF=False,
                       first_diff_time=False,initial_reset=False
                       ):
    '''
    All args as kwargs, just to be extra explicit
    Times in seconds, unless otherwise stated. HF clock freq is 4096 Hz.
    The first difference refers to the time between the most recent sun pulse
    and the packet time for a certain (usually NS) packet before the extended
    mode starts.
    '''
    if time:
        time=time
    elif spins:
        time=spins*spin_period
    elif resets:
        time=resets*spin_period
    else:
        raise Exception("Need to provide either time, spins or resets!")
    if first_diff_time:
        first_diff_time=first_diff_time
    elif first_diff_HF:
        if first_diff_HF<0:
            first_diff_HF += 2**16
        first_diff_time = first_diff_HF/4096.
    else:
        raise Exception("Need a first diff, either first_diff_time or "
                        "first_diff_HF!")
    if not spin_period or not reset_period:
        raise Exception("Need both spin_period and reset_period in seconds!")
    if not initial_reset:
        raise Exception("Need initial reset counter value!")
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
    resets = pd.DataFrame({'time':reset_times,
                           'real':reset_counter})
    resets['real'] = resets['real'].apply(lambda x:x+2**16 if x<0 else x)
    resets['seen'] = resets['real'].apply(lambda x:x>>4)
    spins = pd.DataFrame({'time':spin_times})
    spins['reset'] = spins['time'].apply(lambda x:max(resets[resets['time']<=x]['seen']))
    spins.index.name='vector'
    return spins    
    
spin = 4.260667134634775
reset = 5.152220843827191
spins = 14787
first_diff_HF = (58195-40172)
initial_reset = 58028
spins = extrapolate_timing(spin_period=spin,reset_period=reset,spins=spins,
                   first_diff_HF=first_diff_HF,initial_reset=initial_reset)
                   
#spins.plot(x='time',y='reset',title='observed reset with time')
#plt.figure()
#spins.groupby('reset').size().plot(title='number of vectors at reset')
print spins.groupby('reset').size().mean()
print spins.groupby('reset').size().std()

'''
aim for
mean: 19.304177545691907
std:  0.8797850538542629
'''