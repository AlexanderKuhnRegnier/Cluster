import fileinput
import tempfile

tmpfile = tempfile.TemporaryFile(mode='wb+')
tmpfile2 = tempfile.TemporaryFile(mode='wb+')
#print tmpfile.closed
counter = 0 
for line in fileinput.input():
    print "Writing: ", line,
    tmpfile.write(line)
print ""
#print "Finished Writing"

tmpfile.seek(0) #have to seek in order to see any output!!!
contents = tmpfile.readlines()
for line in contents:
    tmpfile2.write(str(int(line)+100)+'\n')
    
#print "Closing tmpfile"
print ""
tmpfile.close()    
print "Closed (1) (2): ", tmpfile.closed, tmpfile2.closed

print "Content of second tempfile"
tmpfile2.seek(0) #have to seek in order to see any output!!!
print tmpfile2.read()

tmpfile2.close() 
print "Finished"