import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from numba import jit,float64,int32
import data_analysis as da

def upsample_frame_wrapper_jit(frame,factor=10):
    times = frame.index.values
    values = frame.ix[:,0].values
    times_result = upsample_frame_jit_times(times,factor=factor)
    data_result = upsample_frame_jit_values(values,factor=factor)
    new = pd.DataFrame(data_result,index=times_result)
    return new

@jit(nopython=True)    
def numba_func(input,steps,factor):
    new = np.empty((input.shape[0])*factor+1,dtype=input.dtype)
    for i in range(input.shape[0]):
        start = input[i]     
        step = steps[i]
        for j in range(factor):
            new[j+i*factor] = start+j*step
    return new

def upsample_frame_jit_times(times,factor=10):
    factor_f = float(factor)
    start_times = times[:-1]
    end_times = times[1:]
    deltas = (end_times-start_times)/np.timedelta64(1,'us')
    timesteps = (deltas/factor_f)*np.timedelta64(1,'us')
    new = numba_func(start_times,timesteps,factor)
    new[-1] = times[-1]
    return new
    
def upsample_frame_jit_values(values,factor=10):
    factor_f = float(factor)
    start_values = values[:-1]
    end_values = values[1:]
    gradients = end_values-start_values
    datasteps = gradients/factor_f
    new = numba_func(start_values,datasteps,factor)    
    new[-1] = values[-1]
    return new
    
def interpolate(df,factor=10):
    assert df.columns.shape[0]==1,"1 datetime index and one data column!"
    upsampled = upsample_frame_wrapper_jit(df,factor=factor)
    return upsampled 