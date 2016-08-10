import pandas as pd
import numpy as np
from lin_interpolate import interpolate
from numba import jit

'''
doesn't work since argsort isn't implemented
'''
@jit(nopython=True)
def numba_func(times,values,diffs,sample_number,timestep):
    new_times = np.empty(sample_number,dtype=times.dtype)
    new_values = np.empty(sample_number,dtype=values.dtype)
    for i in range(sample_number):
        target_diff = i*timestep
        index = np.abs(diffs-target_diff).argsort()[0]
        new_times[i]=times[index]
        new_values[i]=values[index]
    return new_times,new_values

def find_nearest(df,timestep,start):
    '''
    work in ns
    '''
    times = df.index.values
    values = df.ix[:,0].values
    diffs = (times-start)/np.timedelta64(1,'ns')
    mask = diffs>=0
    times = times[mask]
    diffs = diffs[mask]
    timestep *= 1e9 #convert to ns
    sample_number = int(diffs[-1]/timestep)+1
    new_times,new_values = numba_func(times,values,diffs,sample_number,timestep)
    return pd.DataFrame(new_values,index=new_times)
    
def xcorr_frames(df1,df2,time_sampling=0.15,factor=100):
    '''
    sampling in seconds!!
    '''
    start = np.sort([df1.index.values[0],
                       df2.index.values[0]])[0]
    df1 = interpolate(df1,factor=factor)
    df2 = interpolate(df2,factor=factor)
    
    df3 = find_nearest(df1,time_sampling,start)
    df4 = find_nearest(df2,time_sampling,start)
    return df3,df4
'''
n=1000
df = pd.DataFrame(np.random.randn(n),index=pd.date_range('2009',periods=n,freq='4.2s'))

df3,df4=xcorr_frames(df,df,time_sampling=0.1,factor=10)
'''