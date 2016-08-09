import pandas as pd
import numpy as np
from overlap_data_dict_processing import read_overlap_data_dicts
import cPickle as pickle
import os
import matplotlib.pyplot as plt
import itertools
#plt.style.use('seaborn-darkgrid')
plt.close('all')
import data_analysis as da
import PyPDF2 as pdf
results_root = 'Y:/overlap_stats/results_'
pickledir = 'Y:/overlap_stats/'
imagedir=pickledir+'images/'
data_file = 'overlap_stats.pickle'

def append_pdf(input,output):
    [output.addPage(input.getPage(page_num)) for page_num in 
                            range(input.numPages)]

def report_frame(filtered_frame,source='caa'):
    results_dir = results_root+source
    for i in range(0,100):
        results_dir_new = results_dir+format(i,'03d')+'/'
        if not os.path.isdir(results_dir_new):
            os.makedirs(results_dir_new)
            break
    '''
    calls the package_data function from the data analysis
    code for every row in the input frame
    '''
    for index,row in filtered_frame.iterrows():
        da.package_data(row,source=source,result_dir=results_dir_new)

def save_filtered(filtered_frame,filetypes=['.pdf'],dpi=330,prune=True,
                  source='caa'):
    '''
    Take a dataframe that has been filtered using certain criteria,
    and saves figures depicting the time intervals and spacecraft 
    specified in the dataframe.
    Options to change the saved filetype(s) and the dpi.
    '''
    for image_type in filetypes:
        for index,row in filtered_frame.iterrows():
            da.plot_mag_xyz(row,save=True,dpi=dpi,image_type=image_type,
                            show=False,prune=prune,source=source)
            da.plot_xyz(row,save=True,dpi=dpi,image_type=image_type,
                            show=False,prune=prune,source=source)
        if image_type=='.pdf':
            merger = pdf.PdfFileMerger()
            for f in os.listdir(imagedir):
                if '.pdf' in f:
                    merger.append((file(imagedir+f,'rb')))
            if prune:
                merger.write(imagedir+'overlap_periods.pdf')
            else:
                merger.write(imagedir+'overlap_periods_not_pruned.pdf')                

'''
#overlap_data.groupby(overlap_data['start'].dt.normalize())
'''

if os.path.isfile(pickledir+data_file):
    with open(pickledir+data_file,'rb') as f:
        overlap_data = pickle.load(f)
else:
    overlap_data = pd.DataFrame()

overlap_data_dict=read_overlap_data_dicts(remove=True)
new_overlap_data = pd.DataFrame(overlap_data_dict,columns=['start','end',
                                                       'duration',
                                                       'std',
                                                       'max',
                                                       'min',
                                                       'mean',
                                                       'ext_sc',
                                                       'non_ext_sc',
                                                       'std_threshold',
                                                       'std_n'])
overlap_data = pd.concat((overlap_data,new_overlap_data),axis=0)
print "Size before dropping duplicates:",overlap_data.size,overlap_data.shape
overlap_data.drop_duplicates(['start','end'],inplace=True)
overlap_data.reset_index(drop=True,inplace=True)
print "Size after dropping duplicates:",overlap_data.size,overlap_data.shape
with open(pickledir+data_file,'wb') as f:
     pickle.dump(overlap_data,f,protocol=2)
     
##############################################################################
'''
setting display options
'''

pd.set_option('expand_frame_repr',False)
pd.set_option('precision',4)
print "Data Description"
print overlap_data.describe()
pd.set_option('max_rows',30)
'''
processing
'''
#replacing seconds column by hour column
overlap_data['duration']*=(1/3600.)
overlap_data.rename(columns={'duration':'duration (h)'},inplace=True)

'''
min_time=2. #hours
print "\nAll overlaps longer than {0:.1f} hours".format(min_time)
print overlap_data[overlap_data['duration (h)']>min_time]
'''

'''
print "\nAll overlaps sorted by time in descending order"
print overlap_data.sort_values(by='duration (h)',ascending=False)

print "\nNumber of overlaps wrt ext_sc"
print overlap_data.groupby('ext_sc').size()

print "\nNumber of overlaps wrt non_ext_sc"
print overlap_data.groupby('non_ext_sc').size()

print "\nNumber of overlaps by year"
print overlap_data.groupby(overlap_data['start'].dt.year).size()

print "\nNumber of overlaps by month"
print overlap_data.groupby(overlap_data['start'].dt.month).size()
'''

'''
upper_percentile=0.98
lower_percentile=0.95
print "\nDuration between {0:0.1f} and {1:0.1f} percent, sorted by standard "\
       "deviation in ascending order".format(upper_percentile*100,
                                               lower_percentile*100)
print overlap_data[(overlap_data['duration (h)']>
                    overlap_data['duration (h)'].quantile(lower_percentile))
                  & (overlap_data['duration (h)']<
                    overlap_data['duration (h)'].quantile(
                    upper_percentile))].sort_values(
                    by='std',ascending=True)
'''

'''
longest_duration=9
shortest_duration=5
print "\nDuration between {0:0.1f} and {1:0.1f} hours, sorted by standard "\
       "deviation in ascending order".format(longest_duration,
                                               shortest_duration)
print overlap_data[(overlap_data['duration (h)']>shortest_duration)
                  & (overlap_data['duration (h)']<longest_duration)
                  ].sort_values(by='std',ascending=True)
 '''  

'''               
print "\nHexbin plot of duration (h) vs standard deviation (nT)"
ax=overlap_data.plot(kind='hexbin',x='duration (h)',y='std',gridsize=100)
'''
#fig = ax.get_figure()
#fig.savefig(pickledir+'hexbin.png',dpi=300)

'''
print "\nHexbin plot of duration (h) vs standard deviation (nT) log bins"
ax=overlap_data.plot(kind='hexbin',x='duration (h)',y='std',gridsize=100,bins='log',
                         title='Hexbin, log bins')
fig = ax.get_figure()
cb = fig.get_axes()[1]
cb.set_ylabel('log10(N)')
plt.show()
'''

'''
print "\nScatter plot of duration (h) vs standard deviation (nT)"
ax=overlap_data.plot(kind='scatter',x='duration (h)',y='std')
'''

'''
limit = 0.2  #hours
print "\nHexbin plot of duration (h) vs standard deviation (nT) log bins"\
             "(durations over {0:.1f} hours)".format(limit)
filtered = overlap_data[overlap_data['duration (h)']>2]
if not filtered.empty:
    ax=filtered.plot(kind='hexbin',x='duration (h)',y='std',gridsize=100,bins='log',
                             title='Hexbin, log bins')
    fig = ax.get_figure()
    cb = fig.get_axes()[1]
    cb.set_ylabel('log10(N)')
    plt.show()
'''

'''
width = 0.01
min_hour = 0
max_hour = 13
hour_mins = np.arange(min_hour,max_hour,width)
hour_maxs = hour_mins[1:]
hour_mins = hour_mins[:-1]
min_std = []
for mini,maxi in zip(hour_mins,hour_maxs):
    filtered = overlap_data[overlap_data['duration (h)']>=mini]
    filtered = filtered[filtered['duration (h)']<maxi]
    min_std.append(filtered['std'].min())
fig,ax=plt.subplots(figsize=(20,12))
rects1 = ax.bar(hour_mins,min_std,width,label='Minimum STD')
plt.show()
ax.legend()
ax.set_xlabel('Duration (hours)',fontsize=14)
ax.set_ylabel('std (nT)',fontsize=14)
plt.suptitle('Minimum standard deviation for different duration intervals',
             fontsize=16)
'''

'''            
filtered = overlap_data.sort_values('duration (h)',ascending=False).iloc[:40].\
            sort_values('std').iloc[:2]
save_filtered(filtered)
'''

filtered = []
for (ext_sc,non_ext_sc) in itertools.permutations([0,1,2,3],2):
    df=overlap_data[(overlap_data['ext_sc']==ext_sc) & 
                    (overlap_data['non_ext_sc']==non_ext_sc)]
    m_list = [0.5,1.2,2,4]#min hours
    max_field = 8 #nT
    for m in m_list:
        filtered.append(df[(df['duration (h)']>m)
                        & (df['mean']<max_field)].sort_values('std',
                          ascending=True).groupby(
                          overlap_data['start'].dt.year).first())


results = pd.concat(filtered,ignore_index=True).\
                    drop_duplicates(['start','end','ext_sc','non_ext_sc'])
results.sort_values('start',inplace=True)
results.reset_index(drop=True,inplace=True)
filtered_results = results[results['std']<2.5]
#filtered_results.plot(kind='hexbin',x='ext_sc',y='non_ext_sc',gridsize=7)
filtered2 = filtered_results[filtered_results['start'].dt.year != 2013]