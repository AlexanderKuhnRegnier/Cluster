import numpy as np
from getscchfile import getscchfiles
from datetime import datetime,timedelta
import matplotlib.pyplot as plt
import matplotlib
from copy import deepcopy as deepcop
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
        print scch_files
        for file in scch_files:
            print file
            with open(file,mode='rb') as f:
                for line in f:
                    if len(line)>15:
                        data = line[15:]
                        data = data.split(' ')
                        command = data[3]
                        #print command
                        if command[1:] in EXTMODE_INITIATE:
                            command_execution_time = data[0]
                            extmode_commanding = np.vstack((
                            extmode_commanding,
                            [command_execution_time,'INITIATE',sc]))
                        elif command[1:] in EXTMODE_TERMINATE:
                            command_execution_time = data[0]
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


print "start"
#time   commmand    sc
start_date = datetime(2015,11,6)
end_date = datetime(2015,11,10)

extmode_commanding_list=getcommands(start_date,end_date)
print "got commmands"
print "before"
for a in extmode_commanding_list:
    print a
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
print "after"
for a in extmode_commanding_list:
    print a

plt.close('all')

fig,axarr=plt.subplots(4,sharex=True)
print "Plotting"
cmdlist = []
datelist=[]
for i in range(len(extmode_commanding_list)):
    extmode_cmds=extmode_commanding_list[i]
    dates = [line[0] for line in extmode_cmds]
    cmds = [line[1] for line in extmode_cmds]
    tempcmds=[]
    tempdates=[]
    for date in dates:
        tempdates.append(np.datetime64(date))
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
    print tempcmds
    print tempdates
    cmds = tempcmds
    dates = tempdates
    cmdlist.append(cmds)
    datelist.append(dates)
    #axarr[i].plot_date(tempdates,tempcmds, '-') #this plots triangle wave - modify data in next stage
    
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
    print cs
    print ds
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
    print "output"
    print tempcs
    print tempds  
    axarr[c].plot_date(tempds,tempcs, '-')
    c+=1

for c in range(4):
    axarr[c].set_ylim(-0.2,1.2)


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
        currentdate = dates[eventid]
        currentcommand = cmdlist[spacecraft][eventid]
        if currentcommand==1:   #if currently, ext mode is being initiaed, check if this was the case earlier for other sc
            other_scs = otherspacecrafts(spacecraft)
            for othersc in other_scs:
                #previous = np.datetime64(datetime(1,1,1))
                other_dates = np.array(datelist[othersc])
                
    