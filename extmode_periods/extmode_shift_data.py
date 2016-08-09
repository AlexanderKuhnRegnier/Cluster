import pandas as pd
import numpy as np
import cPickle as pickle
import os
import matplotlib.pyplot as plt
import itertools
#plt.style.use('seaborn-darkgrid')
plt.close('all')
import data_analysis as da
import PyPDF2 as pdf
results_root = 'Y:/overlap_stats/results_'
pickledir = 'Y:/overlap_stats/'
imagedir=pickledir+'images/'
data_file = 'overlap_stats.pickle'
shift_data = 'shift_data.pickle'

pd.set_option('expand_frame_repr',False)
pd.set_option('precision',4)
pd.set_option('max_rows',30)

def vector_data(series):
    results = {}
    results['ext_mode'] = da.return_ext_data(series.ext_sc,series.start,
                                                            series.end)
    results['non_ext_mode'] = da.return_normal_data(series.non_ext_sc,series.start,
                                                            series.end)
    return results   

def initial_processing(min_hours=1):
    if os.path.isfile(pickledir+data_file):
        with open(pickledir+data_file,'rb') as f:
            overlap_data = pickle.load(f)
    else:
        raise Exception("Original Data not Found!")
    '''
    
    '''
    overlap_data['duration']*=(1/3600.)
    overlap_data.rename(columns={'duration':'duration (h)'},inplace=True)

    filtered_duration = overlap_data[overlap_data['duration (h)']>min_hours]
    std_sorted = filtered_duration.sort_values('std',ascending=True)
    single_days = std_sorted.groupby(std_sorted.start.dt.date).first()
    single_days = single_days[['start','end','ext_sc','non_ext_sc']]
    return single_days
    '''
    get caa field stats and position stats using data_analysis
    '''
    '''
    with open(pickledir+shift_data,'wb') as f:
         pickle.dump(overlap_data,f,protocol=2)
    '''  
single_days = initial_processing()