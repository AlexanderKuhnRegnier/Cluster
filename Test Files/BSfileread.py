import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import os

class extdata:
    #packet header ID
    ID={'SC1BS':38,'SC2BS':78,'SC3BS':118,'SC4BS':158,
        'SC1NS':31,'SC2NS':71,'SC3NS':111,'SC4NS':151}
    telem_mode={12:'Normal Mode',13:'Burst Science',14:'Extended Mode',
                15:'MSA Dump'}
    def __init__(self,filename):
        self.fgm_data = {'Telemetry Mode':[],'First 1ry HF':[],
                         'First 2ry HF':[],'Reset Count':[]}
        self.dds_data = {'SCET':[],'Header ID':[],'Packet Length':[],
                         'sc ID':[]}
        self.packet_offset = 0
        self.data = []
        self.packet_info = pd.DataFrame()
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
        df = pd.DataFrame(data_dict,columns = ['range','reset','sensor',
                                                       'x','y','z'])
        return df
    def read_odd(self,data):
        data_dict = {'x':[],'y':[],'z':[],'sensor':[],'range':[],'reset':[]}
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
        df = pd.DataFrame(data_dict,columns = ['range','reset','sensor',
                                                       'x','y','z'])
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
        sumcheck_code_failure =          status_data>>15
        incorrect_vectors_sampled =     (status_data & 0b0010000000000000)>>13
        possible_corrupt_science_data = (status_data & 0b0001000000000000)>>12
        dpu_test_sequence_number =      (status_data & 0b0000111000000000)>>9
        msa_data_filtered =             (status_data & 0b0000000100000000)>>8
        cal_seq_number =                (status_data & 0b0000000011000000)>>6
        mem_dump_in_progress =          (status_data & 0b0000000000100000)>>5
        code_patch_in_progress =        (status_data & 0b0000000000010000)>>4
        telemetry_mode =                 status_data & 0b0000000000001111
        packet_start_hf = extdata.read_bytes([2,3],science_header)
        prev_sun_pulse_hf = extdata.read_bytes([4,5],science_header)
        most_recent_sun_pulse_hf = extdata.read_bytes([6,7],science_header)
        first_1ry_hf = extdata.read_bytes([8,9],science_header)
        first_2ry_hf = extdata.read_bytes([10,11],science_header)
        reset_count = extdata.read_bytes([12,13],science_header)
        tel_mode = extdata.telem_mode[telemetry_mode]
        self.fgm_data['Telemetry Mode'].append(tel_mode)
        self.fgm_data['First 1ry HF'].append(first_1ry_hf)
        self.fgm_data['First 2ry HF'].append(first_2ry_hf)
        self.fgm_data['Reset Count'].append(reset_count)
        return 1
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
    def read_data(self):
        even = []
        odd = []
        for i in range(20000):#arbitrary limit
            dds_data = self.read_dds(self.data[self.packet_offset:
                                                self.packet_offset+15])
            self.packet_offset+=15
            fgm_data = self.read_fgm_science(self.data[self.packet_offset:
                                                self.packet_offset+34])
            self.packet_offset+=34 #needs to be subtracted from packet length!
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
        packet_str = lambda n:'packet'+format(n,'03d')
        self.fgm_data.update(self.dds_data)
        number_of_packets = len(self.fgm_data[self.fgm_data.keys()[0]])
        
        if number_of_packets != len(even) or number_of_packets != len(odd):
            raise Exception("Packet number mismatch between header info"
                            " and number of read packets")
                            
        self.packet_info = pd.DataFrame(self.fgm_data,index=[packet_str(i) for
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
            top_level.extend([packet_str(packet_count)]*length)
            packet_count += 1    
        bottom_level=range(1,self.odd.shape[0]+1)            
            
        multiindex=pd.MultiIndex.from_arrays([top_level,bottom_level],
                                             names=['packet','vector'])
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

    def filter_data(self):
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
        #####even######
        mask = ~(self.even.apply(lambda x:np.all(x==invalid_row_data1),axis=1,
                                    raw=True).values)
        mask = mask | (~self.even.apply(lambda x:np.all(x==invalid_row_data2),
                                       axis=1,raw=True).values)
        self.even = self.even[mask]
        #####odd#######
        mask = ~(self.odd.apply(lambda x:np.all(x==invalid_row_data1),axis=1,
                                    raw=True).values)
        mask = mask | (~self.odd.apply(lambda x:np.all(x==invalid_row_data2),
                                       axis=1,raw=True).values)
        self.odd = self.odd[mask]       
        
        '''
        filter out entries with all 0's in them
        '''
        #####even######
        mask = ~(self.even.apply(lambda x:np.all(x==0),axis=1,
                                    raw=True).values)
        self.even = self.even[mask]
        #####odd#######
        mask = ~(self.odd.apply(lambda x:np.all(x==0),axis=1,
                                    raw=True).values)
        self.odd = self.odd[mask]
        '''
        filter out invalid ranges, ie range<2 (range 7 is technically allowed)
        '''        
        #####even######
        mask = self.even['range']>1
        self.even = self.even[mask]
        #####odd#######
        mask = self.odd['range']>1
        self.odd = self.odd[mask]   
        '''
        filter out the inboard sensor, since this is never used 
        -- is this essential, since it is technically possible to have
        the inboard sensor??
        '''
        #####even######
        mask = self.even['sensor']==0
        self.even = self.even[mask]
        #####odd#######
        mask = self.odd['sensor']==0
        self.odd = self.odd[mask]       
        
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

'''
header lengths
dds - 15
fgm science - 34
combined - 49 - should be first index of data 
since packet length includes fgm science header
packet length  - 34 should be last data index
'''        

RAW = 'C:/Users/ahfku/Documents/Magnetometer/clusterdata/'
#RAW = 'Z:/data/raw/'
pd.options.display.expand_frame_repr=False
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
print "Before filtering"
print ext.even.shape,
print ext.odd.shape
even1 = ext.even
odd1 = ext.odd
ext.filter_data()
print "After filtering"
print ext.even.shape,
print ext.odd.shape
even = ext.even
odd = ext.odd
packet_sizes_even = even.groupby(level=['packet']).size()
packet_sizes_even.name = 'even'
packet_sizes_odd = odd.groupby(level=['packet']).size()
packet_sizes_odd.name = 'odd'
packet_sizes = pd.concat((packet_sizes_even,packet_sizes_odd),axis=1)
packetinfo=ext.packet_info
removed = ext.removed_packets
#packet_info['Reset Count'] = packet_info['Reset Count'].apply(hex)
#print packet_info
#print packet_info.groupby('Telemetry Mode').count()