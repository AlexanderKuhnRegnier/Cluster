import RawData
import pandas as pd
import numpy as np
from datetime import datetime
from collections import OrderedDict as od
'''
The goal is to find valid NS packets around the border to extended mode

The input will be the dump date, which will be the latest date searched,
since the extended mode had to happen before that. If the time difference
between the extended mode and the dump is longer than about 93 hours,
this method might fail due to rollover - but this is not likely to require
much consideration.

The other input will be the reset count at the start and end of extended mode.
These will be the top 12 bits of the reset counter, so they will have 
to be shifted up by 4 bits in order to get a number that can be compared
to the reset count in the packet headers. This has an uncertainty of
16 resets (due to the fact that only the top 12 bits are known). Again,
this should not matter too much, since we are only looking for ANY valid
packets around the borders. 
The reset count in the NS packet header will be matched to the reset values
supplied to the code.

The criteria that will be used are as follows:
    Reset count increment has to be 1
    Spacecraft is in Normal Mode
    Spin Period is in the range 3.8 to 4.5 seconds (quite relaxed)
    Both First 1ry HF and First 2ry HF counts have to be non-zero
    None of the error flags are set (eg. Mem dump in progress, etc.)
    Reset Period (s) is in the range 5.13 to 5.17 seconds (very relaxed)
    
Compile a filtered list, using the RawData module (which does some minor
prefiltering and calculation which we will use further here), according to 
the criteria above.
Record if the reset count has changed by more than one when traversing this
filtered list. When this happens, compare the reset counts as follows:
    The reset counts put into this code may not be the exact start/end 
    resets of the extended mode, since you may have missing packets and such.
    So if the resets 'fit into' the gap observed in the filtered list
    (from above) - then that will be the time period where extended mode 
    has occurred!

Regarding wrap-arounds of the reset counter:
    The BSfileprocessing module handles this by adding 4096
    (or 65536 to the entire 16 bits) to the reset counter when this 
    is below 1050 (given that there is also data that has a reset 
    count of above 3000 or so).
    So the max_reset value that this code receives, can be higher than the
    reset values that are actually possible.
    So if max_reset is above 4095, we are dealing with a reset counter
    wrap-around.
    The equivalent rollover will then have to be applied to the data
    read in from the NS packets. If the reset count after the 'jump' is
    lower than the reset count before the 'jump' (jump is the place where
    the reset value changes in the filtered list of packet header info)
    add 2**16 to the final value, and then try to perform the matching. 
    This SHOULD work. If it doesn't, the next rollover won't occur for another
    4 days or so.
'''

RAW = 'C:/Users/ahfku/Documents/Magnetometer/clusterdata/'#home pc
#RAW = 'Z:/data/raw/' #cluster alsvid server

def find_packets(sc,dump_date,min_reset,max_reset):
    '''
    sc        - spacecraft (1|2|3|4)
    dump_date - datetime of the dump date (or pd.Timestamp)
    min_reset - minimum reset value (top 12 bits) in ext mode
    max_reset - maximum reset value (top 12 bits) in ext mode.
                Can be higher than 4095, if a rollover occurs, because
                that should have been corrected for by adding 4096 already.
    Look backwards through NS packet headers in order to find the gap where
    the extended mode data, which has min/max reset values given by 
    min_reset and max_reset, fits in.
    Look back for 8 days. This will be quite slow.
    Probably only need 3/4 days at most, one could optimise this function
    to only search further back than 3 days if nothing is found!
    Or, to make things even faster - serialise the packet_info result
    from RawData.RawDataHeader for a month at a time, for example,
    so that subsequent attempts to access the packet information will be
    much faster - ie multiple processing runs of the same packets would
    be avoided.
    '''
    min_reset_shift = min_reset<<4
    max_reset_shift = max_reset<<4 #gives LOWEST possible
    rollover = False
    if max_reset>4095:
        rollover = True
    '''
    Search from last day forwards, and build up dataframe in this order.
    Last day is 8 days before the dump date.
    '''
    ##########################################################################################change back to 8 days!!!
    dates = pd.date_range(start=dump_date-pd.Timedelta('3 days'),
                            end = dump_date, freq='D')
    #yes, the above includes the 'end' date                            
    packet_info_frames = []                            
    for date in dates:
        packet_info_frames.append(RawData.RawDataHeader(sc,date,'NS',
                                                        dir=RAW).packet_info)
    packets = pd.concat(packet_info_frames,axis=0)
    packets.reset_index(inplace=True,drop=True)
    '''
    Filtering out entries based on the criteria above
    '''
    print "Initial Length:",packets.shape[0]
    packets.dropna(inplace=True)
    packets = packets[packets['Telemetry Mode']=='Normal Mode']
    packets = packets[packets['Reset Increment']==1]
    packets = packets[(packets['Spin Period (s)']>3.8) & \
                                (packets['Spin Period (s)']<4.5)]
    packets = packets[(packets['Reset Period (s)']>5.13) & \
                                (packets['Reset Period (s)']<5.17)] 
    '''
    This filtering of 1ry and 2ry HF counts is more based on qualitative
    observation, since it is possible that a valid packet will have a 0 value
    here. So this will remove some valid packets as well.
    '''                                
    packets = packets[packets['First 1ry HF']!=0]
    packets = packets[packets['First 2ry HF']!=0]
    packets = packets[np.all((packets[['Sumcheck code failure',
                                'Incorrect vectors sampled',
                                'Possible currupt science data',
                                'DPU test sequence number',
                                'Calibration sequence number',
                                'Memory Dump in Progress',
                                'Code Patch in Progress']].values == 0),
                                axis=1)]
    print "After filtering:",packets.shape[0]
    packets.reset_index(inplace=True,drop=True)
    '''
    Now look for reset jumps in the filtered frame
    If EITHER the difference to the next, or the previous
    packet is off, then flag it as True in this case - we will use these
    flagged packets to determine the jump afterwards!
    '''                 
    diffup = (packets['Reset Count'].shift(-1)-packets['Reset Count'])!=1
    diffdown = (packets['Reset Count']-packets['Reset Count'].shift(1))!=1
    jump_packet_mask = diffup | diffdown
    print np.sum(diffup)
    print np.sum(diffdown)
    print np.sum(jump_packet_mask)
    jumps = packets[jump_packet_mask]
    jumps.reset_index(inplace=True,drop=False) #False in case we need it to
                                               #access the original frame
    '''
    Build up intervals from these jumps -> Dataframe containing start/end
    reset of the jump interval (between two packets in the jumps DataFrame
    above), Reset difference, SCET time before/after, SCET time difference
    '''
    nr_entries = jumps.shape[0]
    data_dict = od([('start_reset',[]),('end_reset',[]),
                    ('start_scet',[]),('end_scet',[])])
    for i,j in zip(range(0,nr_entries-1),range(1,nr_entries)):
        start_series = jumps.iloc[i]
        end_series = jumps.iloc[j]
        data_dict['start_reset'].append(start_series['Reset Count'])
        data_dict['end_reset'].append(end_series['Reset Count'])
        data_dict['start_scet'].append(start_series['SCET'])
        data_dict['end_scet'].append(end_series['SCET'])
    intervals = pd.DataFrame(data_dict)
    rollovers_start = []
    rollovers_end = []
    for row_i in range(len(intervals)-1):
        row_j = row_i+1
        value_i = intervals.iloc[row_i]
        value_j = intervals.iloc[row_j]
        if value_i['end_reset']==1 and value_j['start_reset']==1:
            rollovers_start.append(row_i)
            rollovers_end.append(row_j)
    rollover_dict = od([('start_reset',[]),('end_reset',[]),
                    ('start_scet',[]),('end_scet',[])])
    for i,j in zip(rollovers_start,rollovers_end):
        rollover_dict['start_reset'].append(intervals.iloc[i]['start_reset'])
        rollover_dict['end_reset'].append(intervals.iloc[j]['end_reset'])
        rollover_dict['start_scet'].append(intervals.iloc[i]['start_scet'])
        rollover_dict['end_scet'].append(intervals.iloc[j]['end_scet'])
    rollovers = pd.DataFrame(rollover_dict)        
    '''
    remove entries that are now contained within rollover dict from the 
    intervals frame
    '''
    to_drop = np.in1d(intervals.index.values,rollovers_start+rollovers_end)
    intervals.drop(intervals.index[to_drop],axis=0,inplace=True)
    intervals = pd.concat((intervals,rollovers),axis=0)
    intervals.reset_index(drop=True,inplace=True)
    reset_diff = intervals['end_reset']-intervals['start_reset']
    scet_diff = (intervals['end_scet']-  \
                                intervals['start_scet'])/pd.Timedelta(1,'s')
    negative_diff = reset_diff<0
    reset_diff[negative_diff]+=2**16
    intervals.loc[negative_diff,'end_reset']+=2**16
    intervals.insert(intervals.columns.get_loc('end_reset')+1,'reset_diff',
                     reset_diff)
    intervals.insert(intervals.columns.get_loc('end_scet')+1,'scet_diff',
                     scet_diff)
    '''
    the number of resets between the start and end packet must be at least as
    large as the number of resets between the start and end resets given
    to the function. Need to take 16 reset uncertainty into account here.
    When converting the given reset value to the actual reset value,
    ie. shift left by 4 bits given_reset<<4, this will give the LOWEST actual
    reset value that corresponds to the given reset. The highest possible value
    is 15 resets higher.
    '''
    min_reset_diff = max_reset_shift - (min_reset_shift+16)
    filtered_intervals = intervals[intervals['reset_diff']>=min_reset_diff]
    '''
    Matching up the actual reset counts
    '''
    filtered_intervals = filtered_intervals[
                        (filtered_intervals['start_reset']<min_reset_shift+16)
                        & (filtered_intervals['end_reset']>max_reset_shift)]
    if filtered_intervals.shape[0]!=1:
        raise Exception("Should have found 1 interval!")
    initial_reset = filtered_intervals['start_reset'].values[0]
    final_reset = filtered_intervals['end_reset'].values[0]
    if final_reset>65535:
        final_reset -= 65536
    final_packets = packets[
                            (packets['Reset Count']==initial_reset) | \
                            (packets['Reset Count']==final_reset)]
    return final_packets
    
final_packets = find_packets(2,datetime(2016,1,6),3277,4041)