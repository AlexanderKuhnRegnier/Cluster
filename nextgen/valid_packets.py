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

#RAW = 'C:/Users/ahfku/Documents/Magnetometer/clusterdata/'#home pc
#RAW = 'Z:/data/raw/' #cluster alsvid server

class start_end_packets:
    def __init__(self,sc,dump_date,min_reset,max_reset,dir='Z:/data/raw/'):
        self.RAW = dir
        self.sc = sc
        self.dump_date = dump_date
        self.min_reset = min_reset
        self.max_reset = max_reset
        self.min_reset_shift = min_reset<<4
        self.max_reset_shift = max_reset<<4 #gives LOWEST possible
        self.rollover = False
        self.dates = pd.date_range('2000',periods=0) #empty
        self.packets = pd.DataFrame()
        if max_reset>4095:
            self.rollover = True

    def read_packet_info(self,days=3):            
        '''
        Search from last day forwards, and build up dataframe in this order.
        Last day is n days before the dump date.
        '''
        if self.dates.to_series().empty:
            '''
            No packet data read before, start anew with the given days.
            '''
            self.dates = pd.date_range(start=self.dump_date-pd.Timedelta(days,'D'),
                                    end = self.dump_date, freq='D')
            #yes, the above includes the 'end' date                            
            packet_info_frames = []                            
            for date in self.dates:
                packet_info_frames.append(RawData.RawDataHeader(self.sc,date,'NS',
                                                        dir=self.RAW).packet_info)
            self.packets = pd.concat(packet_info_frames,axis=0)
        else:
            '''
            Here, we had already read packet info before, so we need to look
            for headers on days prior to the dates already in self.dates,
            in such a way as that we will have looked at 'days' number of days
            in total.
            '''
            assert self.dates.max()==self.dump_date,("If we have read data"
                                "before, this should be the case!")
            still_to_read = days-len(self.dates)+1 #+1 because intervals include end date
            if still_to_read>0:
                new_dates = pd.date_range(
                                start=self.dump_date-pd.Timedelta(days,'D'),
                                end=self.dates.min()-pd.Timedelta(1,'D'),
                                freq='D')
                packet_info_frames = [] 
                for date in new_dates:
                    packet_info_frames.append(
                                    RawData.RawDataHeader(self.sc,date,'NS',
                                                    dir=self.RAW).packet_info) 
                
                self.dates = new_dates.append(self.dates) #since new_dates 
                                                          #are before
                new_packets = pd.concat(packet_info_frames,axis=0)
                self.packets = pd.concat((new_packets,self.packets),axis=0)
        self.packets.reset_index(inplace=True,drop=True)
    def find_packets(self):
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
        if self.packets.empty:
            print "Need to call read_packet_info first!"
            return None
        '''
        Filtering out entries based on the criteria above
        '''
        #print "Initial Length:",self.packets.shape[0]
        self.packets.dropna(inplace=True)
        self.packets = self.packets[self.packets['Telemetry Mode']=='Normal Mode']
        self.packets = self.packets[self.packets['Reset Increment']==1]
        self.packets = self.packets[(self.packets['Spin Period (s)']>3.8) & \
                                    (self.packets['Spin Period (s)']<4.5)]
        self.packets = self.packets[(self.packets['Reset Period (s)']>5.13) & \
                                    (self.packets['Reset Period (s)']<5.17)] 
        '''
        This filtering of 1ry and 2ry HF counts is more based on qualitative
        observation, since it is possible that a valid packet will have a 0 value
        here. So this will remove some valid packets as well.
        '''                                
        self.packets = self.packets[self.packets['First 1ry HF']!=0]
        self.packets = self.packets[self.packets['First 2ry HF']!=0]
        self.packets = self.packets[np.all((self.packets[['Sumcheck code failure',
                                    'Incorrect vectors sampled',
                                    'Possible currupt science data',
                                    'DPU test sequence number',
                                    'Calibration sequence number',
                                    'Memory Dump in Progress',
                                    'Code Patch in Progress']].values == 0),
                                    axis=1)]
        #print "After filtering:",self.packets.shape[0]
        self.packets.reset_index(inplace=True,drop=True)
        '''
        Now look for reset jumps in the filtered frame
        If EITHER the difference to the next, or the previous
        packet is off, then flag it as True in this case - we will use these
        flagged packets to determine the jump afterwards!
        '''                 
        diffup = (self.packets['Reset Count'].shift(-1)-self.packets['Reset Count'])!=1
        diffdown = (self.packets['Reset Count']-self.packets['Reset Count'].shift(1))!=1
        jump_packet_mask = diffup | diffdown
        #print np.sum(diffup)
        #print np.sum(diffdown)
        #print np.sum(jump_packet_mask)
        jumps = self.packets[jump_packet_mask]
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
        #print "intervals scet times"
        #print intervals
        if intervals.empty:
            print "Found no intervals"
            return None
        #print intervals['end_scet'],intervals['start_scet']
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
        min_reset_diff = self.max_reset_shift - (self.min_reset_shift+16)
        filtered_intervals = intervals[intervals['reset_diff']>=min_reset_diff]
        '''
        Matching up the actual reset counts
        '''
        filtered_intervals = filtered_intervals[
                            (filtered_intervals['start_reset']<self.min_reset_shift+16)
                            & (filtered_intervals['end_reset']>self.max_reset_shift)]
        if filtered_intervals.shape[0]!=1:
            print "Should have found 1 interval!"
            return None
        initial_reset = filtered_intervals['start_reset'].values[0]
        final_reset = filtered_intervals['end_reset'].values[0]
        if final_reset>65535:
            final_reset -= 65536
        final_packets = self.packets[
                                (self.packets['Reset Count']==initial_reset) | \
                                (self.packets['Reset Count']==final_reset)]
        return final_packets

    def try_until_found(self,max_days=8):
        '''
        Try reading new header information for a maximum of 'max_days'
        before the dump date. As soon as a jump that fits the criteria is
        found, it is returned! If it is not found, then None is returned 
        to signal failure.
        If this not work, even for 7-8 days - then a more crude method can
        be used.
        '''
        for read_days in range(1,max_days+1):
            self.read_packet_info(days=read_days)
            final_packets = self.find_packets()
            if type(final_packets)==pd.DataFrame:
                return final_packets
        return None
    
    def simple_packet_search(self):
        '''
        This should only be used if the 'try_until_found' method
        did not return any result, for some reason. That could be, because
        there is no data fitting the exact requirements, or because the 
        software has an error in it and cannot handle certain packet data.
        
        This 'cruder' version simply finds packets based on their reset 
        count.    
        Also, this relies on having called 'try_until_found' or the 
        read_packet_info method itself before, so that the self.packets
        frame is populated!
        '''
        if self.packets.empty:
            print "Need to populate packet info first!"
            return None
        target_min = self.min_reset_shift+16
        target_max = self.max_reset_shift+0
        if self.rollover:
            target_max -= 65536
        #threshold = 400000 #Not used atm - should this be used? It could cause
                            #no packets to be detected in the case of missing
                            #ext mode data...
        '''
        find match for target_min - want larger value
        '''
        reset_diff = self.packets['Reset Count']-target_min
        reset_diff = reset_diff[reset_diff<0]
        if not reset_diff.empty:
            #reset_diff = self.packets['Reset Count']-target_min
            #reset_diff = reset_diff[reset_diff.abs()<threshold]
            reset_diff.sort_values(ascending=False,inplace=True)
            #print reset_diff,target_min
            min_packet_index = reset_diff.index[0]
        '''
        find match for target_max - want lower value
        '''
        reset_diff = self.packets['Reset Count']-target_max
        reset_diff = reset_diff[reset_diff>0]
        if not reset_diff.empty:
            #reset_diff = self.packets['Reset Count']-target_max
            #reset_diff = reset_diff[reset_diff.abs()<threshold]
            reset_diff.sort_values(ascending=True,inplace=True) 
            #print reset_diff,target_max
            max_packet_index = reset_diff.index[0]   
            final_packets = self.packets.loc[[min_packet_index,max_packet_index]]
            if type(final_packets)==pd.DataFrame:
                return final_packets
        return None
    
    def find_valid(self,max_days=8):
        '''
        Tie all of the above together, first searching for matches using
        the more sophisticated method, and then resorting to the simple method
        if this fails. If this still does not yield results, return None
        The commanding history will then probably be used, in the
        rare case that this should be needed.
        '''
        valid = self.try_until_found(max_days)
        if type(valid) == pd.DataFrame:
            return valid
        valid = self.simple_packet_search()
        if type(valid) == pd.DataFrame:
            return valid 
        return pd.DataFrame()
        
'''
packets = start_end_packets(2,datetime(2016,1,6),3277,4041)
valid = packets.find_valid(8)
'''
'''
final_packets = packets.try_until_found()
final_packets2 = packets.simple_packet_search()
'''