import os
import cPickle as pickle
pickledir = 'Y:/overlap_stats/'

class newdict(dict):
    def __init__(self,*args,**kwargs):
        dict.__init__(self,*args,**kwargs)
        self.count = 0
    def join(self,otherdict):
        for key,value in otherdict.iteritems():
            if not type(value) == list:
                raise Exception("Other Dictionary does not contain list!")
            try:
                self[key].extend(value)
            except KeyError:
                print "Either the other dictionary introduced new keys, or the" \
                        "present dictionary does not have all the keys"
                raise
        self.count += 1
    def print_number_joint(self):
        print "Number of joins:",self.count

def read_overlap_data_dicts(remove=True):      
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
    overlap_data_dict=newdict(overlap_data_dict)
    read_files=[]
    for file in os.listdir(pickledir):
        if 'overlap_data_dict' in file and '.pickle' in file:
            with open(pickledir+file,'rb') as f:
                read_data = pickle.load(f)
            overlap_data_dict.join(read_data)
            read_files.append(file)
            
    print "read the following files"
    print 'nr. of files:{0:02d} \nnr. of joins:{1:02d}'.format(len(read_files),
                                                         overlap_data_dict.count)
    print read_files
    if remove:
        print "Removing files"
        removed=0
        for file in read_files:
            os.remove(pickledir+file)
            removed+=1
        print "Removed files:",format(removed,'02d')
    return overlap_data_dict