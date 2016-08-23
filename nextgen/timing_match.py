import timing_end as te
import timing_start as ts
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import RawData

def estimate_spin_reset(sc,ext_date,dir='Z:/data/raw/'):
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
    return spin_period,reset_period
    
RAW = 'C:/Users/ahfku/Documents/Magnetometer/clusterdata/'#home pc
#RAW = 'Z:/data/raw/' #cluster alsvid server

'''
load previously processed ext mode data!
'''
import cPickle as pickle
pickledir = 'C:/Users/ahfku/Documents/Magnetometer/clusterdata/'#home pc
#pickledir = 'Y:/testdata/'
picklefile = pickledir+'extdata.pickle'
with open(picklefile,'rb') as f:
    combined_data = pickle.load(f)

'''
#estimate from real packet data - quite slow
spin_period,reset_period = estimate_spin_reset(sc=1,
                                    ext_date=datetime(2016,1,4),dir=RAW)
print "spin period:",spin_period
print "reset period:",reset_period
'''

'''
define spin and reset period, as well as initial packet conditions
'''
spin_period = 4.2607927059690756
reset_period = 5.1522209199771503 
spin = spin_period
reset = reset_period
spins = 14793
first_diff_HF = (34866-23540)
initial_reset = 58028
time = spins*spin

final_reset = 4729+2**16
final_first_diff_HF = (47677-44563)
real_resets = combined_data['reset'].values

SCET_time_diff = 63027.118545#time difference between initial and final packets

SCET_time_diff = 63047#this makes the series agree, as expected!

start_extrapolation = ts.extrapolate_timing(spin,reset,time,first_diff_HF,initial_reset)
end_extrapolation = te.extrapolate_timing_from_end(spin,reset,time,final_first_diff_HF,final_reset)
'''
results contain:
0 spin times
1 spin resets
2 seen spin resets
3 reset times
4 reset counter
'''

'''
Need to add SCET_time_diff to all of the end_extrapolation time series!!!
'''
time_index = 0
data_index = 2

plt.figure()
plt.title('Matching Beginning and End,before spin adjustment!')
plt.plot(start_extrapolation[time_index],start_extrapolation[data_index],c='r',label='seen from start')
plt.plot(end_extrapolation[time_index]+SCET_time_diff,end_extrapolation[data_index],c='g',label='seen from end')
plt.legend(loc='best')
plt.show()

'''
Estimate a new spin time from comparison to extrapolation - offset needs to
be known before this!
'''
offset_start = ts.find_offset_initial(spin_period,reset_period,real_resets,
                                      first_diff_HF,initial_reset,time)
offset_end = te.find_offset_from_end(spin_period,reset_period,real_resets,
                                     final_first_diff_HF,final_reset,time)
print "start offset:", offset_start," end offset:", offset_end     

start_spin = ts.optimise_spin(spin_period,reset_period,time,first_diff_HF,
                              initial_reset,real_resets,offset_start)
end_spin = te.optimise_spin(spin_period,reset_period,time,final_first_diff_HF,
                            final_reset,real_resets,offset_end)

spin_estimates = pd.DataFrame(np.array([start_spin,end_spin]).reshape(-1,2),columns=['start','end'],index=[0])
spin_estimates['diff'] = spin_estimates['start']-spin_estimates['end']
spin_estimates['mean'] = np.mean([start_spin,end_spin])
spin_estimates['orig'] = spin_period
spin_estimates = spin_estimates[['orig','start','end','diff','mean']]
spin_estimates['diff to orig']=spin_estimates['orig']-spin_estimates['mean']
print spin_estimates            

'''
Repeat above with improved spin times!!!
'''
spin_estimate=spin_estimates['mean'].values[0]
start_extrapolation = ts.extrapolate_timing(spin_estimate,reset,time,first_diff_HF,initial_reset)
end_extrapolation = te.extrapolate_timing_from_end(spin_estimate,reset,time,final_first_diff_HF,final_reset)  

plt.figure()
plt.title('Matching Beginning and End,after spin adjustment!')
plt.plot(start_extrapolation[time_index],start_extrapolation[data_index],c='r',label='seen from start')
plt.plot(end_extrapolation[time_index]+SCET_time_diff,end_extrapolation[data_index],c='g',label='seen from end')
plt.legend(loc='best')
plt.show()              