import fileinput
counter = 0 
for line in fileinput.input():
    counter += 1
    print "Line: ", counter
    print line,
    
print "Finished"