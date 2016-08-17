import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import os

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

class extdata:
    #packet header ID
    ID={'SC1BS':38,'SC2BS':78,'SC3BS':118,'SC4BS':158,
        'SC1NS':31,'SC2NS':71,'SC3NS':111,'SC4NS':151}
    telem_mode={12:'Normal Mode',13:'Burst Science',14:'Extended Mode',
                15:'MSA Dump'}
    def __init__(self,filename):
        '''
        self.fgm_data = {'Telemetry Mode':[],'First 1ry HF':[],
                         'First 2ry HF':[],'Reset Count':[]}
        '''
        self.fgm_data = {'Telemetry Mode':[],'Reset Count':[]}
        self.dds_data = {'SCET':[],'Header ID':[],'Packet Length':[],
                         'sc ID':[]}
        self.packet_offset = 0
        self.data = []
        self.packet_info = pd.DataFrame()
        self.evenodd = pd.DataFrame()
        self.oddeven = pd.DataFrame()
        self.combined = pd.DataFrame()
        self.full_packets = np.array([])
        self.evenodd=pd.DataFrame()
        self.oddeven = pd.DataFrame()
        with open(filename,'rb') as f:
            self.data = f.read()
        if not self.data:
            raise Exception("Could not read file:"+filename)
    
    @staticmethod
    def shift_left(num,left):
        return num<<left
    @staticmethod
    def read_byte(index,data):
        return ord(data[index])                
    @staticmethod
    def read_bytes(indices,line):
        values=[]
        for i in indices:
            leftshift = (max(indices)-i)*8
            values.append(extdata.shift_left(ord(line[i]),leftshift))
        return sum(values)
    def read_even(self,data):
        data_dict = {'x':[],'y':[],'z':[],'sensor':[],'range':[],'reset':[]}
        for offset in range(0,444*8,8):
            data_dict['x'].append(extdata.read_bytes([offset,offset+1],data))
            data_dict['y'].append(extdata.read_bytes([offset+2,offset+3],data))
            data_dict['z'].append(extdata.read_bytes([offset+4,offset+5],data))
            last_bytes = extdata.read_bytes([offset+6,offset+7],data)
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
        data_dict['x'].append(extdata.read_bytes([offset,offset+1],data))
        data_dict['y'].append(extdata.read_bytes([offset+2,offset+3],data))
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
        data_dict['z'].append(extdata.read_bytes([0,1],data))
        last_bytes = extdata.read_bytes([2,3],data)
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
            data_dict['x'].append(extdata.read_bytes([offset,offset+1],data))
            data_dict['y'].append(extdata.read_bytes([offset+2,offset+3],data))
            data_dict['z'].append(extdata.read_bytes([offset+4,offset+5],data))
            last_bytes = extdata.read_bytes([offset+6,offset+7],data)
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
    def read_dds(self,dds_data):
        if len(dds_data) != 15:
            print "wrong length:",len(dds_data)
            return 0  
        day_indices = [0,1]
        days = extdata.read_bytes(day_indices,dds_data)
        ms_indices = [2,3,4,5]
        ms = extdata.read_bytes(ms_indices,dds_data)
        us_indices = [6,7]
        us = extdata.read_bytes(us_indices,dds_data)
        '''
        print days,(days/365)+1958
        print 'ms,      s,    mins,hours'
        print ms,ms/1000, (ms/1000)/60,((ms/1000)/60)/60
        '''
        date1=datetime(1958,1,1)
        dt = timedelta(days=days,seconds=0,milliseconds=ms,microseconds=us)
        SCET = date1+dt
        self.dds_data['SCET'].append(SCET)
        header_ID = ord(dds_data[8])
        self.dds_data['Header ID'].append(header_ID)
        '''
        compare with ext.data.ID dictionary!!!
        -also based on sc_ID below
        '''
        packet_length = extdata.read_bytes([9,10,11],dds_data)
        self.dds_data['Packet Length'].append(packet_length)
        #print "packet_length",packet_length
        sc_ID = extdata.read_byte(12,dds_data)>>4  
        self.dds_data['sc ID'].append(sc_ID)
        return 1
    def read_fgm_science(self,science_header):
        if len(science_header) != 34:
            print "wrong length:",len(science_header)
            return 0
        status_data = extdata.read_bytes([0,1],science_header)
        '''
        #this is only useful for normal science data!
        sumcheck_code_failure =          status_data>>15
        incorrect_vectors_sampled =     (status_data & 0b0010000000000000)>>13
        possible_corrupt_science_data = (status_data & 0b0001000000000000)>>12
        dpu_test_sequence_number =      (status_data & 0b0000111000000000)>>9
        msa_data_filtered =             (status_data & 0b0000000100000000)>>8
        cal_seq_number =                (status_data & 0b0000000011000000)>>6
        mem_dump_in_progress =          (status_data & 0b0000000000100000)>>5
        code_patch_in_progress =        (status_data & 0b0000000000010000)>>4
        packet_start_hf = extdata.read_bytes([2,3],science_header)
        prev_sun_pulse_hf = extdata.read_bytes([4,5],science_header)
        most_recent_sun_pulse_hf = extdata.read_bytes([6,7],science_header)
        '''
        telemetry_mode =                 status_data & 0b0000000000001111
        '''
        #again, useful for normal science data
        #if these need to be used, need to include these labels in the
        #dict creation in __init__!
        first_1ry_hf = extdata.read_bytes([8,9],science_header)
        first_2ry_hf = extdata.read_bytes([10,11],science_header)
        self.fgm_data['First 1ry HF'].append(first_1ry_hf)
        self.fgm_data['First 2ry HF'].append(first_2ry_hf)
        '''
        reset_count = extdata.read_bytes([12,13],science_header)
        tel_mode = extdata.telem_mode[telemetry_mode]
        self.fgm_data['Telemetry Mode'].append(tel_mode)
        self.fgm_data['Reset Count'].append(reset_count)
        '''
        bits 14 - 33 not used
        '''
        #print "fgm science"
        '''
        print sumcheck_code_failure
        print incorrect_vectors_sampled
        print possible_corrupt_science_data
        print dpu_test_sequence_number
        print msa_data_filtered
        print cal_seq_number
        print mem_dump_in_progress
        print code_patch_in_progress
        
        print telemetry_mode,extdata.telem_mode[telemetry_mode]
        print packet_start_hf
        print prev_sun_pulse_hf
        print most_recent_sun_pulse_hf
        print first_1ry_hf
        print first_2ry_hf
        print reset_count
        '''
        return 1
    def read_data(self):
        even = []
        odd = []
        for i in range(20000):#arbitrary limit to the number of packets
            dds_data = self.read_dds(self.data[self.packet_offset:
                                                self.packet_offset+15])
            self.packet_offset+=15
            fgm_data = self.read_fgm_science(self.data[self.packet_offset:
                                                self.packet_offset+34])
            self.packet_offset+=34  #needs to be subtracted from packet length
                                    #later, since packet lenght includes the
                                    #fgm header size!
            if not dds_data or not fgm_data:
                break
            else:
                #print "reading data"
                vector_data_length = self.dds_data['Packet Length'][-1]-34
                even.append(self.read_even(self.data[self.packet_offset:
                                        self.packet_offset+vector_data_length]))
                odd.append(self.read_odd(self.data[self.packet_offset:
                                        self.packet_offset+vector_data_length]))
                self.packet_offset+=vector_data_length
        '''
        changes fgm data dict inplace - acceptable?
        '''
        self.fgm_data.update(self.dds_data)
        number_of_packets = len(self.fgm_data[self.fgm_data.keys()[0]])
        
        if number_of_packets != len(even) or number_of_packets != len(odd):
            raise Exception("Packet number mismatch between header info"
                            " and number of read packets")
        self.packet_info = pd.DataFrame(self.fgm_data,index=[i for
                                            i in range(1,number_of_packets+1)])
        self.even = pd.concat((even))
        self.odd = pd.concat((odd))
        if self.even.shape != self.odd.shape:
            raise Exception("Even and Odd shapes don't mach, should contain"
                            "the same number of vectors at this point!")
        top_level = []
        packet_count = 1
        for packeto,packete in zip(odd,even):
            if packete.shape != packeto.shape:
                raise Exception("Unequal number of vectors in packet nr:"+
                                    str(packet_count))
            length = packete.shape[0]
            top_level.extend([packet_count]*length)
            packet_count += 1    
        bottom_level=range(0,self.odd.shape[0])            
        multiindex=pd.MultiIndex.from_arrays([top_level,bottom_level],
                                             names=['packet','index'])
        self.even.index=multiindex
        self.odd.index=multiindex
        '''
        filter out non-MSA dump data
        '''
        packet_mask = self.packet_info['Telemetry Mode'] == 'MSA Dump'
        self.removed_packets = self.packet_info[~packet_mask].index.values
        self.packet_info = self.packet_info[packet_mask]

        index_vals = self.even.index.get_level_values('packet').values
        maski = np.array([False]*index_vals.shape[0],dtype=bool)        
        for removed in self.removed_packets:
            maski = maski | (index_vals==removed)
        mask = ~maski
        self.even = self.even[mask]

        index_vals = self.odd.index.get_level_values('packet').values
        maski = np.array([False]*index_vals.shape[0],dtype=bool)        
        for removed in self.removed_packets:
            maski = maski | (index_vals==removed)
        mask = ~maski
        self.odd = self.odd[mask]    
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
        mask = ~(frame.apply(lambda x:np.all(x==invalid_row_data1),axis=1,
                                    raw=True).values)
        mask = mask | (~frame.apply(lambda x:np.all(x==invalid_row_data2),
                                       axis=1,raw=True).values)
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
hex_format = lambda i:'{:x}'.format(i).upper()
#RAW = 'C:/Users/ahfku/Documents/Magnetometer/clusterdata/'#home pc
RAW = 'Z:/data/raw/' #cluster alsvid server
pd.options.display.expand_frame_repr=False
pd.options.display.max_rows=20
Year= '2016'
year='16'
month = '01'
day='03'
sc = '1'
version = 'B'
BSfile = RAW+Year+'/'+month+'/'+'C'+sc+'_'+year+month+day+'_'+version+'.BS'
print BSfile
ext = extdata(BSfile)
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

#hex formatting of reset counts

packetinfo_hex = packetinfo.copy(deep=True)
packetinfo_hex['Reset Count'] = packetinfo_hex['Reset Count'].apply(hex_format)
even_hex = evenf.copy(deep=True)
even_hex['reset']=even_hex['reset'].apply(hex_format)
odd_hex = oddf.copy(deep=True)
odd_hex['reset']=odd_hex['reset'].apply(hex_format)
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
min_length = 5  #at a min value of 2, lots of 'coincidental' vblocks are
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
print "Intersections"
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
blocks = intersections.shape[0] #number of blocks to reduce
assert blocks == len(orderings),("Different orderings, and number of "
                                    "intersections should match")
boundaries = intersections['intersections'].values #array of (start,end)
dataframes = []
for (i,(start,end)) in zip(range(blocks),boundaries):
    data = select_index_level_1(orderings_data[orderings[i]],start,end)
    packets = data.index.get_level_values(0)
    vectors = data.index.get_level_values(1)
    blocks = [i]*len(packets)
    multi = pd.MultiIndex.from_arrays((blocks,packets,vectors),
                                      names=['blocks','packets','vectors'])
    data.index = multi
    dataframes.append(data)

combined_data = pd.concat((dataframes))
combined_data.drop_duplicates(inplace=True)
'''
some rough and ready processing, bear in mind that the data still needs to be
scaled from engineering units to nT, the range is important for that
Tim is still working on 'what' the scaling factors should be?
'''
combined_data['x'] = combined_data['x'].apply(lambda x: x-65536 if x>32767 else x)
combined_data['y'] = combined_data['y'].apply(lambda x: x-65536 if x>32767 else x)
combined_data['z'] = combined_data['z'].apply(lambda x: x-65536 if x>32767 else x)
combined_data['mag']=np.linalg.norm(combined_data[['x','y','z']],axis=1)