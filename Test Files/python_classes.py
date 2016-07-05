#import numpy as np

class packet:
    def __init__(self):
        self.vectors = []
        self.resets = []
    
    def add_vector(self,vector):
        self.vectors.append(vector)

class block:
    def __init__(self):
        self.packetlist= []
    
    def addpacket(self,p):
        if not isinstance(p,packet):
            raise Exception("Not a packet")
        else:
            self.packetlist.append(p)