import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from collections import OrderedDict as orddict
class RawDataHeader:
    #packet header ID
    HF_freq = 4096.
    HF_period = 1/HF_freq
    Header_ID_value={'SC1BS':38,'SC2BS':78,'SC3BS':118,'SC4BS':158,
        'SC1NS':31,'SC2NS':71,'SC3NS':111,'SC4NS':151}
    Header_ID=dict([(value,key) for key,value in Header_ID_value.iteritems()])
    telem_mode={12:'Normal Mode',13:'Burst Science',14:'Extended Mode',
                15:'MSA Dump'}
    groundstation={0:'Unknown',1:'Vilspa 1',2:'Vilspa 2',3:'Kiruna',4:'Perth',
                   5:'Kourou',6:'Malindi',7:'Redu',8:'Canberra',
                   9:'Reference Station',15:'N/A'}
    normal_mode_names = ['ns','normal mode','normal science','nm']
    burst_mode_names = ['bs','burst mode','burst science']
    mode_dict = dict([(label,'NS') for label in normal_mode_names])
    mode_dict.update(dict([(label,'BS') for label in burst_mode_names]))
    def __init__(self,sc,dt,mode,version='B',dir='Z:/data/raw/'):
        version = version.upper()
        mode = mode.lower()
        if version not in ['A','B','K']:
            raise Exception("Version must be one of 'A','B' or 'K'")
        if mode not in RawDataHeader.mode_dict.keys():
            raise Exception("Please select either 'NS' or 'BS'")
        if sc not in [1,2,3,4]:
            raise Exception("Select a valid spacecraft (1,2,3,4)")
        Year,year,month,day = map(int,dt.strftime("%Y,%y,%m,%d").split(','))
        if Year<2000:
            raise Exception("Need to select a year after (or on) 2000")
        directory = dir+'{0:4d}/{1:02d}/'.format(Year,month)
        file = 'C{0:1d}_{1:02d}{2:02d}{3:02d}_{4:s}.{5:s}'.format(
                    sc,year,month,day,version,RawDataHeader.mode_dict[mode])
        filepath = directory+file
        self.fgm_data = orddict([
                                 ('Telemetry Mode',[]),
                                 ('Reset Count',[]),
                                 ('Packet Start HF',[]),
                                 ('Previous Sun Pulse',[]),
                                 ('Most Recent Sun Pulse',[]),
                                 ('First 1ry HF',[]),
                                 ('First 2ry HF',[]),
                                 ('Sumcheck code failure',[]),
                                 ('Incorrect vectors sampled',[]),
                                 ('Possible currupt science data',[]),
                                 ('DPU test sequence number',[]),
                                 ('MSA data filtered',[]),
                                 ('Calibration sequence number',[]),
                                 ('Memory Dump in Progress',[]),
                                 ('Code Patch in Progress',[])])
        self.dds_data = orddict([
                                ('SCET',[]),
                                ('Header ID',[]),
                                ('sc ID',[]),
                                ('Packet Length',[]),
                                ('Groundstation ID',[])])
        self.packet_offset = 0
        self.data = []
        self.packet_info = pd.DataFrame()
        self.evenodd = pd.DataFrame()
        self.oddeven = pd.DataFrame()
        self.combined = pd.DataFrame()
        self.full_packets = np.array([])
        self.evenodd=pd.DataFrame()
        self.oddeven = pd.DataFrame()
        self.blocks = pd.DataFrame()
        '''
        Exceptions should probably be handled differently for the final code,
        since these are not really fatal errors, unless previous checking is
        done.
        '''
        try:
            with open(filepath,'rb') as f:
                self.data = f.read()
        except IOError:
            raise Exception("Could not open file:"+filepath)
        if not self.data:
            raise Exception("Could not read file:"+filepath)
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
            values.append(RawDataHeader.shift_left(ord(line[i]),leftshift))
        return sum(values)
    def read_dds(self,dds_data):
        if len(dds_data) != 15:
            return 0  
        day_indices = [0,1]
        days = RawDataHeader.read_bytes(day_indices,dds_data)
        ms_indices = [2,3,4,5]
        ms = RawDataHeader.read_bytes(ms_indices,dds_data)
        us_indices = [6,7]
        us = RawDataHeader.read_bytes(us_indices,dds_data)
        date1=datetime(1958,1,1)
        dt = timedelta(days=days,seconds=0,milliseconds=ms,microseconds=us)
        SCET = date1+dt
        self.dds_data['SCET'].append(SCET)
        header_ID = ord(dds_data[8])
        self.dds_data['Header ID'].append(RawDataHeader.Header_ID[header_ID])
        packet_length = RawDataHeader.read_bytes([9,10,11],dds_data)
        self.dds_data['Packet Length'].append(packet_length)
        #print "packet_length",packet_length
        sc_ID = RawDataHeader.read_byte(12,dds_data)>>4  
        self.dds_data['sc ID'].append(sc_ID)
        ground_ID = RawDataHeader.read_byte(12,dds_data) & 0b1111
        self.dds_data['Groundstation ID'].append(
                                              RawDataHeader.groundstation[ground_ID])
        return 1
    def read_fgm_science(self,science_header):
        if len(science_header) != 34:
            return 0
        status_data = RawDataHeader.read_bytes([0,1],science_header)
        sumcheck_code_failure =          status_data>>15
        incorrect_vectors_sampled =     (status_data & 0b0010000000000000)>>13
        possible_corrupt_science_data = (status_data & 0b0001000000000000)>>12
        dpu_test_sequence_number =      (status_data & 0b0000111000000000)>>9
        msa_data_filtered =             (status_data & 0b0000000100000000)>>8
        cal_seq_number =                (status_data & 0b0000000011000000)>>6
        mem_dump_in_progress =          (status_data & 0b0000000000100000)>>5
        code_patch_in_progress =        (status_data & 0b0000000000010000)>>4
        packet_start_hf = RawDataHeader.read_bytes([2,3],science_header)
        prev_sun_pulse_hf = RawDataHeader.read_bytes([4,5],science_header)
        most_recent_sun_pulse_hf = RawDataHeader.read_bytes([6,7],science_header)
        telemetry_mode =                 status_data & 0b0000000000001111
        tel_mode = RawDataHeader.telem_mode[telemetry_mode]
        self.fgm_data['Telemetry Mode'].append(tel_mode)
        self.fgm_data['Previous Sun Pulse'].append(prev_sun_pulse_hf)
        self.fgm_data['Most Recent Sun Pulse'].append(most_recent_sun_pulse_hf)
        self.fgm_data['Sumcheck code failure'].append(sumcheck_code_failure)
        self.fgm_data['Incorrect vectors sampled'].append(
                                                    incorrect_vectors_sampled)
        self.fgm_data['Possible currupt science data'].append(
                                                possible_corrupt_science_data)
        self.fgm_data['DPU test sequence number'].append(
                                                    dpu_test_sequence_number)
        self.fgm_data['MSA data filtered'].append(msa_data_filtered)
        self.fgm_data['Calibration sequence number'].append(cal_seq_number)
        self.fgm_data['Memory Dump in Progress'].append(mem_dump_in_progress)
        self.fgm_data['Code Patch in Progress'].append(code_patch_in_progress)
        self.fgm_data['Packet Start HF'].append(packet_start_hf)
        first_1ry_hf = RawDataHeader.read_bytes([8,9],science_header)
        first_2ry_hf = RawDataHeader.read_bytes([10,11],science_header)
        self.fgm_data['First 1ry HF'].append(first_1ry_hf)
        self.fgm_data['First 2ry HF'].append(first_2ry_hf)
        reset_count = RawDataHeader.read_bytes([12,13],science_header)       
        self.fgm_data['Reset Count'].append(reset_count)
        '''
        bits 14 - 33 not used
        '''
        return 1
    def read_data(self):
        for i in range(20000):#arbitrary limit to the number of packets
            dds_data = self.read_dds(self.data[self.packet_offset:
                                                self.packet_offset+15])
            self.packet_offset+=15
            fgm_data = self.read_fgm_science(self.data[self.packet_offset:
                                                self.packet_offset+34])
            self.packet_offset+=self.dds_data['Packet Length'][-1]
            if not dds_data or not fgm_data:
                break
        self.fgm_data.update(self.dds_data) #modifies fgm_data inplace
        number_of_packets = len(self.fgm_data[self.fgm_data.keys()[0]])
        self.packet_info = pd.DataFrame(self.fgm_data,
                               index=[i for i in range(1,number_of_packets+1)])
        self.packet_info.insert(self.packet_info.columns.get_loc(
                                        'Reset Count')+1,
                                        'Reset Increment',
                                        self.packet_info['Reset Count'].diff())
        def calculate_spin_period(row):
            HF_diff = row['Most Recent Sun Pulse']-row['Previous Sun Pulse']
            if HF_diff > 0:
                return HF_diff/RawDataHeader.HF_freq
            else:
                return (HF_diff+0xFFFF)/RawDataHeader.HF_freq
        self.packet_info.insert(self.packet_info.columns.get_loc(
                                'Most Recent Sun Pulse')+1,
                                'Spin Period (s)',
                                self.packet_info.apply(calculate_spin_period,
                                                       axis=1))
        self.packet_info.insert(self.packet_info.columns.get_loc(
                                        'SCET')+1,'Reset Period (s)',
                                        self.packet_info['SCET'].diff().apply(
                                        lambda x:x/pd.Timedelta(1,'s')))
'''
#Usage example
pd.options.display.expand_frame_repr=False
pd.options.display.max_rows=20
raw = RawDataHeader(1,datetime(2016,1,6),'NS',version='b')
raw.read_data()
packet_info =  raw.packet_info
'''