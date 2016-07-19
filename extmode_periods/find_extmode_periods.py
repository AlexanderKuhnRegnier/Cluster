import numpy as np
from getscchfile import getscchfiles
from datetime import datetime,timedelta
import matplotlib.pyplot as plt
import matplotlib
from copy import deepcopy as deepcop
import os
import cPickle as pickle
import csv
import data_analysis
from data_analysis import refdir,refdirahk114,caadir
import calendar

end_date=datetime(9999,1,1)
EXTMODE_INITIATE = ["SFGMJ059","SFGMJ064","SFGMSEXT","SFGMM002"]
EXTMODE_TERMINATE = ["SFGMJ065","SFGMJ050"]
EXTMODE_COMMANDS = EXTMODE_INITIATE+EXTMODE_TERMINATE

def getcommands(start_date,end_date):
    extmode_commanding_list = []
    for s in range(4):
        sc=1+s
        extmode_commanding=np.zeros((0,3))
        #print extmode_commanding
        scch_files = getscchfiles(sc,start_date,end_date)
        #print scch_files
        for file in scch_files:
            #print file
            with open(file,mode='rb') as f:
                for line in f:
                    if len(line)>15:
                        data = line[15:]
                        data = data.split(' ')
                        command = data[3]
                        #print command
                        if command[1:] in EXTMODE_INITIATE:
                            command_execution_time = data[0]
                            #print "time",command_execution_time
                            extmode_commanding = np.vstack((
                            extmode_commanding,
                            [command_execution_time,'INITIATE',sc]))
                        elif command[1:] in EXTMODE_TERMINATE:
                            command_execution_time = data[0]
                            #print "time",command_execution_time
                            extmode_commanding = np.vstack((
                            extmode_commanding,
                            [command_execution_time,'TERMINATE',sc]))                   
        #print "commanding"
        #print extmode_commanding
        extmode_commanding_list.append(extmode_commanding)
    return extmode_commanding_list

def eliminate_identical(extmode_commanding):
    delete_list=[]
    if np.shape(extmode_commanding)[0]>0:
        previous_line = extmode_commanding[0]
        for i in range(1,len(extmode_commanding)):
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
        for i in range(1,len(extmode_commanding)):
            current_command_sc = extmode_commanding[i][1]+extmode_commanding[i][2]
            if previous_command_sc == current_command_sc:
                delete_list.append(i)
            else:
                previous_command_sc = current_command_sc
            i+=1
        return np.delete(extmode_commanding,delete_list,0)    
    else:
        return []
        
def print_results(results):
    '''
    Prints out the contents of the results array in a more easily readable way
    Converts the microsecond (us) time duration value into minutes for easier viewing
    '''
    for sc in range(4):
        print "SC",sc+1
        for i,row in zip(range(len(results)),results):
            if row[2]==sc:
                print format(i,'02d'),row[0].tolist().isoformat(),format(int(row[1]/60e6),'04d'),"mins",row[2],row[3]

def calculate_end_times(results):
    results_end_date = np.array([]).reshape(-1,4)
    for i in range(len(results)):
        results_end_date = np.vstack((results_end_date,
                                np.array([
                                results[i,0],
                                results[i,0]+results[i,1]*np.timedelta64(1,'us'),
                                results[i,2],
                                results[i,3]])))
    return results_end_date

def find_min_max_dates(results_end_date):
    print "SC has possible values 0,1,2,3!!!"
    min_date = datetime(9999,1,1)
    max_date = datetime(1,1,1)
    for row in results_end_date:
        start_date = row[0].tolist()
        end_date = row[1].tolist()
        if start_date<min_date:
            min_date = start_date
        if end_date>max_date:
            max_date=end_date
    if min_date == datetime(9999,1,1) or max_date == datetime(1,1,1):
        print "No events found!"
        return False,False
    return min_date.date(),max_date.date()

cmdlist = []
datelist = []

start_date = datetime(2015,8,6)
end_date = datetime(2015,10,10)
reprocess = 0

simple_plot = 0
overlay_plot = 1

write_to_file = 0

if reprocess:
    if 'datelist.pickle' in os.listdir(os.getcwd()):
        os.remove('datelist.pickle')
    if 'cmdlist.pickle' in os.listdir(os.getcwd()):
        os.remove('cmdlist.pickle')        

if 'datelist.pickle' in os.listdir(os.getcwd()) and 'cmdlist.pickle' in os.listdir(os.getcwd()):
    print "Loading previously processed results"
    f = open('datelist.pickle','r')
    datelist = pickle.load(f)
    f.close()
    f = open('cmdlist.pickle','r')
    cmdlist = pickle.load(f)
    f.close()
    print "   Datelist lengths",len(datelist[0]),len(datelist[1]),len(datelist[2]),len(datelist[3])
    print "Commandlist lengths",len(cmdlist[0]),len(cmdlist[1]),len(cmdlist[2]),len(cmdlist[3])
else:
    print "starting new processing"
    #time   commmand    sc
    
    extmode_commanding_list=getcommands(start_date,end_date)
    print "got commmands"
    #print "before"
    #for a in extmode_commanding_list:
        #print a
    #print "Before filter"
    #print extmode_commanding_list
    templist=[]
    for extmode_commanding in extmode_commanding_list:
        #print "Commanding1", extmode_commanding
        extmode_commanding=eliminate_identical(extmode_commanding)
        #print "Commanding2", extmode_commanding
        extmode_commanding=eliminate_adjacent_identical(extmode_commanding)
        templist.append(extmode_commanding)
        
    extmode_commanding_list=templist
    #print "after"
    #for a in extmode_commanding_list:
        #print a
    
    cmdlist = []
    datelist=[]
    for i in range(len(extmode_commanding_list)):
        extmode_cmds=extmode_commanding_list[i]
        dates = [line[0] for line in extmode_cmds]
        cmds = [line[1] for line in extmode_cmds]
        tempcmds=[]
        tempdates=[]
        for date in dates:
            #print "appending",date
            tempdates.append(np.datetime64(date))
            #print "appended",tempdates[-1]
            #print tempdates[-1].tolist()
        for cmd in cmds:
            if cmd=='INITIATE':
                tempcmds.append(1)
            elif cmd=='TERMINATE':
                tempcmds.append(0)
            else:
                tempcmds.append(0)
                print "Error:Not valid command"
        '''
        write the following data to file, and do more processing on it as well!!
        '''
        #print tempcmds
        #print tempdates
        cmds = tempcmds
        dates = tempdates
        cmdlist.append(cmds)
        datelist.append(dates)
        #axarr[i].plot_date(tempdates,tempcmds, '-') #this plots triangle wave - modify data in next stage
        
    picklefilename = 'cmdlist.pickle'
    f=open(picklefilename,'w')
    pickle.dump(cmdlist,f)
    f.close()
    picklefilename = 'datelist.pickle'
    f=open(picklefilename,'w')
    pickle.dump(datelist,f)
    f.close()
        
if simple_plot:
    plt.close('all')
    
    fig,axarr=plt.subplots(4,sharex=True)
    print "Plotting"

    print "modifying data"
    for cs,ds in zip(cmdlist,datelist):
        if len(cs) != len(ds):
            raise Exception("Not of equal lenght!!")
    
    c=0
    for cs,ds in zip(cmdlist,datelist):
        #tempcs = deepcop(cs)
        #tempds = deepcop(ds)
        tempcs = []
        tempds = []
        #print cs
        #print ds
        if len(cs)>1:
            for i in range(len(cs)-1):
                command = cs[i]
                next_command = cs[i+1]
                date = ds[i]
                next_date = ds[i+1]
                tempcs.append(command)
                tempcs.append(command)
                tempds.append(date)
                tempds.append(next_date)
                
                '''
                print "current, then next"
                print command,date
                print next_command,next_date
                '''
        #print "output"
        #print tempcs
        #print tempds  
        axarr[c].plot_date(tempds,tempcs, '-')
        c+=1
    
    for c in range(4):
        axarr[c].set_ylim(-0.2,1.2)
    


'''
cmdlist has corresponding datelist
'''

results = np.array([]).reshape(-1,4) 
'''   
will contain start time[0], duration[1] and spacecraft[2] which is in ext mode while
at least another spacecraft is not in ext mode
as well as the other spacecraft that is not in ext mode[3]
'''

spacecrafts = [0,1,2,3]
otherspacecrafts = lambda x: spacecrafts[:x]+spacecrafts[x+1:]
for spacecraft in range(4):
    dates = datelist[spacecraft]    #get list of date for a spacecraft - cmdlist[spacecraft] is the associated event list
    for eventid in range(len(dates)): #looping through all of the events for the selected spacecraft
        '''
        if ext mode is initiated, check if this has been the case for other spacecraft before,
        but we only care about the event immediately before the current spacecraft ext mode has 
        been initiated!
        '''
        currentcommand = cmdlist[spacecraft][eventid]
        if currentcommand==1:   #if currently, ext mode is being initiaed, check if this was the case earlier for other sc
                                #and in those cases, check how long
            currentdate = dates[eventid]
            if eventid<(len(dates)-1):
                current_end_date = dates[eventid+1]
                ext_mode_duration = (current_end_date-currentdate)/np.timedelta64(1,'us')
            else:
                current_end_date = -1 #end date is unknown!!
                ext_mode_duration = -1 #duration is therefore also unknown!
            other_scs = otherspacecrafts(spacecraft)
            for othersc in other_scs:
                #previous = np.datetime64(datetime(1,1,1))
                if len(datelist[othersc]):          #if this datelist even has any entries!
                    other_dates = np.array(datelist[othersc])
                    '''
                    print "Current, sc:",spacecraft
                    print currentdate,type(currentdate)                    
                    print "Other, sc:",othersc
                    print other_dates
                    print ""
                    '''
                    timediffs = np.array((other_dates-currentdate)/np.timedelta64(1,'us'),dtype=np.int64) #time differences in minutes! -
                    '''
                    need to assert the following things at this stage:
                        this loop is active if the currently selected sc is being told to switch to ext mode
                        at the current time (currentdate)
                        so we are looking for events in the period of time starting from the current time,
                        where the other spacecraft are NOT in ext mode.
                        Focus on time period between current time and time when current sc is given TERMINATE command (0)
                        
                        search through command-date pairs of all 3 other sc in the aforementioned time period
                        case1: 1(first) INITIATE command found
                            this means that until that time, the other sc was NOT in ext mode
                            -verify this by searching backwards through previous entries in order to find
                            the TERMINATE entry that MUST have preceeded this INITIATE command
                            if this check is completed successfully, record the CURRENT time as well
                            as the time difference between the current time and the initiate command,
                            as well as the spacecraft number for which the initiate command was found.
                        case2: 1(first) TERMINATE command found
                            the other sc was in ext mode until now, overlapping with the current spacecraft's
                            ext mode.
                            we now need to look for the time when the other sc is given an INITIATE command
                            But we are only to look in the time period between current time and when the
                            current sc is given a TERMINATE command.
                        case3: further INITIATE commands
                            this is covered in case2 above
                        case4: further TERMINATE commands
                            similar to case2, look for next INITIATE command
                        
                    In all cases, need to make sure that preceeding/next command (depending on which is required)
                    is present. - is this always necessary though?
                    
                    we also need to check for TERMINATE commands that occur before the current time windows, with
                    no additional INITIATE commands to follow it.
                    '''
                    #print "timediffs"
                    #print timediffs
                    
                    other_commands = cmdlist[othersc]
                    if len(other_commands) != timediffs.shape[0]:
                        raise Exception("other_commands list and timediffs array are not of the same length!")
                    length = len(other_commands) #is the same for both lists (arrays) !
                    '''
                    #the following for statement would be unable to deal with fewer than 3 commands, which
                    #is unreasonable given the low amount of ext mode for sc4 in particular
                    for cmd0,diff0,cmd1,diff1,cmd2,diff2 in \
                    zip(other_commands[:length-2],timediffs[:length-2],
                        other_commands[1:length-1],timediffs[1:length-1],
                        other_commands[2:],timediffs[2:]):
                    '''
                    last_index = length-1
                    for i in range(length):
                        orig_length = len(results)
                        cmd = other_commands[i]
                        timediff = timediffs[i]
                        if timediff<=0 and cmd==0:   #TERMINATE command before current time
                            if i == last_index:     #This was the last command issued
                                results = np.vstack((results,[currentdate,ext_mode_duration,spacecraft,othersc]))
                                '''
                                row = results[-1]
                                if 9<len(results)<21 and spacecraft==1:
                                    print "1"
                                    print row[0].tolist().isoformat(),format(int(row[1]/60e6),'04d'),row[2],row[3]
                                '''
                            elif timediffs[i+1]>0:#if next event is after the current even!
                                if timediffs[i+1]<ext_mode_duration:
                                    results = np.vstack((results,[currentdate,timediffs[i+1],spacecraft,othersc]))
                                else:
                                    results = np.vstack((results,[currentdate,ext_mode_duration,spacecraft,othersc]))

                                '''
                                row = results[-1]
                                if 9<len(results)<21 and spacecraft==1:
                                    print "2"
                                    print row[0].tolist().isoformat(),format(int(row[1]/60e6),'04d'),row[2],row[3]
                                '''
                            elif timediffs[i+1]<=0:
                                pass
                            else:#should never happen                                
                                raise Exception("Unknown Error")
                        if timediff>0 and cmd==0:
                            if timediff<ext_mode_duration:
                                duration = ext_mode_duration-timediff
                                new_start = currentdate+timediff*np.timedelta64(1,'us')
                                results = np.vstack((results,[new_start,duration,spacecraft,othersc]))
                                '''
                                row = results[-1]
                                if 9<len(results)<21 and spacecraft==1:
                                    print "3"
                                    print row[0].tolist().isoformat(),format(int(row[1]/60e6),'04d'),row[2],row[3]
                                '''
                        if timediff<=0 and cmd==1:
                            pass
                        if timediff>0 and cmd==1:
                            if i==0:    #if this is the first command!
                                #assume that there was no ext mode before this - is this valid without explicitly having the
                                #TERMINATE command?
                                if timediff>ext_mode_duration:
                                    results = np.vstack((results,[currentdate,ext_mode_duration,spacecraft,othersc]))
                                    '''
                                    row = results[-1]
                                    if 9<len(results)<21 and spacecraft==1:
                                        print "4"
                                        print row[0].tolist().isoformat(),format(int(row[1]/60e6),'04d'),row[2],row[3]
                                    '''
                                else:
                                    results = np.vstack((results,[currentdate,timediff,spacecraft,othersc]))
                                    '''
                                    row = results[-1]
                                    if 9<len(results)<21 and spacecraft==1:
                                        print "5"
                                        print row[0].tolist().isoformat(),format(int(row[1]/60e6),'04d'),row[2],row[3]
                                    '''
                        '''
                        if spacecraft==1:
                            if len(results)>orig_length:
                                orig_length=len(results)
                                if 9<len(results)<21:
                                    row = results[-1]
                                    print row[0].tolist().isoformat(),format(int(row[1]/60e6),'04d'),row[2],row[3]
                        '''
results = np.array(sorted(results,key=lambda x:x[0]))
#print "Sorted Results (by date)"
#for i,row in zip(range(len(results)),results):
#    print i,row

######
'''
for testing only
'''
'''
results = results[9:21]
print "reduced results"
for sc in range(1,2):
    print "SC",sc+1
    for i,row in zip(range(len(results)),results):
        if row[2]==sc:
            print format(i,'02d'),row[0].tolist().isoformat(),format(int(row[1]/60e6),'04d'),"mins",row[2],row[3]
'''
######     
        
if overlay_plot:
    '''
    Note that the conversion between the np.datetime64 object and the 
    python datetime.datetime object that seems to be necessary in order
    to plot the data also introduces a timeshift into the data,
    probably due to time-zone conversion or something similar.
    '''
    plt.close('all')
    
    fig,axarr=plt.subplots(4,sharex=True)
    print "Plotting Overlay with Relevant Time Periods"

    print "modifying data"
    for cs,ds in zip(cmdlist,datelist):
        if len(cs) != len(ds):
            raise Exception("Not of equal lenght!!")
    
    c=0
    for cs,ds in zip(cmdlist,datelist):
        #tempcs = deepcop(cs)
        #tempds = deepcop(ds)
        tempcs = []
        tempds = []
        #print cs
        #print ds
        if len(cs)>1:
            for i in range(len(cs)-1):
                command = cs[i]
                next_command = cs[i+1]
                date = ds[i]
                next_date = ds[i+1]
                tempcs.append(command)
                tempcs.append(command)
                tempds.append(date)
                tempds.append(next_date)
                
                '''
                print "current, then next"
                print command,date
                print next_command,next_date
                '''
        #print "output"
        #print tempcs
        #print tempds  
        axarr[c].plot_date(tempds,tempcs, '-')
        c+=1
    for row in results:
        start = row[0]
        end = start+np.timedelta64(1,'us')*row[1]
        axarr[row[2]].scatter(start,0.+(1-row[3]/3.),c='r',s=150)
        axarr[row[2]].scatter(end,0.+(1-row[3]/3.),c='g',s=150)
    for c in range(4):
        axarr[c].set_ylim(-0.2,1.2)
    figManager = plt.get_current_fig_manager()
    figManager.window.showMaximized()

#print_results(results)

results_end_date = calculate_end_times(results)
for rowend, row in zip(results_end_date,results):
    print rowend
    print row
    print ""
directory = 'Y:/ExtModeDurations/'
filename = directory+'extmode_durations.csv'
if write_to_file:
    with open(filename,'wb') as f:
        writer = csv.writer(f,dialect='excel')
        writer.writerow(['Start Time of Interval','Interval Duration (s)','Spacecraft in Ext Mode', 'Spacecraft not in Ext Mode'])
        for row in results:
            writer.writerow([row[0].tolist().strftime('%d/%m/%Y %H:%M:%S'),row[1]/1e6,row[2]+1,row[3]+1])
            
'''
Now, the time periods where ext mode for one spacecraft and non-ext mode for
any other spacecraft overlap.
The data_analysis module will now be used to generate a list of periods of
time, where data (either in ext or not in ext mode) with a standard deviation
below a certain threshold for a certain sample size is available, for 
field values up to a certain specified value. This list will then be searched
for matches with the overlaps determined previously
'''
'''
analyse every 'event' that is recorded, ie. every time that one sc is in ext
mode but at least 1 other sc is not
want to record:
        0+start time of this event
        1+end time of event
        2+duration of event in seconds
        (data: - only concerns data that meets the standard deviation target 
                set beforehand)
        3+sc in ext mode        
        4+analysis output for ext mode sc
        
        5+sc not in ext mode
        6+analysis output for non-ext mode sc
7 'columns' - number of 'rows' depending on the number of events
'''
data_list = []
PLOT = 1
reprocess = 1
std_threshold=1000.
std_n = 40
prune_value = 2000
prune_greater_than = False
for row in results_end_date:
    start_date,end_date=row[0].tolist().date(),row[1].tolist().date()
    spacecrafts=[row[2],row[3]]
    ext_modes = [1,0]
    for spacecraft,ext_mode in zip(spacecrafts,ext_modes):
        print ""
        print "SC:",spacecraft,"EXT MODE:",ext_mode
        if ext_mode:
            legend = 'ext mode'
            c = 'r'
        else:
            legend = 'non ext mode'
            c = 'b'
        print start_date,end_date
        input = [[refdir,ext_mode,c,legend,'mag']]
        prune_start = row[0].tolist()
        prune_end = row[1].tolist()
        output=data_analysis.analyse(
                              spacecraft=spacecraft+1,
                              input=input,start_date=start_date,
                              end_date=end_date,
                              prune_value=prune_value,
                              prune_greater_than=prune_greater_than,
                              prune_start=prune_start,
                              prune_end=prune_end,
                              PLOT=PLOT,reprocess=reprocess,
                              std_threshold=std_threshold,
                              std_n=std_n)
        if ext_mode:
            data_list.append([row[0].tolist(),
                              row[1].tolist(),
                              (row[1]-row[0])/np.timedelta64(1,'s'),
                              spacecraft,
                              output])
        else:
            data_list[-1].extend([spacecraft,output])
print "Finished compliling data list",len(data_list)

'''
Now just need to sift through all the entries in column 4 and 6 of
data_list, in order to find intervals that match up, and then filter
out this data in order to obtain the dataset which describes
the true intersection between the ext mode and non-ext mode
data, given the standard deviation requirements given.
'''