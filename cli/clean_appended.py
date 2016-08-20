LOG = '/home/ahk114/logs/date_range/'
APPENDED_EXT = 'ext_appended.log'
APPENDED_EXT_GSE = 'ext_gse_appended.log'

def drop_duplicates(filepath):
    '''
    Reads the file at filepath and removes duplicates from the entries,
    based only on the date information in the file (first 23 characters)
    The last entries are kept, in case new processing methods change the 
    values, but not the dates somehow.
    If dates are changed by a change in the processing code, then this 
    way of identifying duplicates no longer works and those duplicates 
    will remain!
    
    No sorting is performed, it is assumed that the original file contains
    sorted entries
    '''
    lines = []
    with open(filepath,'rb') as f:
        lines=f.readlines()
    lines.reverse()
    seen = {}
    pos = 0
    for line in lines:
        if line[:24] not in seen:
            seen[line[:24]]=True
            lines[pos]=line
            pos+=1
    del lines[pos:]
    lines.reverse()
    with open(filepath,'wb') \
    as f:
        f.writelines(lines)

def unique_fileset(filepath):
    '''
    Returns an unordered set of filenames
    '''
    lines=[]
    try:
        with open(filepath,'rb') as f:
            lines=f.readlines()
    except IOError:
        print filepath,"does not seem to exist!"
        return False
    return set([line.split(' ')[-1].rstrip() for line in lines])
    
def main():
    import math,datetime
    not_processed = []
    log_dir = LOG
    log_appended_files = (APPENDED_EXT,APPENDED_EXT_GSE)
    for log_file in log_appended_files:
        time = datetime.datetime.now()
        time_str = time.strftime('%Y-%m-%d %H:%M:%S ')
        files = unique_fileset(log_dir+log_file)
        if files:
            increment_every = int(len(files)/10)
            if increment_every == 0:
                increment_every = 1
            s = int(math.ceil(len(files)/float(increment_every)))
            counter = 0
            start = datetime.datetime.now()
            print "Cleaning files from:",log_file
            print "Time (s) Completion"
            for count,filepath in enumerate(files):
                if count%increment_every==0:
                    print format((datetime.datetime.now()-start).seconds,
                                                                 '04d')+' s  ',
                    print "|"+"-"*counter+"|".rjust(s-counter)
                    counter+=1
                try:
                    drop_duplicates(filepath)
                except IOError:
                    not_processed.append(time_str+filepath+'\n')
            number_processed = len(files)-len(not_processed)
            print "Number of files processed (/total files):",\
                                str(number_processed)+"/"+str(len(files))
    error_file = log_dir+'not_cleaned.log'
    with open(error_file,'ab') as f:
        f.writelines(not_processed)
    print "To remove the appended.log files, execute the following:"
    print "rm {0} ; rm {1} ;".format(*[log_dir+log_file for log_file in 
                                                        log_appended_files])
    
if __name__ == "__main__":
    main()