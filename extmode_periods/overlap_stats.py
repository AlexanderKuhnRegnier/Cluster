import pandas as pd
from overlap_data_dict_processing import read_overlap_data_dicts
import cPickle as pickle
import os
'''
#overlap_data.groupby(overlap_data['start'].dt.normalize())
#df.drop_duplicates()
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
print "Size after dropping duplicates:",overlap_data.size,overlap_data.shape
with open(pickledir+data_file,'wb') as f:
     pickle.dump(overlap_data,f,protocol=2)