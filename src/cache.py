"""
(a) parâmetro/Name
(b) tipo do valor/Type
(c) valor/Value
(d) tempo de validade/TTL 
(e) prioridade/Order
(f) origem da entrada/Origin(FILE, SP, OTHERS)
(g) tempo em segundos que passou desde o arranque do servidor até ao
momento em que a entrada foi registada na cache/TimeStamp
(h) número da entrada/Index (as entradas válidas são numeradas/indexadas de 1 até N, em que N é o número total de entradas na
cache, incluindo as entradas livres/FREE)
(i) estado da entrada/Status (FREE, VALID)

"""

from enum import Enum
import time


class entryState(Enum):
    FREE = "free"
    VALID = "valid"

class entryOrigin(Enum):
    FILE="file"
    SP="SP"
    OTHERS="others"



class CacheEntry:
    def __init__(self):
        self.state(entryState.FREE)

    def __init__(self,name,type,value,ttl,order,origin,timestamp,index,status):
        self.name=name
        self.type=type
        self.value=value
        self.ttl=ttl
        self.order=order
        self.origin=origin
        self.timestamp=timestamp
        self.index=index
        self.status=status
            


class Cache:

    def __init__(self):
        self.entries = [CacheEntry()]
        N=1
        validEntries=0
    
    def getEntry(self,index,name,type):
        for entry in self.entries:
            if (entry.status==entryState.VALID):
                if (entry.origin==entryOrigin.OTHERS and (time.time()-entry.timestamp > entry.ttl)):
                    entry.status=entryState.FREE
                elif (entry.index>=index):
                    if (entry.name==name and entry.type==type):
                        return entry.index
        return None
    

    def hasEntry(self,name,type,value,order):
        for entry in self.entries:
            if (entry.status==entryState.VALID):
                if (entry.origin==entryOrigin.OTHERS and (time.time()-entry.timestamp > entry.ttl)):
                    entry.status=entryState.FREE
                elif (entry.name==name and entry.type==type and entry.value==value and entry.order==order):
                    return entry
        return None

    def duplicateCache(self):
        pass
    
    def addEntry(self,name,type,value,ttl=20,order=None,origin=entryOrigin.OTHERS):
        if (self.validEntries==self.N): self.duplicateCache()
        if (origin!=entryOrigin.OTHERS):
            # primeira posição livre, timestamp do momento e status valid
                    pass
        else:
            e = self.hasEntry(name,type,value,order)
            if (not e):
                #última posição free, timestamp do momento e status valid
                pass
            elif(e.origin== entryOrigin.OTHERS):
                e.timestamp=time.time()
                e.status=entryState.VALID
    

    def setDomainFree(self,domain):
        for entry in self.entries:
            if (entry.name==domain): entry.status= entryState.FREE


            

