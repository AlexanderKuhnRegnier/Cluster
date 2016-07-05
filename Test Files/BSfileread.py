#import numpy as np
from datetime import datetime, timedelta

def shift_left(num,left):
    return num<<left

def read_bytes(indices,line):
    values=[]
    for i in indices:
        leftshift = (max(indices)-i)*8
        values.append(shift_left(ord(line[i]),leftshift))
    return sum(values)
    
RAW = 'Z:/data/raw/'
Year= '2016'
year='16'
month = '01'
day='01'
sc = '1'
version = 'B'
BSfile = RAW+Year+'/'+month+'/'+'C'+sc+'_'+year+month+day+'_'+version+'.BS'
print BSfile

f = open(BSfile, 'rb')
line=f.readline()
f.close()
print line
print len(line)
print [ord(line[i]) for i in range(len(line))]


#day0=ord(line[0])
#day1=ord(line[1])
#print day0,day1
#days=(day0<<8)+day1

day_indices = [0,1]
days = read_bytes(day_indices,line)
print days,(days/365)+1958

ms_indices = [2,3,4,5]
ms = read_bytes(ms_indices,line)
print 'ms,      s,    mins,hours'
print ms,ms/1000, (ms/1000)/60,((ms/1000)/60)/60

us_indices = [6,7]
us = read_bytes(us_indices,line)
print us, (us*ms/10e6)
us *= ms

date1=datetime(1958,1,1)
dt = timedelta(days=days,seconds=0,milliseconds=ms,microseconds=us)
print date1+dt

print line[8], ord(line[8]), hex(ord(line[8]))