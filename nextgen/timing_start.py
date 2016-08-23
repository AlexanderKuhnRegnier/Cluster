import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import RawData
from datetime import datetime
from numba import jit
import numba as nb
from scipy.optimize import minimize

@jit(nopython=True)
def numba_func(spin_times,reset_times,reset_counter):
    spin_resets = np.empty(spin_times.shape,dtype=np.int64)
    i=0
    index = 0
    for spin_time in spin_times:
        if spin_time>reset_times[i+1]:
            i+=1
        spin_resets[index]=reset_counter[i]
        index+=1
    seen_spin_resets = spin_resets>>4
    return spin_resets,seen_spin_resets
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

    spin_resets,seen_spin_resets = numba_func(spin_times,reset_times,
                                              reset_counter)
    return spin_times,spin_resets,seen_spin_resets,reset_times,reset_counter

def compare_real_to_sim(spin_period,reset_period,time,
                   first_diff_HF,initial_reset,combined_data,offset=2):
    '''
    Graphically compare the 'simulated' extrapolated series of resets,
    computed from the given parameters, to the real_resets
    (combined_data['reset']) that were read from the BS file.
    '''                                              
    spins = extrapolate_timing(spin_period,reset_period,time,
                       first_diff_HF=first_diff_HF,initial_reset=initial_reset)
    plt.figure() 
    #ax = f.add_subplot(111)           
    plt.plot(spins[0],spins[2],c='b',label='simulated')
    plt.scatter(spins[0],spins[2],c='b',label='simulated',s=30)
    plt.scatter(spins[0],spins[1]/16.,c='g',label='spin resets',s=100)
    plt.scatter(spins[3],spins[4]/16.,c='k',label='simulated resets',s=100)
    #plt.figure()
    #spins.groupby('reset').size().plot(title='number of vectors at reset',c='b')
    #print spins.groupby('reset').size().mean()
    #print spins.groupby('reset').size().std()
    combined_data['time'] = spin_period*np.arange(0,combined_data.shape[0],1)
    plt.plot(combined_data['time']+offset*spin_period,
             combined_data['reset'],c='r',label='real, time+2 spins')
    plt.scatter(combined_data['time']+offset*spin_period,
                combined_data['reset'],c='r',label='real, time+2 spins',s=30)
    plt.title('seen reset')
    plt.legend()
    plt.show()


def plotboth(a,b):
    plt.figure()
    plt.plot(range(len(a)),a,c='b',label='real')
    plt.scatter(range(len(a)),a,c='b',label='real',s=40)
    plt.plot(range(len(b)),b,c='r',label='simulated')
    plt.scatter(range(len(b)),b,c='r',label='simulated',s=40)
    plt.legend()
    plt.show()

def plotboth_advanced(a_times,a,b_times,b,title=''):
    plt.figure()
    plt.plot(a_times,a,c='b',label='real')
    plt.scatter(a_times,a,c='b',label='real',s=40)
    plt.plot(b_times,b,c='r',label='simulated')
    plt.scatter(b_times,b,c='r',label='simulated',s=40)
    plt.title(title)
    plt.legend()
    plt.show()

def target_func(offset,spin_period,reset_period,real_resets,first_diff_HF,
                initial_reset,time):
    '''
    For the given initial paramters that have been determined from a packet
    before extended mode (first_diff_HF,initial_reset), and those
    that were estimated either before, or are currently being estimated
    (offset,spin_period,reset_period) (time - extended mode time period),
    a simulated series of reset values analogous to those actually observed
    (fed in via real_resets) is created, and compared to the real reset values.
    The element-wise difference squared between the two series is returned.
    This is used in order to determine the parameters that let the simulated,
    ie. extrapolated time series match the actual data as well as possible.
    '''                        
    offset = int(round(offset))
    simulated_resets = extrapolate_timing(spin_period,reset_period,time,
                                          first_diff_HF,initial_reset)[2]
    if offset>0:
        simulated_resets = simulated_resets[offset:]
    else:
        offset = abs(offset)
        real_resets = real_resets[offset:]
    min_length = np.min((simulated_resets.shape[0],real_resets.shape[0]))
    if min_length<100:
        return np.inf
    simulated_resets = simulated_resets[:min_length]
    real_resets = real_resets[:min_length]
    diffs = simulated_resets - real_resets
    diffs_2 = np.square(diffs)
    #diffs_2_sum = np.sum(diffs_2)/float(min_length)
    diffs_2_sum = np.sum(diffs_2)
    return diffs_2_sum

def target_func_reset(reset_period,spin_period,offset,real_resets,first_diff_HF,
                initial_reset,time):
    '''
    Wrapper for target_func so that reset_period is the first arg
    '''                    
    return target_func(offset,spin_period,reset_period,real_resets,
                       first_diff_HF,initial_reset,time)    
def target_func_offset(offset,spin_period,reset_period,real_resets,first_diff_HF,
                initial_reset,time):
    '''
    Wrapper for target_func so that offset is the first arg
    '''                    
    return target_func(offset,spin_period,reset_period,real_resets,
                       first_diff_HF,initial_reset,time)       
def target_func_spin(spin_period,offset,reset_period,real_resets,first_diff_HF,
                initial_reset,time):
    '''
    Wrapper for target_func so that spin_period is the first arg
    '''                                
    return target_func(offset,spin_period,reset_period,real_resets,
                       first_diff_HF,initial_reset,time)       

def find_offset_initial(spin_period,reset_period,real_resets,first_diff_HF,
                initial_reset,time):
    '''
    Determine the offset between the data extrapolated ('simulated') from
    a packet before extended mode and the real data that is fed in via
    real_resets.
    '''                    
    results = []
    real_resets = real_resets[:200]
    offsets = np.arange(-100,real_resets.shape[0],1)
    step = int(round(offsets.shape[0]/100))
    offsets = offsets[::step]
    target_func_offset_local = target_func_offset
    for offset in offsets:
        results.append(target_func_offset_local(offset,spin_period,
                    reset_period,real_resets,first_diff_HF,initial_reset,time))   
    '''        
    simulated_resets = extrapolate_timing(spin_period,reset_period,time,
                                          first_diff_HF,initial_reset)[2] 
    plotboth(real_resets,simulated_resets[:20])
    fig,axes = plt.subplots(1,2)
    axes[0].plot(offsets,results)
    axes[0].set_title('before')
    '''
    '''
    now exand around the minimum, +- step
    '''
    minimum_index = np.where(results==np.min(results))
    min_offset = offsets[minimum_index]
    if min_offset.shape[0]>1:
        raise Exception("There should only be 1 minimum offset!")
    offsets = np.arange(-step,step+1,1)+min_offset
    results = []
    for offset in offsets:
        results.append(target_func_offset_local(offset,spin_period,
                    reset_period,real_resets,first_diff_HF,initial_reset,time))                      
    minimum_index = np.where(results==np.min(results))
    min_offset = offsets[minimum_index]
    '''
    axes[1].plot(offsets,results)                              
    axes[1].set_title('after')
    axes[1].scatter(min_offset,np.min(results))
    '''
    assert min_offset.shape[0] == 1,"should only have 1 result!"
    return min_offset[0]
 
def optimise_spin(original_spin_period,reset_period,time,first_diff_HF,initial_reset,
                  real_resets,best_offset):
    '''
    Takes a spin period estimate, and returns an improved estimate of the 
    spin period, based on the assumption that the reset period is constant,
    and that the offset has been ideally determined.
    '''
    result = minimize(target_func_spin,original_spin_period,method='Nelder-Mead',
                      tol=1e-10,
                      args=(best_offset,reset_period,real_resets,first_diff_HF,
                    initial_reset,time))
    best_spin = result.x[0]    
    return best_spin                       
'''
compare_real_to_sim(spin_period,reset_period,time,first_diff_HF,initial_reset,
                    combined_data,offset=2)
'''

'''
#kind of unreliable to find offset with
result = minimize(target_func_offset,1000,method='Nelder-Mead',tol=1e-10,
                  args=(spin_period,reset_period,combined_data['reset'][:],
                        first_diff_HF,initial_reset,time,False))
'''

'''
#usage examples!!       
min_offset = find_offset_initial(spin_period,reset_period,combined_data,first_diff_HF,
                initial_reset,time)
                
print "optimal offset:",min_offset               
result = minimize(target_func_spin,4,method='Nelder-Mead',tol=1e-10,
                  args=(min_offset,reset_period,combined_data['reset'].values,first_diff_HF,
                initial_reset,time))
print "Spin Optimisation"
#print result 
best_spin = result.x[0]
print best_spin
print "diff:",format((best_spin-spin_period),'0.3e')
print target_func_spin(best_spin,min_offset,reset_period,combined_data['reset'].values,
                       first_diff_HF,initial_reset,time)
print "before:",spin_period,"value:",     
print target_func_spin(spin_period,min_offset,reset_period,combined_data['reset'].values,
                       first_diff_HF,initial_reset,time)
                       

result = minimize(target_func_reset,5.1522,method='Nelder-Mead',tol=1e-30,
                  args=(best_spin,min_offset,combined_data['reset'].values,
                        first_diff_HF,initial_reset,time))
print "\nReset Optimisation"
print result 

print "before:",reset_period,"value:",     
print target_func_reset(reset_period,best_spin,min_offset,combined_data['reset'].values,
                        first_diff_HF,initial_reset,time)
                       
'''
'''                    
print "\nOnly Reset no Spin Optimisation"

This and the reset optimisation above are pretty much just for reference,
since we are only interested in the spin period, since that is what will
give the vectors their time-stamp in the end. Plus, the reset period
is bound to not vary very much anyway - so it is more likely that the 
spin period has changed slightly, as opposed to the reset, even though
both are theoretically possible, the former is more important in this case.
The end time of the extended mode interval will also have to be considered
here, since the vectors obviously cannot overlap!!
'''
'''
result = minimize(target_func_reset,5.1522,method='Nelder-Mead',tol=1e-16,
                  args=(spin_period,min_offset,combined_data['reset'].values,
                        first_diff_HF,initial_reset,time),bounds=(5.151,5.154))

print result 

print "before:",reset_period,"value:",     
print target_func_reset(reset_period,spin_period,min_offset,combined_data['reset'].values,
                        first_diff_HF,initial_reset,time)
'''