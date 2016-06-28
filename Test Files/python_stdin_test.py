import fileinput
import tempfile

tmpfile = tempfile.TemporaryFile(mode='wb+')
print tmpfile.closed
counter = 0 
for line in fileinput.input():
    print "Writing: ", line,
    tmpfile.write(line)
print ""
print "Finished Writing"
print "Contents of temporary file"
tmpfile.seek(0) #have to seek in order to see any output!!!
print tmpfile.read()

print "Closing tmpfile"
tmpfile.close()    
print tmpfile.closed

print "Finished"