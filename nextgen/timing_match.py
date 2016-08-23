import timing_end as te
import timing_start as ts
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import RawData
from datetime import datetime

def estimate_spin_reset(sc,ext_date,dir='Z:/data/raw/'):
    day_delta = pd.Timedelta('1 day')
    dates=[ext_date-day_delta, ext_date, ext_date+day_delta]
    modes= ['NS','BS']
    spin_periods = []
    reset_periods = []
    for date in dates:
        for mode in modes:
            packetdata = RawData.RawDataHeader(sc,date,mode,dir=dir).packet_info
            spin_periods.append(packetdata['Spin Period (s)'].mean())
            reset_periods.append(packetdata['Reset Period (s)'].mean())
                                
    spin_period = np.mean(spin_periods)
    reset_period = np.mean(reset_periods)
    return spin_period,reset_period
    
#RAW = 'C:/Users/ahfku/Documents/Magnetometer/clusterdata/'#home pc
RAW = 'Z:/data/raw/' #cluster alsvid server

'''
load previously processed ext mode data!
'''
import cPickle as pickle
#pickledir = 'C:/Users/ahfku/Documents/Magnetometer/clusterdata/'#home pc
pickledir = 'Y:/testdata/'
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
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
'''
'''
#SC 1 parameters, for 2016/01/04
spin_period = 4.2607927059690756
reset_period = 5.1522209199771503 
spin = spin_period
reset = reset_period
spins = 14793+10
first_diff_HF = (34866-23540)
initial_reset = 58028
time = lambda spin:spins*spin
final_reset = 4729+2**16
final_first_diff_HF = (47677-44563)
real_resets = combined_data['reset'].values
SCET_time_diff = 63027.118545#time difference between initial and final packets
'''
'''
#SC 2 parameters, for 2016/01/04
spin_period  = 4.1682032682937651
reset_period = 5.1522152392407365
spin = spin_period
reset = reset_period
spins = 15114+10 #(+10 for good measure)
first_diff_HF = (39268-37901)
initial_reset = 52442
time = lambda spin:spins*spin
final_reset = 64677
final_first_diff_HF = (52079-38933)
real_resets = combined_data['reset'].values
SCET_time_diff = 63027.109034#time difference between initial and final packets
'''

#SC 3 parameters, for 2016/01/04
spin_period = 4.2104047062408361
reset_period = 5.1522212401212863
spin = spin_period
reset = reset_period
spins = 14965+10
first_diff_HF = (10016-2579)
initial_reset = 52437
initial_scet = pd.Timestamp('2016-01-04 04:59:47.042457')
time = lambda spin:spins*spin
final_reset = 64676
final_first_diff_HF = (65035-64899)
real_resets = combined_data['reset'].values
final_scet = pd.Timestamp('2016-01-04 22:30:24.468790')
SCET_time_diff = (final_scet-initial_scet)/pd.Timedelta(1,'s')
'''
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
'''
'''
above is the time difference between the PACKETS, but we are interested 
in the spin times, so we need to adjust for the fact that the spins
and packets do not happen at the same time.
For the extrapolation from the start, the spin at time 0 is the spin
immediately after the packet - subtracts from time diff (since negative)
For the extrapolation from the end, the spin at time 0 is the spin 
immediately before the packet - subtracts from time diff (since positive,
and being subtracted - it happened AFTER the spin of interest)
We can correct the SCET time by using the result of the extrapolation
below!!
'''
###############################################################################
#different corrections, depending on what is seen in the data, and also the
#SCET time vs. reset count discrepancy!!
#SCET_time_diff = 63037
#final_reset -= 3
###############################################################################
start_extrapolation = ts.extrapolate_timing(spin,reset,time(spin),first_diff_HF,initial_reset)
end_extrapolation = te.extrapolate_timing_from_end(spin,reset,time(spin),final_first_diff_HF,final_reset)
'''
results contain:
0 spin times
1 spin resets
2 seen spin resets
3 reset times
4 reset counter
'''

'''
Now correct the SCET time difference!
'''
start_correction = start_extrapolation[3][0] #needs to be added to diff!
end_correction = end_extrapolation[3][-1]    #needs to be subtracted from diff!
print "SCET time correction at start,end:", start_correction,end_correction
SCET_time_diff = SCET_time_diff+start_correction-end_correction
print "New SCET time diff between SPINS:",SCET_time_diff
'''
Need to add corrected SCET_time_diff to all of the end_extrapolation 
time series!!!
'''
'''
Just matching up the results above, ie. the extrapolated results from
the packets at the border of extended mode!!
'''
time_index = 0
data_index = 1


plt.figure()
plt.title('Matching Beginning and End Extrapolated data,before spin adjustment!')
plt.plot(start_extrapolation[time_index],start_extrapolation[data_index],c='r',label='seen from start')
plt.plot(end_extrapolation[time_index]+SCET_time_diff,end_extrapolation[data_index],c='g',label='seen from end')
plt.scatter(start_extrapolation[time_index],start_extrapolation[data_index],c='r',label='seen from start',s=30)
plt.scatter(end_extrapolation[time_index]+SCET_time_diff,end_extrapolation[data_index],c='g',label='seen from end',s=30)
plt.legend(loc='best')
plt.minorticks_on()
plt.xlabel('time (s)')
plt.show()


'''
Estimate a new spin time from comparison to extrapolation - offset needs to
be known before this!
'''
offset_start = ts.find_offset_initial(spin_period,reset_period,real_resets,
                                      first_diff_HF,initial_reset,time(spin))
offset_end = te.find_offset_from_end(spin_period,reset_period,real_resets,
                                     final_first_diff_HF,final_reset,time(spin))
print "start offset:", offset_start," end offset:", offset_end     

start_spin = ts.optimise_spin(spin_period,reset_period,time(spin),first_diff_HF,
                              initial_reset,real_resets,offset_start)
end_spin = te.optimise_spin(spin_period,reset_period,time(spin),final_first_diff_HF,
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
start_extrapolation = ts.extrapolate_timing(spin_estimate,reset,time(spin_estimate),first_diff_HF,initial_reset)
end_extrapolation = te.extrapolate_timing_from_end(spin_estimate,reset,time(spin_estimate),final_first_diff_HF,final_reset)  


plt.figure()
plt.title('Matching Beginning and End Extrapolated Data,after spin adjustment!')
plt.plot(start_extrapolation[time_index],start_extrapolation[data_index],c='r',label='seen from start')
plt.plot(end_extrapolation[time_index]+SCET_time_diff,end_extrapolation[data_index],c='g',label='seen from end')
plt.scatter(start_extrapolation[time_index],start_extrapolation[data_index],c='r',label='seen from start',s=30)
plt.scatter(end_extrapolation[time_index]+SCET_time_diff,end_extrapolation[data_index],c='g',label='seen from end',s=30)
plt.legend(loc='best')
plt.minorticks_on()
plt.xlabel('time (s)')
plt.show()              

'''
Now combined the above data with the real reset values
Need to determine offsets to the packets first, since the first/last spin
of the extended mode data is never going to occur at those packets directly.
'''


ts.compare_real_to_sim(spin_estimate,reset_period,time(spin_estimate),
                       first_diff_HF,initial_reset,combined_data,offset_start)
te.compare_real_to_sim_from_end(spin_estimate,reset_period,time(spin_estimate),
                        final_first_diff_HF,final_reset,combined_data,offset=offset_end)


start_spin_times = start_extrapolation[0]
start_seen_spin_resets = start_extrapolation[2]
end_spin_times = end_extrapolation[0]
end_seen_spin_resets = end_extrapolation[2]

real_spin_times = np.arange(0,combined_data.shape[0],1)*spin_estimate
real_seen_spin_resets = real_resets

'''
Offsets as determined above describe how much the REAL data has to be SHIFTED
in order to fit the data extrapolated from a known packet! So now, since we
are matching two simulated datasets to the real data, the simulated,
ie. extrapolated datasets will have to be shifted by the negative of their
respective inverse, ie. if the 'offset_start' (from a NS packet before 
ext mode) is +2, this extrapolation shall be shifted backwards by 
2 spins now.

We also need to add the time difference between the reference packets to
the end_spin_times, since we are taking the first spin to be at time 0
'''

'''
This is WRONG - the start and end extrapolation have to match up without
this shift!!! (given that the SCET time is corrected in order to give the
time difference between spins, not packets (this is done above))
By shifting it this way, you are basically 'creating' more spins for the
extended mode data to slot 'into' - whereas it should really just fit
neatly on top of the extrapolated reset counts!!!
start_spin_times = start_spin_times-(offset_start*spin_estimate)
end_spin_times = end_spin_times-(offset_end*spin_estimate)+SCET_time_diff
'''
end_spin_times += SCET_time_diff
'''
Now plot all of these things together on one graph!
'''
def plotting_all(times=[real_spin_times,start_spin_times,end_spin_times],
                 resets=[real_seen_spin_resets,start_seen_spin_resets,
                         end_seen_spin_resets],
                         steps=1):
    '''
    Plot extrapolated data from both ends against the real data,
    either all in one go if steps=1, or by typing n+Enter in the console
    vai raw_input in order to scroll through the different steps one at 
    a time.
    '''
    ext_start = times[0][0]
    ext_end = times[0][-1]
    diff = ext_end-ext_start
    print "EXT Mode Times:",ext_start,ext_end,diff
    plt.figure(figsize=(22,17))
    window_size = np.max((real_spin_times.shape[0],start_spin_times.shape[0],
                          end_spin_times.shape[0]))/steps
    plt.ion()                    
    for step in range(steps): 
        plt.cla()                     
        c='r'
        label='real data'
        plot_times = times[0][window_size*step:window_size*(step+1)]
        print "limits:",window_size*step,window_size*(step+1)
        plot_resets = resets[0][window_size*step:window_size*(step+1)]
        #times = real_spin_times
        #resets = real_seen_spin_resets
        plt.plot(plot_times,plot_resets,c=c,label=label,lw=3)
        plt.scatter(plot_times,plot_resets,c=c,label=label,s=30)
    

        if np.any(ext_start==plot_times):
            plt.scatter(times[0][0],resets[0][0],c=c,s=100)
        if np.any(ext_end==plot_times):
            plt.scatter(times[0][-1],resets[0][-1],c=c,s=100)
        
        c='g'
        label='extrapolated from start'
        plot_times = times[1][window_size*step:window_size*(step+1)]
        plot_resets = resets[1][window_size*step:window_size*(step+1)]
        #times = start_spin_times
        #resets = start_seen_spin_resets
        plt.plot(plot_times,plot_resets,c=c,label=label,ls='dashed',lw=3)
        plt.scatter(plot_times,plot_resets,c=c,label=label,s=30)
        
        c='b'
        label='extrapolated from end'
        plot_times = times[2][window_size*step:window_size*(step+1)]
        plot_resets = resets[2][window_size*step:window_size*(step+1)]    
        #times = end_spin_times
        #resets = end_seen_spin_resets
        plt.plot(plot_times,plot_resets,c=c,label=label,ls='dashed',lw=3)
        plt.scatter(plot_times,plot_resets,c=c,label=label,s=30)
        
        plt.title('Comparing all 3 datasets')
        plt.legend(loc='best')
        plt.xlabel('time (s)')
        plt.ylabel('seen reset (top 12-bits)')
        plt.minorticks_on()
        plt.draw()
        plt.pause(0.1)
        if steps!=1:
            n = raw_input('Next?')
            if n!='n':
                break
        else:
            break
       
plotting_all(steps=1)



'''
Now aim to find where the 4 extra resets (case:04/01/2016 sc1) may have
sneaked in, by plotting the number of vectors per reset value for the 
extrapolated time series as well as the real data
(the top 12-bits, that is) and seeing where they start to disagree

from packets surrounding extended mode, the spin period and reset were
estimated. These are redefined for convenience below, according to this method
(found using the function estimate_spin_reset)
'''
'''
#SC 1 parameters, for 2016/01/04
spin_period = 4.2607927059690756
reset_period = 5.1522209199771503
'''
'''
#SC 2 parameters, for 2016/01/04
spin_period  = 4.1682032682937651
reset_period = 5.1522152392407365
'''
'''
#SC 3 parameters, for 2016/01/04
spin_period = 4.2104047062408361
reset_period = 5.1522212401212863
'''
'''
Generate data, with the original spin and reset estimates above,
not the optimisations!!
'''
start_extrapolation = ts.extrapolate_timing(spin_period,reset_period,time(spin),first_diff_HF,initial_reset)
end_extrapolation = te.extrapolate_timing_from_end(spin_period,reset_period,time(spin),final_first_diff_HF,final_reset)
'''
results list contains:
0 spin times
1 spin resets
2 seen spin resets <<--- we want this, which is the top 12-bits of entry 1
3 reset times
4 reset counter
'''
start_resets = start_extrapolation[2]
end_resets = end_extrapolation[2]
possible_resets = np.unique(np.append(start_resets,end_resets))
'''
now for all of these resets, count the occurrences in the two extrapolations
as well as the real data!
'''

occurrences_real = []
occurrences_start = []
occurrences_end = []
for reset_value in possible_resets:
    occurrences_real.append(np.sum(real_resets==reset_value))
    occurrences_start.append(np.sum(start_resets==reset_value))
    occurrences_end.append(np.sum(end_resets==reset_value))
'''
now plot these three lists, and compare - maybe take the difference as well
'''
fig,axarr = plt.subplots(3,1,sharex=True)
s=50
axarr[0].scatter(possible_resets,occurrences_real,c='r',label='real data',s=s)
axarr[1].scatter(possible_resets,occurrences_start,c='g',label='start',s=s)
axarr[2].scatter(possible_resets,occurrences_end,c='b',label='end',s=s)
plt.minorticks_on()
plt.legend(loc='best')
plt.title('Number of spins per reset value (top 12 bits)')
plt.ylabel('ccurrences')
plt.xlabel('reset (top 12 bits)')
plt.show()

'''
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
SC 1 date: 2016/01/04 (dump date 2016/01/06) (4 resets extra from SCET/reset)
spin_period = 4.2607927059690756
reset_period = 5.1522209199771503
'Block' of 16 resets takes: 82.4355347196344 s
The MAX number of spins within that time period is
(82.43... / 4.2608....)+1 => 20.347464288546103 spins
(+1 because we are including the first spin, which, for the maximum
number of spins shown above, would happen pretty much at exactly the same
time as the first reset in the 16 reset 'block', or slightly after.
We are counting it because data is packaged every sun count, ie every
spin in ext mode, so that is when the reset is recorded (the top 12 bits
of it that is))
The number of vectors (or spins) per 16 reset 'block' (1 of these reset 
blocks is just seen as a constant reset in the extended mode data,
since in extended mode, only the top 12 bits are observed) was plotted for
the real data, and for the extrapolated data, as per the method above.
It was found that the real data displayed four anomalous 'blocks' of resets,
which only had 18 resets, as opposed to the 19 or 20 expected (19 is the 
minimum you would expect from the above spin and reset periods, and 20
is the maximum (actually 20.35, but you obviously don't detect a third
of a spin)). This is not seen in the extrapolated data, as this follows 
what is expected (and deterministic) - so it seems that during those four
occasions where only 18 spins per reset value occurred - an anomalous reset
event happened.

+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
SC 2 date: 2016/01/04 (dump date 2016/01/06) (2 vectors extra from SCET/reset)
spin_period  = 4.1682032682937651
reset_period = 5.1522152392407365
16 reset 'Block' takes: 82.43544382785178
Max Nr. of spins : 20.77721299124559 (including +1 for starting spin)

Here, the graph for all the datasets, ie. the extrapolations and the real data
 - look as as intended, with 19 or 20 vectors per 16 reset 'block', with more
'blocks' having 20 vectors as opposed to 19. (it is 20.77 after all)
- ie. it looks normal, no proof of the extra vectors, as there may have been
before - but this may just be a case where instead of 20, we had 19 vectors,
so this is not apparent. - could investigate further
Adjusting the plots, it seems like there are 3 resets missing, as opposed to 2.

+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
SC 3 date: 2016/01/04 (dump date 2016/01/06) (4 vectors extra from SCET/reset)
spin_period = 4.2104047062408361
reset_period = 5.1522212401212863
16 reset 'Block' takes: 82.43553984194058
MAX Nr. of spins : 20.5790061985612 (including +1 for starting spin)

Graphs shows anomly in real data - 1 long block at 21 vectors,
and 3 short ones at 18.
The extrapolations look as expected.
###############################################################################

###############################################################################
'''