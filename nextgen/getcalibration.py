from getcalfile import getcalfile
import os
import numpy as np
#from datetime import datetime

RAW = '/cluster/data/raw/'
CAACAL='/cluster/caa/calibration/' #caa calibration files directory
DAILYCAL='/cluster/operations/calibration/daily/'#dailycalfile dir

#RAW = 'Z:/data/raw/'
#CAACAL = 'Z:/caa/calibration/'
#DAILYCAL = 'Z:/operations/calibration/daily/'

def display_calibration(offsetx,offsety,offsetz,gainx,gainy,gainz):
    dec_points = 4
    pad = 11
    print "Sensor: OB, ADC: 1"
    print ("Range:    {1:{0:}}{2:{0:}}{3:{0:}}{4:{0:}}"
                    "{5:{0:}}{6:{0:}}".format(pad,*range(2,8)))
    print ("Offset X: {2:{0:}.{1:}f}{3:{0:}.{1:}f}{4:{0:}.{1:}f}{5:{0:}.{1:}f}"
        "{6:{0:}.{1:}f}{7:{0:}.{1:}f}".format(pad,dec_points,*offsetx[0,:]))
    print ("Offset Y: {2:{0:}.{1:}f}{3:{0:}.{1:}f}{4:{0:}.{1:}f}{5:{0:}.{1:}f}"
        "{6:{0:}.{1:}f}{7:{0:}.{1:}f}".format(pad,dec_points,*offsety[0,:]))
    print ("Offset Z: {2:{0:}.{1:}f}{3:{0:}.{1:}f}{4:{0:}.{1:}f}{5:{0:}.{1:}f}"
        "{6:{0:}.{1:}f}{7:{0:}.{1:}f}".format(pad,dec_points,*offsetz[0,:])) 
    print ("Gain X  : {2:{0:}.{1:}f}{3:{0:}.{1:}f}{4:{0:}.{1:}f}{5:{0:}.{1:}f}"
        "{6:{0:}.{1:}f}{7:{0:}.{1:}f}".format(pad,dec_points,*gainx[0,:]))
    print ("Gain Y  : {2:{0:}.{1:}f}{3:{0:}.{1:}f}{4:{0:}.{1:}f}{5:{0:}.{1:}f}"
        "{6:{0:}.{1:}f}{7:{0:}.{1:}f}".format(pad,dec_points,*gainy[0,:]))
    print ("Gain Z  : {2:{0:}.{1:}f}{3:{0:}.{1:}f}{4:{0:}.{1:}f}{5:{0:}.{1:}f}"
        "{6:{0:}.{1:}f}{7:{0:}.{1:}f}".format(pad,dec_points,*gainz[0,:]))
def read_line(line):
    return [float(entry) for entry in line.split(' ') if not (entry == '' or entry.find('S')!=-1)]

def getcal(sc,start_date,calibration='CAA'):
    # [adc 1..2][sensor 0..1 (OB..IB)][sc 1..4][range 2..5]
    #
    # Order in Cal File
    # OB     ADC1
    #    IB  ADC1
    # OB          ADC2
    #    IB       ADC2
    #
    # Range 2, 3, 4, 5, 7
    #
    # Offset X
    # Offset Y
    # Offset Z
    #
    # Gain X
    # ----
    # ----
    #
    # ----
    # Gain Y
    # ----
    #
    # ----
    # ----
    # Gain Z
    
    # for non-default calibration files
    # Range 2, 3, 4, 5, 6
    # ----
    # ...
    # ----
    #!Range7
    # Offset X   Offset Y   Offset Z 
    #   M1          M2			M3
    #	M4			M5			M6
    #	M7			M8			M9
    
    #we care about the diagonal elements M1,M5,M9, since these are the gains, 
    #+ some re-orthogonalisation which
    #is assumed to be negligible for ext mode data processing.
    #thus, effectively  M1 = Gain X
    #					M2 = Gain Y
    #					M3 = Gain Z
    if calibration.upper() == 'DEFAULT':
        calfile = "/cluster/operations/calibration/default/C"+format(sc,'1d')+".fgmcal";	
    elif calibration.upper() == 'CAA':
        calfile = getcalfile(sc,start_date,cal_dir=CAACAL)
    elif calibration.upper() == 'DAILY':
        calfile = getcalfile(sc,start_date,cal_dir=DAILYCAL)
    else:
        print "Please select a valid calibration type! (caa|daily|default)"
        return False
    print "calfile found:",calfile
    if os.path.isfile(calfile):
        if not os.stat(calfile).st_size:
            return False
    else:
        return False
    with open(calfile,'rb') as f:
        lines = f.readlines()
    lines = lines[1:] #skip first line
    line_counter = 0
    offsetx = np.zeros((4,6),dtype=np.float64)
    offsety = np.zeros((4,6),dtype=np.float64)
    offsetz = np.zeros((4,6),dtype=np.float64)
    gainx = np.ones((4,6),dtype=np.float64)
    gainy = np.ones((4,6),dtype=np.float64)
    gainz = np.ones((4,6),dtype=np.float64)
    #sholud be 1,2 1,2 - but this makes indexing easier
    for adc_sensor in range(0,4):
            offsetx[adc_sensor,:-1] = read_line(lines[line_counter])[:5]
                                    #ignore identifier string (eg. S2_32)
            line_counter += 1
            offsety[adc_sensor,:-1] = read_line(lines[line_counter])[:5]
                                    #ignore identifier string (eg. S2_32)
            line_counter += 1
            offsetz[adc_sensor,:-1] = read_line(lines[line_counter])[:5]
                                    #ignore identifier string (eg. S2_32)
            line_counter += 1            
            gainx[adc_sensor,:-1] = read_line(lines[line_counter])[:5]
                                    #ignore identifier string (eg. S2_32)
            line_counter += 4 #skip 3 lines
            gainy[adc_sensor,:-1] = read_line(lines[line_counter])[:5]
                                    #ignore identifier string (eg. S2_32)
            line_counter += 4 #skip 3 lines            
            gainz[adc_sensor,:-1] = read_line(lines[line_counter])[:5]
                                    #ignore identifier string (eg. S2_32)
            line_counter += 1           
    '''
    Now attempt to fill in range 7 info
    '''
    for linecount in range(len(lines)):
        line = lines[linecount]
        if '#!Range7' in line:
            linecount += 1
            offsetx[0,-1],offsety[0,-1],offsetz[0,-1] = read_line(lines[linecount])
            linecount += 1
            gainx[0,-1],dummy1,dummy2 = read_line(lines[linecount])
            linecount += 1
            dummy1,gainy[0,-1],dummy2 = read_line(lines[linecount])
            linecount += 1
            dummy1,dummy2,gainz[0,-1] = read_line(lines[linecount])
            break
    if calibration.upper() == 'DAILY':
        daily_range7_dir = '/cluster/operations/calibration/daily/range7/'+start_date.strftime('%Y/%m/')
        daily_range7_file = daily_range7_dir+'C'+format(sc,'1d')+'_range7.fgmcal'
        if os.path.isfile(daily_range7_file):
            with open(daily_range7_file,'rb') as f:
                lines = f.readlines()
                line_counter = 0
                offsetx[0,-1] = read_line(lines[line_counter])
                line_counter += 1
                offsety[0,-1] = read_line(lines[line_counter])
                line_counter += 1
                offsetz[0,-1] = read_line(lines[line_counter])
                line_counter += 1
                gainx[0,-1] = read_line(lines[line_counter])
                line_counter += 4 #skip 3 lines
                gainy[0,-1] = read_line(lines[line_counter])
                line_counter += 4 #skip 3 lines
                gainz[0,-1] = read_line(lines[line_counter])   
    '''
    Calibration modification - ignore orthogonalities, average gains in 
    spin plane, set offset in spin plane to 0 - assume they cancel out.
    '''
    print "RAW {0} calibration, as read from {1}".format(calibration.upper(),
                                                            calfile)
    display_calibration(offsetx,offsety,offsetz,gainx,gainy,gainz)
    for adc_sensor in range(0,4):
        for r in range(0,6): #corresponds to [2,3,4,5,6,7]
            offsety[adc_sensor,r] = 0
            offsetz[adc_sensor,r] = 0
            
            n = gainy[adc_sensor,r]
            m = gainz[adc_sensor,r]
            
            gainy[adc_sensor,r] = (n+m)/2
            gainz[adc_sensor,r] = (n+m)/2
            
    print "Modified {0} calibration, used for data!".format(calibration.upper())
    display_calibration(offsetx,offsety,offsetz,gainx,gainy,gainz)
    return offsetx,offsety,offsetz,gainx,gainy,gainz
    
#offsetx,offsety,offsetz,gainx,gainy,gainz =getcal(1,datetime(2016,1,20))