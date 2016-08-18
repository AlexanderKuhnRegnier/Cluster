import numpy as np
from getscchfile import getscchfiles
from datetime import datetime
import pandas as pd

end_date=datetime(9999,1,1)
EXTMODE_INITIATE = ["SFGMJ059","SFGMJ064","SFGMSEXT","SFGMM002"]
EXTMODE_TERMINATE = ["SFGMJ065","SFGMJ050"]
EXTMODE_COMMANDS = EXTMODE_INITIATE+EXTMODE_TERMINATE

def getcommands(sc,start_date,end_date,dir):
    extmode_commanding_list = []
    extmode_commanding=np.zeros((0,3))
    #print extmode_commanding
    scch_files = getscchfiles(sc,start_date,end_date,dir=dir)
    #print scch_files
    prev_short_line = ''        
    for file in scch_files:
        #print file
        with open(file,mode='rb') as f:
            for line in f:
                if len(line)>15:
                    offset=0
                    if '\n' in prev_short_line:
                        offset=len(prev_short_line)
                    prev_short_line=''
                    data = line[15-offset:]
                    data = data.split(' ')
                    command = data[3]
                    if command[1:] in EXTMODE_INITIATE:
                        command_execution_time = data[0]
                        '''
                        print "time",command_execution_time,"command",command
                        '''
                        extmode_commanding = np.vstack((
                        extmode_commanding,
                        [command_execution_time,'INITIATE',sc]))
                    elif command[1:] in EXTMODE_TERMINATE:
                        command_execution_time = data[0]
                        '''
                        print "time",command_execution_time,"command",command
                        '''
                        extmode_commanding = np.vstack((
                        extmode_commanding,
                        [command_execution_time,'TERMINATE',sc]))
                else:
                    prev_short_line = line
        '''
        print "commanding"
        print extmode_commanding
        '''
        extmode_commanding_list.append(extmode_commanding)
    return extmode_commanding_list

def eliminate_identical(extmode_commanding):
    delete_list=[]
    if np.shape(extmode_commanding)[0]>0:
        previous_line = extmode_commanding[0]
        for i in xrange(1,len(extmode_commanding)):
            current_line = extmode_commanding[i]
            if np.array_equal(previous_line,current_line):
                delete_list.append(i)
            else:
                previous_line = current_line
            i+=1
        return np.delete(extmode_commanding,delete_list,0)
    else:
        return []
    
def eliminate_adjacent_identical(extmode_commanding):
    if np.shape(extmode_commanding)[0]>0:
        delete_list=[]
        previous_command_sc = extmode_commanding[0][1]+extmode_commanding[0][2]
        for i in xrange(1,len(extmode_commanding)):
            current_command_sc = extmode_commanding[i][1]+\
                                    extmode_commanding[i][2]
            if previous_command_sc == current_command_sc:
                delete_list.append(i)
            else:
                previous_command_sc = current_command_sc
            i+=1
        return np.delete(extmode_commanding,delete_list,0)    
    else:
        return []
    
def ext_commands(sc,start_date,end_date=0,dir='Z:/data/raw/'):
    '''
    Gets extended mode start and end times. Automatically applies a 
    'padding' of start and end dates, expanding them by 6 days, so that
    extended modes that run over midnight are also captured, and to account
    for the fact that the start time of extended mode is still unknown!
    '''
    days_pad = 5
    start = start_date - pd.Timedelta(days_pad,unit='d')
    if not end_date:
        end = start_date+pd.Timedelta(1,unit='d')
    else:
        end = end_date+pd.Timedelta(1,unit='d')
    extmode_commanding_list=getcommands(sc,start,end,dir)
    '''
    print "original"
    print extmode_commanding_list
    print ""
    '''
    templist=[]
    for extmode_commanding in extmode_commanding_list:
        '''
        print "Commanding1\n", extmode_commanding
        print ""
        '''
        extmode_commanding=eliminate_identical(extmode_commanding)
        '''
        print "Commanding2\n", extmode_commanding
        print ""
        '''
        extmode_commanding=eliminate_adjacent_identical(extmode_commanding)
        '''
        print "Commanding3\n", extmode_commanding
        print ""
        '''
        templist.append(extmode_commanding)
    extmode_commanding_list=templist
    ext_commanding = {'Date':[],'Spacecraft':[],'Command':[]}
    for a in extmode_commanding_list:
        if len(a):
            ext_commanding['Date'].extend(a[:,0])
            ext_commanding['Command'].extend(a[:,1])
            ext_commanding['Spacecraft'].extend(a[:,2])
    ext_commanding = pd.DataFrame(ext_commanding)
    if not ext_commanding.empty:
        ext_commanding.drop_duplicates(inplace=True)
        ext_commanding[['Spacecraft']]=ext_commanding[['Spacecraft']].apply(
                                                        pd.to_numeric)
        ext_commanding['Date']=ext_commanding['Date'].apply(pd.to_datetime)
        ext_commanding['Previous Date']=ext_commanding['Date'].shift()
        ext_commanding['Previous Command']=ext_commanding['Command'].shift()
        ext_commanding['Duration (s)']=ext_commanding['Date'].diff().apply(
                                                    lambda x:x/pd.Timedelta(1,'s'))
        def validity(row):
            if row['Previous Command']=='INITIATE' and row['Command']=='TERMINATE'\
            and row['Duration (s)']>0:
                return True
            else:
                return False
        ext_commanding['Valid'] = ext_commanding.apply(validity,axis=1)
        def start_end(row):
            if row['Valid']:
                return pd.Series((row['Previous Date'],row['Date']),
                                 index=['Start','End'])
            else:
                return pd.Series()
        ext_commanding = ext_commanding.iloc[1:]
        ext_commanding = pd.concat((ext_commanding,
                                ext_commanding.apply(start_end,axis=1)),axis=1)
        if 'Start' in ext_commanding.columns:
            ext_commanding =ext_commanding[['Start','End','Duration (s)','Spacecraft']]
            return ext_commanding[ext_commanding['End'].notnull()]
    return pd.DataFrame()
'''
RAW = 'C:/Users/ahfku/Documents/Magnetometer/clusterdata/'
#RAW = 'Z:/data/raw/'
for i in range(1,31):
    ext_commanding = ext_commands(1,datetime(2016,1,i),
                                       dir=RAW)
    if not ext_commanding.empty:
        print ext_commanding
    
ext_commanding = ext_commands(1,datetime(2016,1,1),datetime(2016,1,30),
                                   dir=RAW)
print ext_commanding
'''