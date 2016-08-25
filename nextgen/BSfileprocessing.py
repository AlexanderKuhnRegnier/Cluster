import numpy as np
import pandas as pd
from datetime import datetime
import os
import RawData
import ext_mode_times as emt
from frame_hex_format import hexify
import matplotlib.pyplot as plt
#import timing
#import valid_packets

RAW = 'C:/Users/ahfku/Documents/Magnetometer/clusterdata/'#home pc
#RAW = 'Z:/data/raw/' #cluster alsvid server
pickledir = 'C:/Users/ahfku/Documents/Magnetometer/clusterdata/'#home pc
#pickledir = 'Y:/testdata/'

'''
#Use this to suppress performance warn messages!
import warnings
warnings.simplefilter(action='ignore',category='PerformanceWarning')
'''
verbose=True
def browse_frame_ipython(frame,window=40):
    frame['reset']=frame['reset'].apply(hex)
    from IPython.utils.coloransi import TermColors as tc
    import msvcrt
    window=int(window)
    helptext=(tc.Green+
    "d for 1/2 down"+'\n'+
    "u for 1/2 up"+'\n'+
    "spacebar for page down"+'\n'+
    "p for next packet (444 lines)"+'\n'+
    "o for previous packet (-444 lines)"+'\n'+
    "q for quit"+'\n'+
    "h to print this help text"+tc.Normal)
    print helptext
    '''
    row_data = lambda frame,row:list(frame.index.values[row])+\
                                        list(frame.values[row])
    row_str = lambda frame,row:"{0:9s}{1:7d}{2:7d}{3:>10s}{4:7d}{5:7d}{6:7d}{7:7d}".\
                        format(*row_data(frame,row))
    headers = ["Packet","Vector","Range","Reset","Sensor","x","y","z"]
    '''
    scroll = 0   
    max_row = frame.shape[0]
    '''
    pre-process strings!
    '''
    row_strings = []
    current_rows = 0
    '''
    def process_rows(current_rows,rows):
        new_rows = []
        for i in range(current_rows,current_rows+rows):
            if not i<0 and not i>max_row:
                new_rows.append(row_str(frame,i))
        return new_rows
    '''
    def process_rows(current_rows,rows):
        if current_rows==0:
            new = frame[current_rows:current_rows+rows].to_string(sparsify=False,
                                            header=True,index_names=True,
                                            col_space=7)
        else:
            new = frame[current_rows:current_rows+rows].to_string(sparsify=False,
                                            header=False,index_names=False,
                                            col_space=7)
        return new.split('\n')
    print "processing:",
    row_strings+=process_rows(current_rows,1000)
    current_rows = len(row_strings)
    #print "rows available:"+tc.Green+str(current_rows)+tc.Normal
    if window>max_row:
        print '\n'.join(row_strings[0:max_row])
    else:
        print '\n'.join(row_strings[0:window])
    while 1:
        char = msvcrt.getch()
        if char=='u':
            #os.system('CLS')
            scroll -= window/2
            if scroll<0:
                scroll=0
            '''
            if scroll==0:
                print "{0:>9s}{1:>7s}{2:>7s}{3:>10s}{4:>7s}{5:>7s}{6:>7s}{7:>7s}".format(*headers)
            '''
            mini = scroll-20
            maxi = scroll+window
            if mini<0:
                mini = 0
            if maxi>max_row:
                maxi = max_row
            print '\n'.join(row_strings[mini:maxi])
        elif char=='o':#previous packet
            os.system('CLS')
            scroll -= 444
            if scroll<0:
                scroll=0
            '''
            if scroll==0:
                print "{0:>9s}{1:>7s}{2:>7s}{3:>10s}{4:>7s}{5:>7s}{6:>7s}{7:>7s}".format(*headers)
            '''
            mini = scroll
            maxi = scroll+window
            if mini<0:
                mini = 0
            if maxi>max_row:
                maxi = max_row
            print '\n'.join(row_strings[mini:maxi])
        elif char=='d':
            scroll += window/2
            if scroll>max_row-window:
                scroll=max_row-window
            mini = scroll
            maxi = scroll+window
            print '\n'.join(row_strings[mini:maxi])
        elif char=='p':
            scroll+=444
            if scroll>max_row-window:
                scroll=max_row-window
            mini = scroll
            maxi = scroll+window
            print '\n'.join(row_strings[mini:maxi])
        elif char == ' ':
            scroll+=window
            if scroll>max_row-window:
                scroll=max_row-window
            print '\n'.join(row_strings[scroll:scroll+window])
        if current_rows-scroll<1000:
            #print "processing:",
            row_strings+=process_rows(current_rows,1000)
            current_rows = len(row_strings)
            #print "rows available:"+tc.Green+str(current_rows)+tc.Normal
        if char == chr(27) or char=='q':
            break
        if char == 'h':
            print helptext

class ExtData(RawData.RawDataHeader):
    def __init__(self,sc,dt,mode,version='B',dir='Z:/data/raw/'):
        RawData.RawDataHeader.__init__(self,sc,dt,mode,version,dir)
        self.evenodd = pd.DataFrame()
        self.oddeven = pd.DataFrame()
        self.combined = pd.DataFrame()
        self.full_packets = np.array([])
        self.blocks = pd.DataFrame()    
    def read_even(self,data):
        data_dict = {'x':[],'y':[],'z':[],'sensor':[],'range':[],'reset':[]}
        for offset in range(0,444*8,8):
            data_dict['x'].append(RawData.RawDataHeader.read_bytes(
                                                    [offset,offset+1],data))
            data_dict['y'].append(RawData.RawDataHeader.read_bytes(
                                                    [offset+2,offset+3],data))
            data_dict['z'].append(RawData.RawDataHeader.read_bytes(
                                                    [offset+4,offset+5],data))
            last_bytes = RawData.RawDataHeader.read_bytes(
                                                    [offset+6,offset+7],data)
            sensor = last_bytes>>15
            inst_range = (last_bytes>>12) & 0b0111
            reset = last_bytes & (0b111111111111)
            data_dict['sensor'].append(sensor)
            data_dict['range'].append(inst_range)
            data_dict['reset'].append(reset)
        '''
        Read 1/2 vetor at end of even packet!
        '''
        offset = 444*8
        data_dict['x'].append(RawData.RawDataHeader.read_bytes(
                                                    [offset,offset+1],data))
        data_dict['y'].append(RawData.RawDataHeader.read_bytes(
                                                    [offset+2,offset+3],data))
        '''
        fill missing half vector with -1
        '''   
        data_dict['z'].append(-1)
        data_dict['sensor'].append(-1)
        data_dict['range'].append(-1)
        data_dict['reset'].append(-1)
        if len(data_dict['x']) != 445:
            raise Exception("Read even has not read 444.5 vectors!")
        data_dict['vector'] = np.arange(1,446,1.) #needs to be float array
        data_dict['vector'][-1] = 444.5
        df = pd.DataFrame(data_dict,columns = ['vector','range','reset',
                                                       'sensor','x','y','z'])                                 
        return df
    def read_odd(self,data):
        data_dict = {'x':[],'y':[],'z':[],'sensor':[],'range':[],'reset':[]}
        '''
        get 1/2 vector at the start of the odd packet!
        '''
        data_dict['z'].append(RawData.RawDataHeader.read_bytes([0,1],data))
        last_bytes = RawData.RawDataHeader.read_bytes([2,3],data)
        sensor = last_bytes>>15
        inst_range = (last_bytes>>12) & 0b0111
        reset = last_bytes & (0b111111111111)
        data_dict['sensor'].append(sensor)
        data_dict['range'].append(inst_range)
        data_dict['reset'].append(reset)  
        '''
        fill missing half vector with -1
        '''
        data_dict['x'].append(-1)
        data_dict['y'].append(-1)
        
        for offset in range(4,(444*8)+4,8):
            #print "offset",offset
            data_dict['x'].append(RawData.RawDataHeader.read_bytes(
                                                    [offset,offset+1],data))
            data_dict['y'].append(RawData.RawDataHeader.read_bytes(
                                                    [offset+2,offset+3],data))
            data_dict['z'].append(RawData.RawDataHeader.read_bytes(
                                                    [offset+4,offset+5],data))
            last_bytes = RawData.RawDataHeader.read_bytes(
                                                    [offset+6,offset+7],data)
            sensor = last_bytes>>15
            inst_range = (last_bytes>>12) & 0b0111
            reset = last_bytes & (0b111111111111)
            data_dict['sensor'].append(sensor)
            data_dict['range'].append(inst_range)
            data_dict['reset'].append(reset)
        if len(data_dict['x']) != 445:
            raise Exception("Read even has not read 444.5 vectors!")
        data_dict['vector'] = np.arange(0,445,1.) #needs to be float array
        data_dict['vector'][0] = 0.5
        df = pd.DataFrame(data_dict,columns = ['vector','range','reset',
                                                       'sensor','x','y','z'])      
        return df
    def read_data(self):
        '''
        Read data, then filter out 
        non MSA Dump Packets out of the packets list
        '''
        packet_mask = self.packet_info['Telemetry Mode'] == 'MSA Dump'
        self.removed_packets = self.packet_info[~packet_mask].index.values
        self.removed_packets_info = self.packet_info[~packet_mask]
        self.packet_info = self.packet_info[packet_mask]
        even = []
        odd = []
        #packets = self.packet_info.index.values
        read_packets = []
        packet_offset = 0
        for packet,row in self.packet_info.iterrows():
            packet_offset += 49 #skip headers (already read)
            packet_length = row['Packet Length']
            skip = False
            if packet_length != 3596 or row['Telemetry Mode'] != 'MSA Dump': #maybe log this / exception?
                print ("Warning, packet length not as expected:"+
                        str(packet_length)+" SKIPPING")
                skip = True
            vector_data_length = packet_length-34
            if not skip:
                read_packets.append(packet)
                even.append(self.read_even(self.data[packet_offset:
                                        packet_offset+vector_data_length]))
                odd.append(self.read_odd(self.data[packet_offset:
                                        packet_offset+vector_data_length]))
            packet_offset+=vector_data_length
        self.even = pd.concat((even))
        self.odd = pd.concat((odd))
        if self.even.shape != self.odd.shape:
            raise Exception("Even and Odd shapes don't mach, should contain"
                            "the same number of vectors at this point!")
        top_level = []
        if (len(read_packets) != len(odd)) or (len(read_packets) != len(even)):
            raise Exception("Unequal lengths!")
        for packet,packeto,packete in zip(read_packets,odd,even):
            if packete.shape != packeto.shape:
                raise Exception("Unequal number of vectors in packet nr:"+
                                    str(packet))
            length = packete.shape[0]
            top_level.extend([packet]*length)
            
        bottom_level=range(0,self.odd.shape[0])            
        multiindex=pd.MultiIndex.from_arrays([top_level,bottom_level],
                                             names=['packet','index'])
        self.even.index=multiindex
        self.odd.index=multiindex
        self.even.columns = ['vector','range','reset','sensor','x','y','z']
        self.odd.columns = ['vector','range','reset','sensor','x','y','z']
    def join_half_vecs(self):
        even_packet_list =np.unique(self.even.index.get_level_values(0).values)
        odd_packet_list = np.unique(self.odd.index.get_level_values(0).values)
        if not np.all(even_packet_list == odd_packet_list):
            raise Exception("At this point, even and odd frames should contain"
                            " equal number of packets!")
        if not self.even.shape==self.odd.shape:
            raise Exception("Even and Odd frames should contain the same "
                            "number of vectors before joining them.")
        self.full_packets = even_packet_list #is the same as odd_packet_list
        for packet,next_packet in zip(self.full_packets[:-1],
                                      self.full_packets[1:]):
            even_half=pd.Series()
            odd_half=pd.Series()
            #####even,end of packet#####
            even_packet=self.even.xs(packet,level='packet',
                         drop_level=False)
            if not even_packet.empty:
                even_half = even_packet.iloc[-1]
                if not np.any(even_half.values==-1):
                    raise Exception("Expected -1 in even half vector!")
            #####odd,start of packet####
            odd_packet=self.odd.xs(next_packet,level='packet',
                         drop_level=False)
            if not odd_packet.empty:
                odd_half = odd_packet.iloc[0]
                if not np.any(odd_half.values==-1):
                    raise Exception("Expected -1 in odd half vector!")
            if not even_half.empty and not odd_half.empty:
                '''
                join the vectors, put them into the even dataframe!
                use even as 'starting point'
                '''
                index = even_half.name[1]
                self.even.set_value((packet,index),'range',odd_half['range'])
                self.even.set_value((packet,index),'reset',odd_half['reset'])
                self.even.set_value((packet,index),'z',odd_half['z'])
                self.even.set_value((packet,index),'sensor',odd_half['sensor'])
                #444.5 vector now contains
                #full vector!
                if np.any(-1==self.even.loc[packet,index].values):
                    print self.even.loc[packet,index]
                    raise Exception("All -1 values should have been filled!")
                vector_number = self.odd.loc[next_packet].iloc[0].name
                odd_half_label = (next_packet,vector_number)
                #drop the odd half vector from the frame, leaving it with
                #1 vector less than the even packet
                self.odd.drop(odd_half_label,axis=0,inplace=True)
            else:
                raise Exception("No half vectors could be read!")
        '''
        remove half vector entry from last even packet, since this can
        never be reconstructed
        similarly, remove half vector entry from first odd packet
        '''
        even_drop = self.even.iloc[-1].name
        self.even.drop(even_drop,inplace=True,axis=0)
        odd_drop = self.odd.iloc[0].name
        self.odd.drop(odd_drop,inplace=True,axis=0)
        '''
        Drop 'vector' columns from dataframes
        '''
        self.odd.drop('vector',axis=1,inplace=True)
        self.even.drop('vector',axis=1,inplace=True)
    def two_series(self):
        '''
        needs to be executed immediately after joining the half vectors!
        create two chains of frames from the even and odd dataframes
        'evenodd' chain with even frame, odd frame, ...
        'oddeven' chain with odd frame, even frame, ...
        '''
        '''
        At this point, the even and odd dataframes contain different numbers
        of vectors. When they are stitched together into two different series,
        the evenodd series may contain 1 more vector or the same number of 
        vectors as the oddeven series, depending on the number of packets
        '''
        even_packets_existing = np.unique(self.even.index.get_level_values(
                                                            'packet').values)
        odd_packets_existing = np.unique(self.odd.index.get_level_values(
                                                            'packet').values)
        if (self.full_packets.shape != even_packets_existing.shape) or \
                (self.full_packets.shape != odd_packets_existing.shape):
            raise Exception("Packet numbers have changed!")
        '''
        the two lists above will deviate from the 'full' packet list
        before any filtering has been done - just a check at this point
        '''
        '''
        create 'evenodd' chain of frames,
        need to use full_packets list here, since this list contains all the
        MSA dump packets in the right ORDER, which is crucial, since we are
        concerned with even and odd packets, whose order matters
        '''
        even_packets = self.full_packets[0:-1:2]#can't use last packet here!
        odd_packets = self.full_packets[1::2]
        if even_packets.shape[0] != odd_packets.shape[0]:
            raise Exception("The packet list lengths should be equal "
                                "at this point!")
        frames = []
        for even_packet,odd_packet in zip(even_packets,odd_packets):
            frames.append(self.even.xs(even_packet,level='packet',
                         drop_level=False))
            frames.append(self.odd.xs(odd_packet,level='packet',
                         drop_level=False))
        self.evenodd = pd.concat((frames))
        '''
        Drop vector columns. Instead, create a vector index, starting from 1,
        increasing monotoincally, without interruption until the last vector.
        This is done, since at this point, no filtering has been done,
        so all of the vectors should be present, and should follow each other.
        Same is done for the oddeven frame below.
        '''
        packetlevel = self.evenodd.index.get_level_values('packet').values
        vectorlevel = np.arange(1,self.evenodd.shape[0]+1,1)
        new_multiindex = pd.MultiIndex.from_arrays((packetlevel,
                                                    vectorlevel),
                                                    names = ['packet',
                                                    'vector'])
        self.evenodd.index = new_multiindex
        '''
        create 'oddeven' chain of frames,
        '''
        even_packets = self.full_packets[1::2]
        odd_packets = self.full_packets[0:-1:2]
        if even_packets.shape[0] != odd_packets.shape[0]:
            raise Exception("The packet list lengths should be equal "
                                "at this point!")
        frames = []
        for odd_packet,even_packet in zip(odd_packets,even_packets):
            frames.append(self.odd.xs(odd_packet,level='packet',
                         drop_level=False))
            frames.append(self.even.xs(even_packet,level='packet',
                         drop_level=False))
        self.oddeven = pd.concat((frames))
        packetlevel = self.oddeven.index.get_level_values('packet').values
        vectorlevel = np.arange(1,self.oddeven.shape[0]+1,1)
        new_multiindex = pd.MultiIndex.from_arrays((packetlevel,
                                                    vectorlevel),
                                                    names=['packet','vector'])
        self.oddeven.index = new_multiindex
        length_diff = self.evenodd.shape[0]-self.oddeven.shape[0]
        if length_diff!=0 and length_diff!=1:
            raise Exception("The length of evenodd and oddeven should differ"
                            " by 0 or 1!")
    def filter_data(self,frame):
        '''
        Filters even,odd,evenodd and oddeven frames - these should all be
        passed into the function separately
        '''
        '''
        unused vector areas could be set to 
        AAAA5555AAAA5555AAAA ie. 1010 1010 1010 etc....
        or
        5555AAAA5555AAAA5555 ie. 0101 0101 0101 etc....
        So need to check for both simultaneously
        '''
        #invalid bytes
        invalid1 = 0b10101010
        invalid2 = 0b01010101
        invalid_magnetic1 = (invalid1<<8)+invalid1#same for x,y,z
        invalid_magnetic2 = (invalid2<<8)+invalid2
        invalid_sensor1 = 1
        invalid_sensor2 = 0
        invalid_range1 = 0b010
        invalid_range2 = 0b101
        invalid_reset1 = (0b1010<<8)+invalid1
        invalid_reset2 = (0b0101<<8)+invalid2
        invalid_row_data1 = np.array([invalid_range1,invalid_reset1,
                             invalid_sensor1,invalid_magnetic1,
                             invalid_magnetic1,invalid_magnetic1])
        invalid_row_data2 = np.array([invalid_range2,invalid_reset2,
                             invalid_sensor2,invalid_magnetic2,
                             invalid_magnetic2,invalid_magnetic2])   
        mask = ~(frame.apply(lambda x:np.all( (x==invalid_row_data1) | \
                                (x==invalid_row_data2)),axis=1,raw=True).values)
        frame = frame[mask]        
        '''
        filter out entries with all 0's in them
        '''
        mask = ~(frame.apply(lambda x:np.all(x==0),axis=1,
                                    raw=True).values)
        frame = frame[mask]
        '''
        filter out invalid ranges, ie range<2 (range 7 is technically allowed)
        '''        
        mask = (frame['range']>1).values
        frame = frame[mask]
        '''
        filter out the inboard sensor, since this is never used 
        -- is this essential, since it is technically possible to have
        the inboard sensor??
        '''
        mask = (frame['sensor']==0).values
        frame = frame[mask]   
        return frame
    def select_packets(self):
        '''
        create chain of dataframes based on assessment of packets - 
        if they are even or odd!
        -could a corrupt packet be even at the start, and odd at the end,
        or vice versa? That would defeat this method
        '''
        '''
        select packets based on size ratio
        if even packet is 1.5 times the size of the odd packet or larger
        (and vice versa)
        '''
        compare_factor = 1.5
        min_vecs = 10
        packet_sizes_even = self.even.groupby(level=['packet']).size()
        packet_sizes_even.name = 'even'
        packet_sizes_odd = self.odd.groupby(level=['packet']).size()
        packet_sizes_odd.name = 'odd'
        self.packet_sizes = pd.concat((packet_sizes_even,packet_sizes_odd),
                                      axis=1)
        def iseven_size_comparison(x):
            even = x['even']
            odd = x['odd']
            if even>odd*compare_factor and even>min_vecs:
                return True
            elif odd>even*compare_factor and odd>min_vecs:
                return False
            else:
                return -1
        self.packet_sizes.fillna(0,inplace=True)
        self.packet_sizes['iseven']=self.packet_sizes[['even','odd']].apply(
                                                iseven_size_comparison,axis=1)
        if np.all(self.packet_sizes['iseven'].values==-1):
            print "No extended Mode Data Detected"
            return None
        selected_packets = self.packet_sizes[
                                self.packet_sizes['iseven']!=-1][['iseven']]          
        '''
        start segregating into different chunks by looking at the alternation
        of even and odd packets. If there is ever an even one next to another
        even packet, or and odd packet next to another odd packet, the starting
        packet of such a change will be recorded
        '''
        selected_packets['contiguous_parity']=selected_packets['iseven']!= \
                                        selected_packets['iseven'].shift()
        '''
        segregate based on packet number. If two packets numbers are not
        contiguous, record this as well
        '''
        #need to do this, because the shift operation cannot be done on an
        #index, only an a series/frame, etc. (is this really true?)
        #in order to match the index of the frame, reassign index as well
        packet_numbers = pd.Series(selected_packets.index.values,
                                   index=selected_packets.index)
        #basically just detect where the packet number changes by more than 1!
        selected_packets['contiguous_packets']=\
              (packet_numbers==(packet_numbers.shift()+1))
        '''
        where the columns titled 'contiguous' are False is where a break 
        occurs!
        '''
        '''
        combine the two 'contiguous' columns so that if any entry is false,
        a break can be identified there -> 'contiguous' column
        this is done with the & operator (bitwise and overloaded for arrays)
        '''        
        selected_packets['contiguous']= (selected_packets['contiguous_parity']\
                                      & selected_packets['contiguous_packets'])
        '''
        now invert the truth value of the 'contiguous' columns in order to
        be able to do a cummulative sum, which increases only when there as a
        non-contiguous value - so, in the inverted array, that would be 
        represented by a "True" value
        '''
        selected_packets['breaks'] = ~selected_packets['contiguous']
        selected_packets['counts'] = selected_packets['breaks'].cumsum()
        '''
        Finally, blocks of contiguous packets can be identified from the 
        'counts' column by grouping the data and getting the first and 
        last indices - those indices are INCLUSIVE, so the last index is 
        the last valid packet in that group
        '''
        block_ranges = selected_packets.groupby('counts').apply(\
                                            lambda x:(x.index[0],x.index[-1]))
        block_ranges.index.name='block'
        self.blocks=pd.DataFrame({'packets':block_ranges,
                                  'start_parity':block_ranges.apply(
                                  lambda x:'even' if selected_packets[
                                  'iseven'].loc[x[0]] else 'odd')})
        
    def reset_analysis(self,frame):
        '''
        Looks at the reset values of the vectors within the dataframe, and 
        checks whether they are increasing 'slowly', ie by either 0 or 1. 
        If that is not the case, the vectors quality is set to 'False'.
        '''
        '''
        add new 'reset_quality' column to the 'even' and 'odd' dataframes,
        which indicates if the reset increase is good or not
        use 'reset'.shift(-1) - 'reset' to compare rows to next rows,
        and 'reset' - 'reset'.shift(1) to compare rows to previous rows
        This then looks at the differences of a vector to the previous,
        and the next vector! - If one of those is valid, then use it.
        The differences have to be 0 or 1 for there to be valid data.
        
        --The analysis is performed for all vectors in the frame,
        partly for convenience, since this is slightly easier to write,
        and also because this allows for a more straightforward manual visual 
        inspection of the data, should this be needed.
        Also, computing 'rdiff_prev','rdiff_next','reset_quality',
        'quality_change' and 'vblock' takes only around 5 ms 
        for even & odd dataframes of length ~6000
        '''
        '''
        rough checks on the input dataframe
        '''
        dataframe = frame.copy()
        if dataframe.index.names != ['packet','vector']:
            raise Exception("Input Dataframe needs to have a multiindex with"
                            "level names 'packet' and 'vector'")
        if 'reset' not in dataframe.columns:
            raise Exception("Input should contain 'range' column!")
        dataframe.index = dataframe.index.droplevel('packet')
        dataframe['rdiff'] = dataframe['reset']-dataframe['reset'].shift(1)
        dataframe['quality_change']=((dataframe['rdiff']!=0) & 
                                        (dataframe['rdiff']!=1))
        dataframe['vblock_resets']=dataframe['quality_change'].cumsum()
        '''
        Finally, blocks of contiguous packets can be identified from the 
        'counts' column by grouping the data and getting the first and 
        last indices - those indices are INCLUSIVE, so the last index is 
        the last valid packet in that group
        '''
        block_ranges = pd.DataFrame()
        block_ranges['blocks'] = dataframe.groupby('vblock_resets').apply(\
                                            lambda x:(x.index[0],x.index[-1]))
        block_ranges.index.name = 'vblock_resets'
        return dataframe,block_ranges
    def vector_analysis(self,frame):
        '''
        Analyse the vector numbers for contiguity, in a fashion similar to 
        above, just for vector numbers, not for reset counts.
        Also, 'valid' vector count increases are now +1 only.
        -The input dataframe should contain a contiguous block of vectors
        packets - (expects columns: 'reset' - and index:'packets','vectors') -
        which is achieved by utilising the other filtering and segregation
        functions in this class.
        --Returns dataframe which has the vector number as its index - this
        is achieved by dropping the 'packet' multiindex level. The vectors
        should all be contiguous - this is part of the analysis. The resets
        should also be monotonically (increasing) by either 0 or 1.
        '''
        dataframe = frame.copy()
        if dataframe.index.names != ['packet','vector']:
            raise Exception("Input Dataframe needs to have a multiindex with"
                            "level names 'packet' and 'vector'")
        dataframe.index = dataframe.index.droplevel('packet')
        vector_numbers = pd.Series(dataframe.index.values,
                                   index=dataframe.index.values)
        vdiff = vector_numbers-vector_numbers.shift(1)
        dataframe['contiguousness_change'] = (vdiff!=1)
        dataframe['vblock_vnumbers'] = dataframe['contiguousness_change'].\
                                                                      cumsum()
        '''
        Finally, blocks of contiguous packets can be identified from the 
        'counts' column by grouping the data and getting the first and 
        last indices - those indices are INCLUSIVE, so the last index is 
        the last valid packet in that group
        '''
        block_ranges = pd.DataFrame()
        block_ranges['blocks'] = dataframe.groupby('vblock_vnumbers').apply(\
                                            lambda x:(x.index[0],x.index[-1]))
        block_ranges.index.name = 'vblock_numbers'
        return dataframe,block_ranges
'''
header lengths
dds - 15
fgm science - 34
combined - 49 - should be first index of data 
since packet length includes fgm science header
packet length  - 34 should be last data index
'''        

'''
When combining half-vectors -> place result into ONLY the even dataframes.
They will have different indices, which may be very confusing, so that needs
to be considered throughout future filtering operations!!!
-> NOW, reconstructed vectors placed only in the even frames,
numbering of odd frames??

Need to make sure that the reconstructed half-vector lying between
two adjacent even & odd packets is removed, so as to avoid its duplication
in the final data!!!!

Index for the odd dataframe has been reconstructed in order to avoid a 
jump in vector numbers at packet transitions,since the half vector 
has been moved to the even dataframe

Only putting the joing half-vector into the even dataframe - is that wise,
or could it introduce some errors, if there are missing packets or otherwise
corrupted data?
'''

pd.options.display.expand_frame_repr=False
pd.options.display.max_rows=20
dump_date = datetime(2016,3,8)
sc = 3
ext = ExtData(sc,dump_date,'BS',dir=RAW)
packet_info1 = ext.packet_info
ext.read_data()

print "Before filtering (even),(odd)"
print ext.even.shape,
print ext.odd.shape
even1 = ext.even.copy()
odd1 = ext.odd.copy()
print "joining half vecs"

ext.join_half_vecs()

print "joined"
print ext.even.shape,
print ext.odd.shape,
print ext.evenodd.shape,
print ext.oddeven.shape

evenj = ext.even.copy()
oddj = ext.odd.copy()
packet_sizes_evenj = evenj.groupby(level=['packet']).size()
packet_sizes_evenj.name = 'even'
packet_sizes_oddj = oddj.groupby(level=['packet']).size()
packet_sizes_oddj.name = 'odd'
packet_sizesj = pd.concat((packet_sizes_evenj,packet_sizes_oddj),axis=1)

'''
now the packets need to be joined
----------------------------------------------------
-join up all packets in the two possible ways, ie. even first then odd,
or odd first then even, and then analyse this further
create -> two_series
create 'evenodd' chain of packets with even packet, then odd packet, etc...
create 'oddeven' chain of packets with odd packet, then even packet, etc...
analyse -> reset count contiguity
based on the analysis, define 'blocks' of valid data
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
-or, one could analyse every packet and see if the packet should be even or odd
ie. reverse the steps,
analyse -> reset count contiguity
        -> even/odd packet size (perhaps relative to other packet)
and then proceed from there -> 'combined'

pick odd/even packets based on this, and join them up correspondingly,
this will introduce missing packets at this stage, which will have to be
taken care of somehow.
Missing packets - packets that are not considered odd/even, and are therefore
not included
If an even packet is selected, but the following odd packet is not, then
that should mean that the odd packet is not good data, so the half vector at 
its end should not be usable either??
What to do with partial packets??
-This method could possibly be used to check whether the other method works
as intended, but ultimately the first method is the preffered one
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
reset count contiguity analysis
12-bit reset count (top 12-bits of the 16-bit HF counter)
Reset count increases every ~5.1522 seconds.
Spin periods range from ~ 3.9 to 4.4 seconds.
Top 12-bits of reset count increase every 16*5.1522 = ~ 81 to 82 seconds
So should see approx. 81.5/3.9 to 81.5/4.4 vectors per 12-bit reset count 
increase, ie. ~ 18 to 21 vectors (spins)!

So good 'elementary blocks' of 18 to 21 vectors can be identified by summing
the difference in reset counts for 22 vectors starting from the first vector
after an observed reset period. If there is a +1 increase in those 22 vectors,
it is a good piece of data.
BUT, this cannot be used to ascertain whether vectors at the start/end 
are usable, since those will almost certainly be shorter. It also does little
to help with the identification of problematic areas, with missing/wrong 
vectors, etc...

Compute reset count difference between current and next row,ie.
diff = df['reset'].diff()
first element of diff will be NaN here
then go through each row and 
'''

ext.two_series()
evenodd1 = ext.evenodd.copy()
oddeven1 = ext.oddeven.copy()

print "two series"
print ext.even.shape,
print ext.odd.shape,
print ext.evenodd.shape,
print ext.oddeven.shape

ext.even = ext.filter_data(ext.even)
ext.odd = ext.filter_data(ext.odd)
ext.evenodd = ext.filter_data(ext.evenodd)
ext.oddeven = ext.filter_data(ext.oddeven)

print "After filtering"
print ext.even.shape,
print ext.odd.shape,
print ext.evenodd.shape,
print ext.oddeven.shape

evenoddf = ext.evenodd.copy()
oddevenf = ext.oddeven.copy()
evenf = ext.even.copy()
oddf = ext.odd.copy()
packet_sizes_even = evenf.groupby(level=['packet']).size()
packet_sizes_even.name = 'even'
packet_sizes_odd = oddf.groupby(level=['packet']).size()
packet_sizes_odd.name = 'odd'
packet_sizesf = pd.concat((packet_sizes_even,packet_sizes_odd),axis=1)
packetinfo=ext.packet_info
removed = ext.removed_packets
removed_info = ext.removed_packets_info

#hex formatting of reset counts

packetinfo_hex = packetinfo.copy(deep=True)
hexify(packetinfo_hex,columns=['Reset Count'],inplace=True)
even_hex = evenf.copy(deep=True)
hexify(even_hex,columns=['reset'],inplace=True)
odd_hex = oddf.copy(deep=True)
hexify(odd_hex,columns=['reset'],inplace=True)
#print packet_info.groupby('Telemetry Mode').count()

ext.select_packets()
new_packetsizes=ext.packet_sizes.copy()

print "blocks"
print ext.blocks

vfilter_evenodd,vranges_evenodd = ext.vector_analysis(ext.evenodd)
rfilter_evenodd,rranges_evenodd = ext.reset_analysis(ext.evenodd)
vfilter_oddeven,vranges_oddeven = ext.vector_analysis(ext.oddeven)
rfilter_oddeven,rranges_oddeven = ext.reset_analysis(ext.oddeven)
'''
size calculation is based on the fact that the blocks start and end indices
are inclusive. They relate to the index of the 'evenodd' or 'oddeven' frame
passed into the analysis function (the 'vector' level (1) that is)
For the reset blocks analysis, it may happen that two vectors agree 
reset-wise, but are actually very far apart in a packet, or even multiple
packets apart. Simply taking the difference of the indices does not suffice
in that case, since that would also count all of the vectors that have been
filtered out in the data filter function. The function below circumvents this
accurately.
'''
min_length = 10 #at a min value of 2, lots of 'coincidental' vblocks are
                #still observed, so a higher value is recommended
#print "even_odd filteredvblocks, min_length="+str(min_length)
#print "vector analysis"
vranges_evenodd['size']=vranges_evenodd['blocks'].apply(
    lambda x:np.sum((ext.evenodd.index.get_level_values(1)>=x[0]) & 
                    (ext.evenodd.index.get_level_values(1)<=x[1])))
vranges_evenodd = vranges_evenodd[vranges_evenodd['size']>=min_length]
#print vranges_evenodd
#print ""
#print "reset analysis"
rranges_evenodd['size']=rranges_evenodd['blocks'].apply(
    lambda x:np.sum((ext.evenodd.index.get_level_values(1)>=x[0]) & 
                    (ext.evenodd.index.get_level_values(1)<=x[1])))
rranges_evenodd = rranges_evenodd[rranges_evenodd['size']>=min_length]
#print rranges_evenodd

#print "odd_even filteredvblocks, min_length="+str(min_length)
#print "vector analysis"
vranges_oddeven['size']=vranges_oddeven['blocks'].apply(
    lambda x:np.sum((ext.oddeven.index.get_level_values(1)>=x[0]) & 
                    (ext.oddeven.index.get_level_values(1)<=x[1])))
vranges_oddeven = vranges_oddeven[vranges_oddeven['size']>=min_length]
#print vranges_oddeven
#print ""
#print "reset analysis"
rranges_oddeven['size']=rranges_oddeven['blocks'].apply(
    lambda x:np.sum((ext.oddeven.index.get_level_values(1)>=x[0]) & 
                    (ext.oddeven.index.get_level_values(1)<=x[1])))
rranges_oddeven = rranges_oddeven[rranges_oddeven['size']>=min_length]
#print rranges_oddeven
'''
the size column really describes the number of vectors, since the start and end
indices are inclusive
'''
'''
what is left to do (for evenodd and oddeven separately, again) is to find
the intersection between the results for the vector analysis and the 
reset analysis. This is to guarantee that only vectors that were read
sequentially from the data, and also have valid reset count increases are
included.
Using sets is a very easy way of doing it, and is actually remarkably fast,
considering that one has to create the full list of indices first, then
take the intersection, and then sort the resulting set once again.
'''
block_data = [[vranges_evenodd,rranges_evenodd,'evenodd'],
              [vranges_oddeven,rranges_oddeven,'oddeven']]
intersections_dict = {'evenodd':[],'oddeven':[]}
for vranges,rranges,label in block_data:
    #the indices are INCLUSIVE
    for v_start,v_end in vranges['blocks']:
        v_indices = set(np.arange(v_start,v_end+1,1))
        for r_start,r_end in rranges['blocks']:
            r_indices = set(np.arange(r_start,r_end+1,1))
            intersection_ind = list(v_indices.intersection(r_indices))
            if intersection_ind:
                intersection_ind.sort()
                intersections_dict[label].append((intersection_ind[0],
                                                    intersection_ind[-1]))
evenodd_intersections = pd.Series(intersections_dict['evenodd'],name='evenodd')
oddeven_intersections = pd.Series(intersections_dict['oddeven'],name='oddeven')
evenodd_length = evenodd_intersections.shape[0]
multiindex_evenodd = pd.MultiIndex.from_arrays((['evenodd']*evenodd_length,
                                                range(evenodd_length)),
                                                names=['order','index'])
oddeven_length = oddeven_intersections.shape[0]
multiindex_oddeven = pd.MultiIndex.from_arrays((['oddeven']*oddeven_length,
                                                range(oddeven_length)),
                                                names=['ordering','index'])
intersections_evenodd = pd.DataFrame(evenodd_intersections)
intersections_evenodd.index = multiindex_evenodd
intersections_oddeven = pd.DataFrame(oddeven_intersections)
intersections_oddeven.index = multiindex_oddeven
intersections_evenodd.columns=['intersections']
intersections_oddeven.columns=['intersections']
intersections = pd.concat((intersections_evenodd,intersections_oddeven),axis=0)
intersections['size'] = intersections['intersections'].apply(
                                                        lambda x:(x[1]-x[0])+1)
'''
this way of calculating the size is alright now, since we are sure of the fact
that there are no gaps between the vectors (since the indices must have been
present at least partly within the vblocks ranges)
'''
'''
Now sort the intersections by size, and rename the block numbers (which is 
just the index) accordingly, so that the lowest index number corresponds to
the largest block!
'''
intersections.sort_values('size',ascending=False,inplace=True)
level0 = intersections.index.get_level_values(0)
level1 = range(1,intersections.shape[0]+1)
intersections.index = pd.MultiIndex.from_arrays((level0,level1),
                                                names=['order','block'])
print "Sorted Intersections"
print intersections
'''
Having determined the intersections between the different analysis methods,
the remaining overlaps have to be reduced to the elementary vectors, 
ie. duplicates removed
A naive solution would involve simply removing rows that share common values
across all columns - the problem with this is that some rows could potentially
contain the same column values, despite being physically different vectors!
Since valid vector starts and ends within packets are not likely to be aligned,
one would have to find a way to compare surrounding rows as well.
'''
def select_index_level_1(frame,start,end):
    '''
    inclusive selection on integer based multiindex level 1
    '''
    level_1 = frame.index.get_level_values(1)
    return frame.iloc[(level_1>=start) & (level_1<=end)]

'''
look at 2 selections
'''
'''
orderings = intersections.index.levels[0]
orderings_data = {'evenodd':ext.evenodd,'oddeven':ext.oddeven}
for ordering in orderings:
    if intersections.xs(ordering).shape[0]>1:
        print "ordering, looking at first 2"
        start1,end1 = intersections.xs((ordering,0))['intersections']
        start2,end2 = intersections.xs((ordering,1))['intersections']
        data1 = select_index_level_1(orderings_data[ordering],start1,end1)
        data2 = select_index_level_1(orderings_data[ordering],start2,end2)
        data1.reset_index(inplace=True)
        data2.reset_index(inplace=True)
        data1.columns = [entry+'1' for entry in data1.columns]
        data2.columns = [entry+'2' for entry in data2.columns]
        comparison = pd.concat((data1,data2),axis=1)
'''
'''
Approach problem by shifting vblocks and determining overlap points between
different vblocks by counting the rows that agree at different shifts

Shift different datasets until they match. At that point, remove all duplicated
rows from the smaller dataset. 
The data may overlap at multiple points if the data is weird, so we need a 
threshold to avoid falling for 'accidental matches' - however rare they might
be.
All remaining data is considered 'new' and added the the larger dataset
++++++++++++++++++
Actually this is highly superfluous, since we are already filtering the 
vblocks for a size larger than a certain threshold. Even if the threshold
were made to be quite small, it would require the resulting vectorblocks
to consist of vectors which have valid reset counts as a group,
AND occur contiguously in the Burst Science data file. That, coupled with
the condition for a duplicated row (ie. all columns must be the same) is 
probably more than sufficient for isolating duplicated values (that are
physical, and not just random)
'''
orderings_data = {'evenodd':ext.evenodd,'oddeven':ext.oddeven}
orderings = intersections.index.get_level_values('order')
blocks = intersections.index.get_level_values('block').values
boundaries = intersections['intersections'].values #array of (start,end)
dataframes = []
for (ordering,block,(start,end)) in zip(orderings,blocks,boundaries):
    data = select_index_level_1(orderings_data[ordering],start,end)
    packets = data.index.get_level_values(0)
    vectors = data.index.get_level_values(1)
    blockslevel = [block]*len(packets)
    multi = pd.MultiIndex.from_arrays((blockslevel,packets,vectors),
                                      names=['block','packet','vector'])
    data.index = multi
    dataframes.append(data)
if not dataframes:
    raise Exception("No data found!")
    
raw_combined_data = pd.concat((dataframes))
raw_combined_data['block'] = raw_combined_data.index.get_level_values(
                                                                'block')
'''
Data which stems from incomplete half vector information that has not
been filtered out before will have to be removed here. The only parts of
a vector that are not filtered beforehand this stage are the 
magnetic field values (x,y,z). If an invalid value sneeks in there while
reading the raw data, it remains undetected. One observed example of this
was a repeat copy of a vector, where the packet data started of with 0s in
such a way that the x-component was exactly 0. So this will be filtered
out here. Other cases may or may not be filtered out this way, but
if the is a problem that occurs at the start/end of packet blocks, then
the reset duplicate removal method described below should deal with that,
given that there are multiple copies of the data. Values that are 
exactly 0.0 may actually occur, so opting to rely on the reset filtering
alone is much better than filtering out those values.
'''
'''
This naive way of dropping duplicates should be refined, even though in
most cases, it will not make much difference, apart from slowing down
program execution. If this turns out to be a significant issue, 
the naive duplicate dropping can always be reinstated.
#combined_data.drop_duplicates(inplace=True)
'''
'''
More refined duplicate dropping will take into consideration the origin
of the vectors. By grouping together vectors that share the same reset
count, and opting to keep only those vectors from the block which has
more vectors at that reset in it, will allow for partial vectors to 
be recovered, if possible. That means that if for some reason, the 
first copy of the data (in the BS file) should not include a vector,
due to a corrupted packet, or missing half-vector, or a similar reason,
if the data is present again in a second copy, that second copy should be
preferred if there are more vectors present. Of course, such an
'extra' vector that may be present in a repeat copy would be included
with the naive duplicate removal - however, the only way of knowing the
order in which the vectors were measured is to look at the vector number
in the dataframe index - since this reflects the order in which they were
read from the raw data file. If one were to 'cherrypick' an additional
vector from a repeat copy, while discarding the remaining vectors from the
repeat copy only to combine this additional vector with the other vectors
from the original copy, that ordering would be lost, since the vector
numbers will not form a neat series anymore. Rather, that additional 
vector from the second repeat copy will always be placed last, since
the dataframe is sorted by reset first and then by the vector value.
This situation (or something similar, with other configurations of 
repeat copies) is probably very unlikely, but accounting for it anyway
is not a big problem. 
The size of the blocks involved will determine which vectors are to be 
kept when the number of vectors for one particular reset are identical.
'''
filtered = []
for key,data in raw_combined_data.groupby('reset'):
    data_blocks = np.unique(data.index.get_level_values('block'))
    nr_of_blocks = data_blocks.shape[0]
    if nr_of_blocks>1:
        '''
        as discussed above, take the vectors from the block which has 
        the most vectors at the selected reset count. If all the blocks
        have the same number of vectors, take the block with the lowest
        number (recall that the blocks were sorted by size earlier on
        and relabelled so that the lowest block-number corresponds to
        the largest block!)
        '''
        data_block_sizes = data.groupby('block').size().to_frame(
                                                            name='size')
        data_block_sizes['block'] = data_block_sizes.index.values
        data_block_sizes.sort_values(by=['size','block'],
                                     ascending=[False,True])
        filtered.append(data.xs(data_block_sizes['block'].iloc[0],
                                level='block',drop_level=False))
    else:
        filtered.append(data)
combined_data = pd.concat((filtered))  
duplicated_indices = combined_data.index.duplicated()
if np.sum(duplicated_indices):
    raise Exception("This should never happen after dropping duplicates!")
combined_data['vector']=combined_data.index.get_level_values('vector')
combined_data.sort_values(['reset','vector'],ascending=True,inplace=True)
print "combined data"
print combined_data
def data_processing(combined_data,plot=True,title=False,copy=True,log_mag=False):
    '''
    Converting engineering units to nT
    Tim is still working on 'what' the scaling factors should be?
    Calibration still needs to be applied, this will be done at a later
    point in time before the data is fed into the dp software
    '''
    if copy:
        combined_data = combined_data.copy()
    combined_data['x'] = combined_data['x'].apply(
                                        lambda x: x-65536 if x>32767 else x)
    combined_data['y'] = combined_data['y'].apply(
                                        lambda x: x-65536 if x>32767 else x)
    combined_data['z'] = combined_data['z'].apply(
                                        lambda x: x-65536 if x>32767 else x)
    
    combined_data['x']=combined_data['x'].values/  \
np.power(2,((np.ones(combined_data.shape[0],dtype=np.float64)*12)-(combined_data['range'].values)*2))
    combined_data['y']=combined_data['y'].values/  \
np.power(2,((np.ones(combined_data.shape[0],dtype=np.float64)*12)-(combined_data['range'].values)*2))
    combined_data['z']=combined_data['z'].values/  \
np.power(2,((np.ones(combined_data.shape[0],dtype=np.float64)*12)-(combined_data['range'].values)*2))
    
    combined_data['mag']=np.linalg.norm(combined_data[['x','y','z']],axis=1)
    if title:
        combined_data.plot(y=['x','y','z','mag'],title=title)
    elif plot:
        combined_data.plot(y=['x','y','z','mag'])
    if log_mag:
        plt.figure()
        plt.plot(range(len(combined_data)),combined_data['mag'],c='k')
        plt.yscale('log')
#data_processing(combined_data,title='before')
'''
Now, need to look at timing!!
Spin periods at around 3.9 to 4.3 seconds
Reset pulse every ~5.152220 seconds, 'more' accurate value can be achieved by 
comparing NS packet SCET times, but for ext mode, the HF clock is more 
important (used to ascertain spin periods, for example), 
which should be stable at 4096 Hz.
Reset count wraps around every 93.8 Hours or so, which should be much much 
longer than one extended mode period should ever be.
HF clock count,however, rolls overs every 65536/4096 seconds = 16.0 seconds

Last NS time can be regarded as the packet HF count and corresponding packet
SCET time of the last Normal Science packet before extended mode.
Can determine the time of the first Normal Science vector by looking at the
SCET time and the HF clock count of the first NS packet after ext mode,
and then using the 1st 1ry vector HF count in the FGM science header to
extrapolate back towards the first vector.

Based on the reset count of the NS packets before and after ext mode (only one
should be needed in practice) it can be determined whether the reset counter
should wrap around or not (assuming extended modes are not longer than a
couple of days)

The time between the vectors will stay constant throughout extended mode -
the average spin period during that time, which should ideally be 
calculated from the HF clock counts for the most recent sun pulses recorded
in the NS packets either side of ext mode.

                |last NS| ext mode |first NS|
                   |                 | 
reset----+----+----+---.............-+----+----+----+----+----+----+

spin ---+---+---+---+--.............+---+---+---+---+---+---+---+---+---+---+
                |   |               | 
      most recent  extrapolated    most recent
There are n resets between the last NS and first NS packets, ie. reset count
increases by n
But there are NOT integer spins between two two packets

Example - ExtMode on 4th January 2016, Dump on 6th Jan
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
Approx. Duration from SCCH - 4:59:54 to 22:30:00 = 63006 s - 17.502 hours
reset period (from NS on 4th) = 5.1522208 s +- 5.45e-06 s
spin period (from NS on 4th) =  4.2606671 s +- 1.22e-04 s
(could be improved by taking MSA dump data on that day as well)
last NS packet:
    packet reset count = 0xE2AC
    most recent sun pulse HF count: 0x5BF4
first NS packet:
    packet reset count = 0x1279 (could be 0x1276, but that value is not
        read correctly by the header reading module (reset count shown as 0),
        and it is marked as corrupt in the header, plus an anomalous packet
        afterwards...)
    most recent sun pulse HF count (for 0x1279 packet): 0xAE13
    
last EXT Mode Reset (top 12 bits): 295 (0x127) (+0x1000 or 4096, wraps-around)
                                    = 0x1127 or 4391
first EXT Mode Reset (top 12 bits):3626(0xE2A)

between these two sun pulse counts, an integer number of spin must have
occurred, but the HF clock counter wraps around every 16 seconds!

Get the time between the two packets from the packet reset counts (be wary of
wrap-around)-> (0x1279(+0x10000 since wrapped around) - 0xE2AC) = 12237(0x2FCD)
                *5.1522208 = 63047.7259 s = 17.513 hours
            That is slightly longer than the estimate from the SCCH file,
            however, note that some corrupt normal science packets were
            'skipped', which is questionable. If 3 packets were ignored at the
            start of NS, then that equates to around 0.0043 hours, or almost
            half the discrepancy. If we include time delays at the end and the
            start for some other reason, then the disparity becomes even
            smaller. It seems that NS packets in the viccinity of ext mode
            are faulty, which can extend to several packets around the border.
(We can convet this to HF clock counts -> time*4096 = 147450106.42944 HF counts
Taking the remainder -> 147450106.42944%(2**16)=59642.42943999171
                     -> round(59642.42943999171) = 59642 )
Taking the difference of the SCET times of the NS packets at 0xE2AC and 0x1279
yields: 63027.118545 s - 20 s shorter than reset count difference value,
                         but still longer than the SCCH time estimate - since
                         3-4 packets were skipped (see above).
                        
                         *Discrepancy to the reset count difference time is 
                         3.9997 reset periods, so exactly 4 - what went wrong
                         here?
Looking at the FULL caa file, the last vector before ext mode occurred at
04:59:53.5,
and the first vector after ext mode at
22:30:20.6. 
20.6 seconds is 4*5.15, - 4 reset periods - same discrepancy as above!
                         
We know the most recent sun pulse HF counter value for both packets.
We also know the one before that (is that accurate/useful for error checking?)

s x spin_period = time_difference(between most recent sun pulse for NS packets)
s is the number of spins in ext mode, needs to be integer.

time_difference = reset_time_diff + (dt1-dt2),
    where dt1 is the time difference between the last NS reset and its most
    recent sun pulse and similarly for dt2 (first NS packet)

dt1 = 34866-23540 = 11326 -> /4096. -> 2.76513671875 s
dt2 = 47677-44563 = 3114  -> /4096. -> 0.76025390625 s
dt1-dt2 = 2.0048828125 s - of course, this is vanishingly small compared to
            the reset_time_diff
            
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

Originally, the spin period was to be estimated using the time difference 
between NS packets at the border of extended mode (thus the calculations
in the example above). However, since it seems to be the case that some NS
packets at the border to extended mode can be corrupt, a more robust way of
estimating the spin period would probably be to average the spin periods
obtained from looking at the sun pulse HF clock times in the NS and BS packets
on the day of extended mode as well as one the days surrounding extended mode.
(Probably 1 day before, 1 day after).

In order to ascertain when the extended mode occurred the commanding history
can be used as a rough indicator, although when NS packets are available, 
matching their reset count to the reset counts observed in the Extended Mode
packets will always yield better accuracy, especially during convoluted time
periods. The NS packet which has a reset count that is lower than the low


--The feasability of a wrap-around of the reset counter shall be assessed very
crudely using the reset counts of all extended mode vectors. If there are valid
vectors with reset counts above 3000, (so that the real reset count is
3000*16) then any disjoint group with a mean reset count under 1000 shall
have their reset counts increased by 4096. 1000*16 reset counts takes 
approx. 23 hours to complete, so this should be valid for pretty much any
situation. 
The alternative is to rely on the most recent spacecraft command history
or matching of the lowest reset in the extended mode vectors. But in the case
where the reset counter wraps around, this would give a very inaccurate 
value if we were to naively assume that extended mode started at a reset count
of 0. So here, we would have to look at any disparity in the reset counts
across the extended mode vectors again, just as above - unless we want to 
rely solely on the commanding.
'''
'''
reset wrap around analysis and if needed, adjustment
'''
blockgroups = combined_data.groupby('block')
mean_resets = blockgroups['reset'].mean()
if max(mean_resets)>3000:
    '''
    Reset counter overflow 'might' have occurred here, so any blocks containing
    a vector with a reset counter value (top 12 bits) under 1050 
    (roughly 24 hours) will have their reset counter values increased by
    4096.
    '''
    min_resets = blockgroups['reset'].min()
    increase_blocks = min_resets[min_resets<1050].index.get_level_values(
                                                                'block').values
    increase_mask = np.in1d(combined_data.index.get_level_values(
                            'block').values,increase_blocks)
    combined_data.ix[increase_mask,'reset'] += 4096
    
combined_data.sort_values(['reset','vector'],ascending=True,inplace=True)
data_processing(combined_data,title='after',copy=False)

'''
checking the number of vectors per (12 top bits) of reset counter, 
in order to check for anomalies.
'''
sizes = combined_data.groupby('reset').size()
plt.figure()
plt.scatter(sizes.index.values,sizes.values,s=120)
plt.title('Number of vectors per (12 top bits) of reset counter\n'
            'dump date:'+dump_date.isoformat()+' sc:'+str(sc))
plt.xlabel('top 12 bits of reset counter')
plt.ylabel('Number of vectors')
plt.minorticks_on()


import cPickle as pickle

picklefile = pickledir+'extdata.pickle'
with open(picklefile,'wb') as f:
    pickle.dump(combined_data,f,protocol=2)

picklefile = pickledir+'packetinfo.pickle'
with open(picklefile,'wb') as f:
    pickle.dump(ext.packet_info,f,protocol=2)

picklefile = pickledir+'sc.pickle'
with open(picklefile,'wb') as f:
    pickle.dump(sc,f)

picklefile = pickledir+'dumpdate.pickle'
with open(picklefile,'wb') as f:
    pickle.dump(dump_date,f)
    
import timing