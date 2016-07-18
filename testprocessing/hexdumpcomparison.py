#import os
#import numpy as np

length = 197

filephp = open('hexdumpphp.hex','rb')
filepython = open('hexdumppython.hex','rb')

True_count = 0
False_count = 0
Total = 0
c1t = filephp.read()
c2t = filepython.read()

filephp.close()
filepython.close()
linelist = []

for line in c1t:
    linelist.extend(line)

filteredline1 = [char for char in linelist if char != '\n']

print len(filteredline1),len(filteredline1)/64.

final1=[]
for i in range((len(filteredline1)/64)):
    final1.append(filteredline1[i*64:(i+1)*64])
    
print len(final1)

linelist = []

for line in c2t:
    linelist.extend(line)

filteredline2 = [char for char in linelist if char != '\n']

print len(filteredline2),len(filteredline2)/64.

final2=[]
for i in range((len(filteredline2)/64)):
    final2.append(filteredline2[i*64:(i+1)*64])

print len(final2)

strue = 0
ttrue = 0
ctrue = 0
otrue = 0

for l1,l2 in zip(final1,final2):
    s='Diff'
    t='Diff'
    c='Diff'
    o='Diff'
    print ""
    Total += 1
    if l1==l2:
        True_count+=1
        #print "Same"
    else:
        False_count+=1
        #print "Different"
    p1 = ''.join(l1[0:8])+' '+''.join(l1[8:24])+' '+''.join(l1[24:48])+' '+''.join(l1[48:66])+'-'.join(l1[66:])
    p2 = ''.join(l2[0:8])+' '+''.join(l2[8:24])+' '+''.join(l2[24:48])+' '+''.join(l2[48:66])+'-'.join(l2[66:])
    s1 = p1.split(' ')[0]
    t1 = p1.split(' ')[1]
    c1 = p1.split(' ')[2]
    o1 = p1.split(' ')[3]
    s2 = p2.split(' ')[0]
    t2 = p2.split(' ')[1]
    c2 = p2.split(' ')[2]
    o2 = p2.split(' ')[3]
    if s1 == s2:
        s='Same'
        strue+=1
    if t1 == t2:
        t='Same'
        ttrue += 1
    if c1 == c2:
        c='Same'
        ctrue +=1 
    if o1 == o2:
        o='Same'
        otrue += 1
        
    print p1
    print p2
    print '{0}     {1}             {2}                     {3}'.format(s,t,c,o)
    if otrue%7==0 and otrue>1:
        x = raw_input("Continue?")
        if x=='n' or x=='N' or x == '0':
            raise Exception("Interrupted by User")
    
print "Identical Lines        (/Total):",format(True_count,'03d'),'/',Total,' {:.3f}%'.format(float(True_count)*100./Total)
#print "Different Lines (/Total):",False_count,'/',Total,'        {:.3f}%'.format(float(False_count)*100./Total)

print "Identical Status       (/Total):",format(strue,'03d'),'/',Total,' {:.3f}%'.format(float(strue)*100./Total)
print "Identical Time         (/Total):",format(ttrue,'03d'),'/',Total,' {:.3f}%'.format(float(ttrue)*100./Total)
print "Identical Field Values (/Total):",format(ctrue,'03d'),'/',Total,' {:.3f}%'.format(float(ctrue)*100./Total)
print "Identical Remainder    (/Total):",format(otrue,'03d'),'/',Total,' {:.3f}%'.format(float(otrue)*100./Total)


