import pandas as pd
import numpy as np
from lin_interpolate import interpolate
import matplotlib.pyplot as plt
import data_analysis as da
from numba import jit
from datetime import datetime,timedelta

@jit(nopython=True)
def search_array(diffs,target_diff,start_i):
    prev = 0
    current = 0
    arr = diffs-target_diff
    if start_i==0:
        i=1
    else:
        i=start_i
    while(i<arr.shape[0]-1):
        prev = arr[i-1]
        current = arr[i]
        if current>0:
            if abs(prev)<abs(current):
                return i-1
            else:
                return i
        i+=1
    return i

@jit(nopython=True)
def sample_new(times,values,diffs,sample_number,timestep):
    new_times = np.empty(sample_number,dtype=times.dtype)
    new_values = np.empty(sample_number,dtype=values.dtype)
    last_ind = 0
    for i in range(sample_number):
        target_diff = i*timestep
        last_ind = search_array(diffs,target_diff,last_ind)
        new_times[i]=times[last_ind]
        new_values[i]=values[last_ind]
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
    new_times,new_values = sample_new(times,values,diffs,sample_number,timestep)
    return pd.DataFrame(new_values,index=new_times)
    
def resample_frames(df1,df2,time_sampling=0.15,factor=100):
    '''
    sampling in seconds!!
    '''
    df1_start = df1.index.values[0]
    df2_start = df2.index.values[0]
    df1_end = df1.index.values[-1]
    df2_end = df2.index.values[-1]
    last_start = np.sort([df1_start,df2_start])[1]
    first_end = np.sort([df1_end,df2_end])[0]
    '''
    print df1.head()
    print df2.head()
    '''
    df1 = interpolate(df1,factor=factor)
    df2 = interpolate(df2,factor=factor)
    df1 = df1[df1.index>=last_start]
    df2 = df2[df2.index>=last_start]
    '''
    print df1.head()
    print df2.head()
    '''
    df3 = find_nearest(df1,time_sampling,last_start)
    df4 = find_nearest(df2,time_sampling,last_start)
    df3 = df3[(df3.index>=last_start) & (df3.index<=first_end)]
    df4 = df4[(df4.index>=last_start) & (df4.index<=first_end)]
    '''
    print df3.head()
    print df4.head()
    '''
    '''
    convert them to the same timebase - just illustrative, really (eg. for graphs)
    just to see qualitively what the effect of this would be
    '''
    length_df3 = df3.shape[0]
    length_df4 = df4.shape[0]
    shortest_length = np.sort([length_df3,length_df4])[0]
    df3 = df3.iloc[:shortest_length]
    df4 = df4.iloc[:shortest_length]
    new_index = pd.date_range(start=last_start,periods=shortest_length,
                              freq=timedelta(seconds=time_sampling))
    df3.index = new_index
    df4.index = new_index
    return df3,df4
'''
n=3
df = pd.DataFrame(np.random.randn(n),index=pd.date_range('2009',periods=n,freq='4.2s'))
'''
start = datetime(2007,11,30,19,35)
end   = datetime(2007,11,30,20,14)
extsc  = 3
normsc = 2
df_ext = da.return_ext_data(extsc,start,end,source='caa')[['mag']]
df_norm = da.return_normal_data(normsc,start,end,source='caa')[['mag']]

#df_ext=df_ext.iloc[:100]
#df_norm =df_norm.iloc[:100]

plt.close('all')
plt.ion()
plt.figure()
plt.plot_date(df_ext.index.values,df_ext.ix[:,0],label='ext',c='r',fmt='-')
plt.plot_date(df_norm.index.values,df_norm.ix[:,0],label='normal',c='g',fmt='-')
plt.title('Before')
plt.legend()

time_sampling = 0.1
factor=10
df_ext_new,df_norm_new=resample_frames(df_ext,df_norm,time_sampling=time_sampling,
                                       factor=factor)

plt.figure()
plt.plot_date(df_ext_new.index.values,df_ext_new.ix[:,0],label='ext',c='r',fmt='-')
plt.plot_date(df_norm_new.index.values,df_norm_new.ix[:,0],label='normal',c='g',fmt='-')
plt.title('After')
plt.legend()

corr = np.correlate(df_norm_new.ix[:,0].values,df_ext_new.ix[:,0].values,"full")

shifts = pd.DataFrame({'shift steps':np.arange(-(df_ext_new.shape[0]-1),df_ext_new.shape[0]),
                       'xcorr':corr})
shifts['seconds'] = shifts['shift steps']*time_sampling
shifts = shifts[['seconds','xcorr']]
s_shifts = shifts.set_index('seconds')
s_shifts.plot()