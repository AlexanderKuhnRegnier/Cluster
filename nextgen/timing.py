import timing_end as te
import timing_start as ts
import pandas as pd
import numpy as np
#import matplotlib.pyplot as plt
import RawData
#from datetime import datetime
import valid_packets
import ext_mode_times as emt
pd.options.display.expand_frame_repr=False
pd.options.display.max_rows=20 

#RAW = 'C:/Users/ahfku/Documents/Magnetometer/clusterdata/'#home pc
#RAW = 'Z:/data/raw/' #cluster alsvid server
RAW = '/cluster/data/raw/'
#pickledir = 'C:/Users/ahfku/Documents/Magnetometer/clusterdata/'#home pc
#pickledir = 'Y:/testdata/'

def estimate_spin_reset(sc,ext_date,days=5,dir=RAW):
    if days%2==0:
        '''
        Even number, so we need to increase by one in order to get data
        from before and after ext mode evenly
        '''
        days+=1
    mean_day =  (days+1)/2 #this IS ext_date, ie. the extended mode date
    min_day = ext_date-pd.Timedelta(mean_day-1,'D')
    max_day = ext_date+pd.Timedelta(mean_day-1,'D')
    dates=pd.date_range(start=min_day,end=max_day,freq='D')
    modes= ['NS','BS']
    spin_periods = []
    reset_periods = []
    for date in dates:
        for mode in modes:
            packetdata = RawData.RawDataHeader(sc,date,mode,dir=dir).packet_info
            if not packetdata.empty:
                spin_periods.append(packetdata['Spin Period (s)'].mean())
                reset_periods.append(packetdata['Reset Period (s)'].mean())
    
    spin_period = np.mean(pd.Series(spin_periods).dropna())
    reset_period = np.mean(pd.Series(reset_periods).dropna())
    if not ((3<spin_period<5) & (4<reset_period<6)):
        return None,None
    return spin_period,reset_period
    
def get_vector_block_times(sc,combined_data,first_diff_HF,
                           initial_reset,initial_scet,final_first_diff_HF,
                           final_reset,final_scet,spin_period,reset_period):
    '''
    Needs full reset counts, which are read from the packet headers!
    '''
    '''
    #Sample input
    #SC 3 parameters, for 2016/01/04
    #spin_period = 4.2104047062408361
    #reset_period = 5.1522212401212863 #estimated using function
    spin = spin_period
    reset = reset_period
    spins = 14965+10
    first_diff_HF = (10016-2579) #need to check for rollover
    initial_reset = 52437
    initial_scet = pd.Timestamp('2016-01-04 04:59:47.042457')
    time = lambda spin:spins*spin
    final_reset = 64676  #check for rollover!
    final_first_diff_HF = (65035-64899) #check for rollover!
    real_resets = combined_data['reset'].values
    final_scet = pd.Timestamp('2016-01-04 22:30:24.468790')
    SCET_time_diff = (final_scet-initial_scet)/pd.Timedelta(1,'s')
    '''
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
    #spins = len(combined_data)+10 #this would only spins in the data, not
                                   #total spins in ext mode!!
    '''
    #this is wrong, since we absolutely need the entire interval!!!!
    #So if you had a partial block of data, using this formula for the time
    #period would not allow you to generate all the needed extrapolation!
    time = lambda spin:spins*spin
    
    Need to get time from the scet difference
    '''
    SCET_time_diff = (final_scet-initial_scet)/pd.Timedelta(1,'s') #SCET diff between PACKETS
    nr_spins = combined_data.shape[0]
    time = SCET_time_diff + 10 #(+10 for good measure)
    if first_diff_HF<0:
        first_diff_HF += 2**16
    if final_first_diff_HF<0:
        final_first_diff_HF += 2**16
    reset_diff = final_reset-initial_reset
    if reset_diff<0:
        reset_diff+=2**16
        final_reset+=2**16
    print "data shape:",combined_data.shape
    real_resets = combined_data['reset'].values #top 12 bits values from ext data!
    print "real resets shape:",real_resets.shape
    #ext_date = initial_scet.date()
    '''
    #this is now done before any of the methods is selected!
    spin_period,reset_period = estimate_spin_reset(sc,ext_date,
                                                          days=5,dir=RAW)
    '''
    #spin = spin_period
    #reset = reset_period
    ###############################################################################
    #different corrections, depending on what is seen in the data, and also the
    #SCET time vs. reset count discrepancy!!
    #SCET_time_diff = 63037
    #final_reset -= 4
    ###############################################################################
    
    '''
    Matching up the extrapolated results from
    the packets at the border of extended mode!!
    '''
    '''
    Estimate a new spin time from comparison to extrapolation - offset needs to
    be known before this!
    '''
    print "input into ts offset:"
    print "spin",spin_period
    print "reset",reset_period
    print "real reset shape",real_resets.shape
    print "first diff HF", first_diff_HF
    print "initial reset", initial_reset
    print "time",time,"nr. of spins:",time/spin_period
    offset_start = ts.find_offset_initial(spin_period,reset_period,real_resets,
                                          first_diff_HF,initial_reset,time)
    print "input into t end offset:"
    print "spin",spin_period
    print "reset",reset_period
    print "data shape",real_resets.shape
    print "final first diff HF",final_first_diff_HF
    print "final reset",final_reset
    print "time",time,"nr. of spins:",time/spin_period
    offset_end = te.find_offset_from_end(spin_period,reset_period,real_resets,
                                         final_first_diff_HF,final_reset,time)
    print "start offset:", offset_start," end offset:", offset_end     
    '''
    #no longer recommended, since the spin estimate can be quite unreliabel
    # --too large in most cases, so that the data would overlap the 
    # normal mode data at the end - is this due to the extra resets?
    start_spin = ts.optimise_spin(spin_period,reset_period,time,first_diff_HF,
                                  initial_reset,real_resets,offset_start)
    end_spin = te.optimise_spin(spin_period,reset_period,time,final_first_diff_HF,
                                final_reset,real_resets,offset_end)
    spin_estimates = pd.DataFrame(np.array([start_spin,end_spin]).reshape(-1,2),columns=['start','end'],index=[0])
    spin_estimates['diff'] = spin_estimates['start']-spin_estimates['end']
    spin_estimates['mean'] = np.mean([start_spin,end_spin])
    '''
    spin_estimates = pd.DataFrame([spin_period],columns=['orig'])
    #spin_estimates = spin_estimates[['orig','start','end','diff','mean']]
    #spin_estimates['diff to orig']=spin_estimates['orig']-spin_estimates['mean']
    '''
    Get improved spin estimate from the time of the spins specified by
    offset_start and offset_end - since the SCET times and spin phases
    are known at both the start and end, this is just a matter of
    extracting the right value from the extrapolation!
    '''
    #times relative to SCET time of first packet!
    first_spin = offset_start*spin_period-((first_diff_HF/4096.)+spin_period)
    last_spin = SCET_time_diff+(offset_end*spin_period)-(final_first_diff_HF/4096.)
    spin_estimates['mean'] = (last_spin-first_spin)/nr_spins
    print "spin estimates"
    print spin_estimates            
    spin_estimate=spin_estimates['mean'].values[0]
    print "spin estimate used:",spin_estimate
    spin_times = np.arange(0,combined_data.shape[0],1)*spin_estimate
    real_spin_times = pd.Series([initial_scet+pd.Timedelta(spin_time,'s') for spin_time in spin_times])
    real_spin_times+= pd.Timedelta( (spin_estimate-(first_diff_HF/4096.) + offset_start*spin_estimate) ,'s')
    '''
    #now obsolete with the new way of estimating spin period!
    print start_spin
    print end_spin
    if ( not (3.8<start_spin<4.5) or not  (3.8<end_spin<4.5)):
        print "Something went wrong"
        return pd.Series()
    '''
    print "start offset (spins):",offset_start
    print "last spin time:",real_spin_times.iloc[-1]
    print "end NS packet SCET:",final_scet
    print "offset at end (spins):",offset_end
    print "first spin time:",real_spin_times.iloc[0]
    print "start NS packet SCET:",initial_scet
    if ((offset_start<0) or (real_spin_times.iloc[-1]>final_scet) or \
        (offset_end>0) or (real_spin_times.iloc[0]<initial_scet)):
        print "Something has gone wrong, matching to scch is recommended."
        return pd.Series()
    return real_spin_times

def get_vector_times(sc,combined_data,first_diff_HF,
                           initial_reset,initial_scet,final_first_diff_HF,
                           final_reset,final_scet,spin_period,reset_period):
    '''
    Since the actual function needs to shift vectors for them to match,
    this function will prepare the data to be treated this way, by 
    splitting it up into blocks based on the reset count value contiguity.
    Those blocks will then be fed into the timin function separately,
    and the final result reconstituted from the different parts.
    '''
    diff = combined_data.reset.diff()
    mask1 = diff==1
    mask2 = diff==0
    valid = mask1 | mask2
    #print "masks"
    #print valid
    invalid = pd.DataFrame(~valid.values,index=combined_data.index,columns=['invalid'])
    invalid['block']=invalid['invalid'].cumsum()
    #print invalid
    blocks = np.unique(invalid['block'])
    times = []
    #print "data shape:",combined_data.shape
    for block in blocks:
        input_data = combined_data[invalid['block']==block]
        print "input data shape:",input_data.shape
        print "for input block:",block
        print "out of possible blocks:",blocks
        block_times = get_vector_block_times(sc,input_data,first_diff_HF,
                                             initial_reset,initial_scet,
                                             final_first_diff_HF,
                                             final_reset,final_scet,
                                             spin_period,reset_period)
        if block_times.shape[0]==0:
            print "Unexpected result"
            return pd.Series()
        times.append(block_times)
    vector_times = pd.concat(times)
    if vector_times.shape[0] != combined_data.shape[0]:
        print "Vectors went missing along the way"
        return pd.Series()
    return vector_times
    

def get_timing(sc,dump_date,combined_data,packet_info):
    '''
    +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    '''   
    '''
    load previously processed ext mode data!
    '''
    '''
    import cPickle as pickle
    picklefile = pickledir+'extdata.pickle'
    with open(picklefile,'rb') as f:
        combined_data = pickle.load(f)
        
    picklefile = pickledir+'packetinfo.pickle'
    with open(picklefile,'rb') as f:
        packet_info=pickle.load(f)
       
    picklefile = pickledir+'sc.pickle'
    with open(picklefile,'rb') as f:
        sc = pickle.load(f)
    
    picklefile = pickledir+'dumpdate.pickle'
    with open(picklefile,'rb') as f:
        dump_date = pickle.load(f)
    
    print "Read data from pickles!"
    '''
    print "sc:",sc
    print "dump date:",dump_date
    
    #combined_data = pd.concat((combined_data.iloc[5000:8000],combined_data.iloc[9000:10000],combined_data.iloc[11000:14000]))
    #combined_data = combined_data.iloc[5000:8000]
    ###############################################################################
    '''
    Need to know starting SCET time of dump, so that we can eliminate any entries 
    in the commanding history that were after this time. Of course, this should
    not be necessary since we are matching the times up using the packet
    information on the borders of extended mode, but it can't hurt to have 
    a backup option available in case the packet matching fails for some reason.
    '''
    first_packet_used = combined_data.index.get_level_values('packet')[0]
    start_scet_time = packet_info.loc[first_packet_used]['SCET']
    print first_packet_used
    print start_scet_time
    '''
    Ext mode must have happened sometime before 'start_scet_time'
    But whether it is the first extended mode, or the second, or third that came
    before (since there may be more than one) is not so straightforward
    to determine using this method. One could look at the reset changes 
    throughout the extended mode data, and match this up to the commanding in 
    a crude way, but matching the data up to normal science data is a lot more
    reliable.
    '''
    min_reset = combined_data.reset.min()
    max_reset = combined_data.reset.max()
    initial_reset = None
    initial_scet = None
    final_reset = None
    final_scet = None
    valid = valid_packets.start_end_packets(sc,dump_date,min_reset,max_reset,
                                            dir=RAW)
    start_end_packets = valid.find_valid(max_days=8)
    use_scch = False
    use_scch_extra = False
    print min_reset
    print max_reset
    print start_end_packets.shape
    
    print "Estimating spin and reset period!"
    
    ext_date = start_scet_time.date()
    spin_period,reset_period = estimate_spin_reset(sc,ext_date,
                                                          days=5,dir=RAW)
    print "spin period:",spin_period
    print "reset period:",reset_period
    if not spin_period or not reset_period:
        spin_period,reset_period = estimate_spin_reset(sc,ext_date,
                                                          days=21,dir=RAW)       
        print "Second attempt, across 21 days"
        print "spin period:",spin_period
        print "reset period:",reset_period
        
    if not spin_period or not reset_period:
        '''
        If in 21 days, no spin or reste period could be estimated, something
        must have gone seriously wrong!
        '''
        raise Exception("Could not determine spin and reset period!")
    if not start_end_packets.empty:
        '''
        Start end end packets around ext mode have been found by the packet
        matching method!!
        '''
        start_end_packets = start_end_packets.sort_values('SCET',ascending=True)
        first_diff_HF = start_end_packets.iloc[0]['Packet Start HF'] - \
                        start_end_packets.iloc[0]['Most Recent Sun Pulse']
        initial_reset = start_end_packets.iloc[0]['Reset Count']
        initial_scet = start_end_packets.iloc[0]['SCET']
        final_first_diff_HF = start_end_packets.iloc[1]['Packet Start HF'] - \
                        start_end_packets.iloc[1]['Most Recent Sun Pulse']
        final_reset = start_end_packets.iloc[1]['Reset Count']
        final_scet = start_end_packets.iloc[1]['SCET']
        vector_times = get_vector_times(sc,combined_data,first_diff_HF,
                                               initial_reset,initial_scet,
                                               final_first_diff_HF,
                                               final_reset,final_scet,
                                               spin_period,reset_period)
        '''
        Record the SCET times and reset counts of the packets and later
        infer the number of resets missing/extra from that!
        '''
        if vector_times.shape[0] == 0:
            print "Failed to acquire timing from the packet info, using SCCH"
            use_scch_extra = True
            use_scch = True
        else:
            '''
            We are good to go, just insert the times into the data!
            '''
            combined_data['time'] = vector_times.values
    
    else:
        use_scch = True
    
    if use_scch:
        '''
        This is very very crude at the moment, even without packet information
        at the borders of extended mode, one could use the packet information
        in the BS packet headers on the dump date, in order to extrapolate
        backwards towards the date of extended mode, which would give massive
        improvements, especially if the data happens to be segmented for some
        reason.
        '''
        print "Using SCCH"
        '''
        Either the timing_adjustment or the
        Packet Matching has failed! So we are reduced to using the command history
        and an estimate of the spin period from the surrounding days
        '''
        '''
        Get an average spin time and reset time from packets 
        around the extended mode time
        '''

        commands = emt.ext_commands(sc,ext_date,dir=RAW)
        print "ext commanding, unfiltered"
        print commands
        if commands.empty:
            print "No commanding found, impossible to determine time now!"
            raise Exception
        commands = commands[commands['Start']<start_scet_time]
        commands.sort_values('Start',ascending=False,inplace=True)
        '''
        Having sorted it like this, the first row contains the data pertaining
        to the most recent ext mode commands BEFORE the dump date
        '''
        print "ext commanding"
        print commands
        ext_start = commands.iloc[0]['Start']
        ext_end = commands.iloc[0]['End']
        ext_duration = commands.iloc[0]['Duration (s)']
        print "ext duration:",ext_duration
        expected_duration = combined_data.shape[0]*spin_period
        print "exptected duration:",expected_duration
        '''
        Now, from the ext_start time, as well as the spin_period, the times can
        be approximated
        Split data up into blocks in order to compute the expected duration, 
        from the reset difference between the blocks, as well as the total
        number of vectors.    
        '''
        diff = combined_data.reset.diff()
        mask1 = diff==1
        mask2 = diff==0
        valid = mask1 | mask2
        invalid = pd.DataFrame(~valid.values,index=combined_data.index,columns=['invalid'])
        invalid['block']=invalid['invalid'].cumsum()
        blocks = np.unique(invalid['block'].values)
        combined_data['block'] = invalid['block'].values
        block_keys = []
        if blocks.shape[0]>1:      
            if blocks.shape[0]>4:
                print "Giving up, too many blocks!"
                raise Exception
            groups = combined_data.groupby('block')
            start_resets = []
            end_resets = []
            '''
            Iterate over the groups, recording the start/end reset values
            '''
            for key,data in groups:
                block_keys.append(key)
                start_resets.append(data.reset.min())
                end_resets.append(data.reset.max())
            reset_diffs = []
            for starts,ends in zip(start_resets[1:],end_resets[:-1]):
                reset_diffs.append(starts-ends)
            '''
            Reset diffs contains the reset differences between the blocks of data
            in the combined_data frame - these are the top 12 bits!
            Compute the equivelent time differences between the blocks by
            multiplying the reset diffs by an appropriate factor, up to
            16*the reset difference*reset_period
            '''
            vector_number_time = combined_data.shape[0]*spin_period
            time_diff = ext_duration-vector_number_time
            if time_diff<0:
                print ("vectors in data * spin period should not be greater than the"
                            " scch time period, especially for segmented data!")
                raise Exception
            if not use_scch_extra:
                total_reset_diffs = np.sum(reset_diffs)
                time_diff_per_reset = time_diff/total_reset_diffs
                resets_diff_per_reset = time_diff_per_reset/reset_period
                print "resets per 16 resets needed:",resets_diff_per_reset
                '''
                The value printed out above will be much higher than the value
                you would get by using the method below!
                '''
            start_reset_diff=0
            if use_scch_extra:
                '''
                This means that we have additional information available to help
                us identify where the different blocks of data should go!
                we know initial_reset and final_reset (all 16 bits)
                
                The reset differences between the blocks have already been
                calculated (reset_diffs) - but with the additional information,
                we can now approximate the time difference between the start
                of the first block and the start of extended mode, as well as 
                the difference at the end.
                
                Then, having a list of all of these reset differences, we can
                distribute the 'padding' needed to conform to the expected time
                (from the SCCH) amongst those differences.
                '''
                print "Using scch extra"
                initial_reset_ext = initial_reset>>4
                final_reset_ext = final_reset>>4
                start_reset_diff = combined_data.reset.min()-initial_reset_ext
                end_reset_diff = final_reset_ext-combined_data.reset.max()
                total_reset_diffs = np.sum(reset_diffs)+start_reset_diff+end_reset_diff
                print "reset diff (naive total, start diff, end diff)",np.sum(reset_diffs),start_reset_diff,end_reset_diff
                time_diff_per_reset = time_diff/total_reset_diffs
                resets_diff_per_reset = time_diff_per_reset/reset_period
                print "resets per 16 resets needed:",resets_diff_per_reset
                if resets_diff_per_reset > 17: #allow for it to be slightly over
                    print ("Should not need to fill more than 16 reset period per"
                          " 16 (max) reset difference")
                    print "DEFAULTING BACK to standard scch procedure"  
                    start_reset_diff=0
                    time_diff_per_reset = time_diff/np.sum(reset_diffs)
            if blocks.shape[0]==2:
                time1 = pd.Series([ext_start+pd.Timedelta(raw_time,'s') for raw_time in (np.arange(0,combined_data[combined_data['block']==block_keys[0]].shape[0],1)*spin_period)])+pd.Timedelta(start_reset_diff*time_diff_per_reset,'s')
                time2 = pd.Series([time1.iloc[-1]+pd.Timedelta(raw_time,'s') for raw_time in (np.arange(0,combined_data[combined_data['block']==block_keys[1]].shape[0],1)*spin_period)])+pd.Timedelta(time_diff,'s')
                vector_times = pd.concat((time1,time2))
                combined_data['time'] = vector_times.values
            if blocks.shape[0]==3:
                time1 = pd.Series([ext_start+pd.Timedelta(raw_time,'s') for raw_time in (np.arange(0,combined_data[combined_data['block']==block_keys[0]].shape[0],1)*spin_period)])+pd.Timedelta(start_reset_diff*time_diff_per_reset,'s')
                time2 = pd.Series([time1.iloc[-1]+pd.Timedelta(raw_time,'s') for raw_time in (np.arange(0,combined_data[combined_data['block']==block_keys[1]].shape[0],1)*spin_period)])+pd.Timedelta(time_diff_per_reset*reset_diffs[0],'s')
                time3 = pd.Series([time2.iloc[-1]+pd.Timedelta(raw_time,'s') for raw_time in (np.arange(0,combined_data[combined_data['block']==block_keys[2]].shape[0],1)*spin_period)])+pd.Timedelta(time_diff_per_reset*reset_diffs[1],'s')
                vector_times = pd.concat((time1,time2,time3))
                combined_data['time'] = vector_times.values
            if blocks.shape[0]==4:
                time1 = pd.Series([ext_start+pd.Timedelta(raw_time,'s') for raw_time in (np.arange(0,combined_data[combined_data['block']==block_keys[0]].shape[0],1)*spin_period)])+pd.Timedelta(start_reset_diff*time_diff_per_reset,'s')
                time2 = pd.Series([time1.iloc[-1]+pd.Timedelta(raw_time,'s') for raw_time in (np.arange(0,combined_data[combined_data['block']==block_keys[1]].shape[0],1)*spin_period)])+pd.Timedelta(time_diff_per_reset*reset_diffs[0],'s')
                time3 = pd.Series([time2.iloc[-1]+pd.Timedelta(raw_time,'s') for raw_time in (np.arange(0,combined_data[combined_data['block']==block_keys[2]].shape[0],1)*spin_period)])+pd.Timedelta(time_diff_per_reset*reset_diffs[1],'s')
                time4 = pd.Series([time3.iloc[-1]+pd.Timedelta(raw_time,'s') for raw_time in (np.arange(0,combined_data[combined_data['block']==block_keys[3]].shape[0],1)*spin_period)])+pd.Timedelta(time_diff_per_reset*reset_diffs[2],'s')
                vector_times = pd.concat((time1,time2,time3,time4))
                combined_data['time'] = vector_times.values
        else:
            pad = 0
            if expected_duration > ext_duration:
                print "expected, ext duration",expected_duration,ext_duration
                '''
                Data would overlap, so try to adjust the spin period a little,
                but only up to 1.5 % of the original estimate!
                '''
                adjusted_spin = ext_duration / combined_data.shape[0]
                print "adjusted spin",adjusted_spin
                if abs(adjusted_spin-spin_period)>0.015*spin_period:
                    print "Overlap is unavoidable here for some reason, Error!"
                    raise Exception
                else:
                    spin_period = adjusted_spin 
            else:
                '''
                Need to add padding, since data is too short
                '''
                time_diff = ext_duration - expected_duration
                pad = time_diff/2.
                print "padding at start (and end):",pad
            raw_times = (np.arange(0,combined_data.shape[0],1)*spin_period)+pad
            real_spin_times = pd.Series([ext_start+pd.Timedelta(spin_time,'s') for spin_time in raw_times])
            combined_data['time'] = real_spin_times.values
            
    #combined_data.plot(x='time',y='mag')
    '''
    picklefile = pickledir+'extdata.pickle'
    with open(picklefile,'wb') as f:
        pickle.dump(combined_data,f,protocol=2)
    '''
    return spin_period,reset_period,initial_reset,initial_scet,final_reset,final_scet