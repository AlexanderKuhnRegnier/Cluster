import numpy as np
from bokeh.plotting import figure, output_file, show
from numpy import linalg as LA

m=1000000000000000

#filename = "Y:/reference/2015/12/C1_151231_B.EXT.GSE"
filename = "cal.GSE"
dates2 = []
x_mag = []
y_mag = []
z_mag = []

counter = 0
with open(filename) as f:
    for line in f:
        #print line[0:25],np.datetime64(line[0:25])
        #print line[:-1]
        #print "012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789"
        #print line[0:24], line[24:33], line[33:42], line[42:51]
        try:
            dates2.append(np.datetime64(line[0:24]))
            x_mag.append(float(line[24:33]))
            y_mag.append(float(line[33:42]))
            z_mag.append(float(line[42:51]))
        except ValueError:
            print "Something wrong with line"
        counter+=1
        if counter==m:
            break

magnitudes = np.vstack((x_mag,y_mag,z_mag))
#print magnitudes

total_magcal = LA.norm(magnitudes,axis=0)

#print total_mag

'''
print "values"
counter = 0
for (i,j) in zip(dates,x_mag):
    print i,j
    counter += 1
    if counter == 10:
        break

'''

filename = "default.GSE"
dates = []
x_mag = []
y_mag = []
z_mag = []

counter = 0
with open(filename) as f:
    for line in f:
        #print line[0:25],np.datetime64(line[0:25])
        #print line[:-1]
        #print "012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789"
        #print line[0:24], line[24:33], line[33:42], line[42:51]
        try:
            dates.append(np.datetime64(line[0:24]))
            x_mag.append(float(line[24:33]))
            y_mag.append(float(line[33:42]))
            z_mag.append(float(line[42:51]))
        except ValueError:
            print "Something wrong with line"
        counter+=1
        if counter==m:
            break

magnitudes = np.vstack((x_mag,y_mag,z_mag))
#print magnitudes

total_magdef = LA.norm(magnitudes,axis=0)


# output to static HTML file (with CDN resources)
output_file("plot.html", title="Plotting Default vs Proper Calibration", mode="cdn")

TOOLS="resize,crosshair,pan,wheel_zoom,box_zoom,reset"

# create a new plot with the tools above, and explicit ranges
p = figure(tools=TOOLS, width=1900, height=1000, x_axis_type="datetime")

p.line(dates, total_magdef, color='red', legend='total_mag default')
p.line(dates, total_magcal, color='green', legend='total_mag cal')

'''
p.line(dates, x_mag, color='navy', legend='x_mag')
p.line(dates, x_mag, color='blue', legend='x_mag')
p.line(dates, y_mag, color='red', legend='y_mag')
p.line(dates, z_mag, color='purple', legend='z_mag')
p.line(dates, total_mag, color='green', legend='total_mag')
'''
# show the results
show(p)