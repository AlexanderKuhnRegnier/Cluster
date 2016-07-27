from datetime import datetime,timedelta
import argparse
from find_extmode_periods import get_overlap_data
import numpy as np
import cPickle as pickle
import csv
import os
pickledir = 'Y:/overlap_stats/'
parser = argparse.ArgumentParser()
parser.add_argument('-y', '--year',required=True,type=int)
parser.add_argument('-m', '--month',required=True,type=int)
parser.add_argument('-d', '--day',required=True,type=int)
parser.add_argument('-l', '--duration',required=True,type=int)
parser.add_argument('-p', '--prune-value',required=False,default=10.0,type=float)
parser.add_argument('-n', '--std-n',required=False,default=20,type=int)
parser.add_argument('-s', '--std-step-number',required=False,default=10,type=int)
parser.add_argument('-a', '--std-start',required=False,default=0.1,type=float)
parser.add_argument('-b', '--std-end',required=False,default=1.0,type=float)
args = parser.parse_args()

start_date        =datetime(args.year,args.month,args.day)
end_date          =start_date + timedelta(days=args.duration)
print "Start date:",start_date
print "End date:  ",end_date

std_threshold_list=np.linspace(args.std_start,args.std_end,args.std_step_number)
overlap_data_dict={
'std':[],
'max':[],
'min':[],
'mean':[],
'ext_sc':[],
'non_ext_sc':[],
'start':[],
'end':[],
'duration':[]}

overlap_data = get_overlap_data(
start_date = start_date,
end_date = end_date,
overlay_plot = 0,
additional_plots = 0,
write_to_file = 0,
std_threshold_list=std_threshold_list,
std_n=args.std_n,
prune_value=args.prune_value,
raw_data_output=0 #needs to be enabled for additional_plots to work!
)
for row in overlap_data:
    overlap_data_dict['start'].append(row[0])
    overlap_data_dict['end'].append(row[1])
    overlap_data_dict['duration'].append(row[2])
    overlap_data_dict['max'].append(row[3][0])
    overlap_data_dict['min'].append(row[3][1])
    overlap_data_dict['mean'].append(row[3][2])
    overlap_data_dict['std'].append(row[3][3])
    overlap_data_dict['ext_sc'].append(row[4])
    overlap_data_dict['non_ext_sc'].append(row[6])

pickle_descriptor= \
'overlap_data_dict_'+\
start_date.strftime('%Y%m%dT%H%M%S')+\
'__'+end_date.strftime('%Y%m%dT%H%M%S')+\
'_std_n_'+format(args.std_n,'03d')+\
'_prune_value_'+format(args.prune_value)+\
'_std_threshold_list_'+'-'.join(map(str,std_threshold_list))+\
'.pickle'
picklef=pickledir+pickle_descriptor
with open(picklef,'wb') as f:
    pickle.dump(overlap_data_dict,f,protocol=2)
print "Wrote Dictionary to file:"
print picklef

filename = pickledir+'processed_periods.csv'
write_header=False
if not os.path.isfile(filename):
    write_header = True
with open(filename,'ab') as f:
    writer = csv.writer(f,dialect='excel')
    if write_header:
        writer.writerow(['Start Date','End Date','prune value','std n','std step number','std start','std end'])
    writer.writerow([start_date.strftime('%d/%m/%Y'),
                     end_date.strftime('%d/%m/%Y'),
                    str(args.prune_value),
                    str(args.std_n),
                    str(args.std_step_number),
                    str(args.std_start),
                    str(args.std_end)])