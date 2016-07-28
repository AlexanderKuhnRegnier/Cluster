import pandas as pd
from overlap_data_dict_processing import read_overlap_data_dicts
import cPickle as pickle
import os
import matplotlib.pyplot as plt
plt.style.use('seaborn-darkgrid')
plt.close('all')

'''
#overlap_data.groupby(overlap_data['start'].dt.normalize())
'''
pickledir = 'Y:/overlap_stats/'
data_file = 'overlap_stats.pickle'
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
                                                       'non_ext_sc'])
overlap_data = pd.concat((overlap_data,new_overlap_data),axis=0)
print "Size before dropping duplicates:",overlap_data.size,overlap_data.shape
overlap_data.drop_duplicates(inplace=True)
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
pd.set_option('max_rows',10)
print "Data Description"
print overlap_data.describe()
pd.set_option('max_rows',5)
'''
processing
'''
#replacing seconds column by hour column
overlap_data['duration']*=(1/3600.)
overlap_data.rename(columns={'duration':'duration (h)'},inplace=True)

min_time=2. #hours
print "\nAll overlaps longer than {0:.1f} hours".format(min_time)
print overlap_data[overlap_data['duration (h)']>min_time]

print "\nAll overlaps sorted by time in descending order"
print overlap_data.sort_values(by='duration (h)',ascending=False)

print "\nNumber of overlaps wrt ext_sc"
print overlap_data.groupby('ext_sc').size()

print "\nNumber of overlaps wrt non_ext_sc"
print overlap_data.groupby('non_ext_sc').size()

upper_percentile=0.9
lower_percentile=0.8
print "\nDuration between {0:0.1f} and {1:0.1f} percent, sorted by standard "\
       "deviation in ascending order".format(upper_percentile*100,
                                               lower_percentile*100)
print overlap_data[(overlap_data['duration (h)']>
                    overlap_data['duration (h)'].quantile(lower_percentile))
                  & (overlap_data['duration (h)']<
                    overlap_data['duration (h)'].quantile(
                    upper_percentile))].sort_values(
                    by='std',ascending=True)

longest_duration=9
shortest_duration=5
print "\nDuration between {0:0.1f} and {1:0.1f} hours, sorted by standard "\
       "deviation in ascending order".format(longest_duration,
                                               shortest_duration)
print overlap_data[(overlap_data['duration (h)']>shortest_duration)
                  & (overlap_data['duration (h)']<longest_duration)
                  ].sort_values(by='std',ascending=True)
   
'''               
print "\nHexbin plot of duration (h) vs standard deviation (nT)"
ax=overlap_data.plot(kind='hexbin',x='duration (h)',y='std',gridsize=100)
'''
#fig = ax.get_figure()
#fig.savefig(pickledir+'hexbin.png',dpi=300)


print "\nHexbin plot of duration (h) vs standard deviation (nT) log bins"
ax=overlap_data.plot(kind='hexbin',x='duration (h)',y='std',gridsize=100,bins='log',
                         title='Hexbin, log bins')
fig = ax.get_figure()
cb = fig.get_axes()[1]
cb.set_ylabel('log10(N)')


'''
print "\nScatter plot of duration (h) vs standard deviation (nT)"
ax=overlap_data.plot(kind='scatter',x='duration (h)',y='std')
'''

limit = 2  #hours
print "\nHexbin plot of duration (h) vs standard deviation (nT) log bins"\
             "(durations over {0:.1f} hours)".format(limit)
filtered = overlap_data[overlap_data['duration (h)']>2]
ax=filtered.plot(kind='hexbin',x='duration (h)',y='std',gridsize=100,bins='log',
                         title='Hexbin, log bins')
fig = ax.get_figure()
cb = fig.get_axes()[1]
cb.set_ylabel('log10(N)')

