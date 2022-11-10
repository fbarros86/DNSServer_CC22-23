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
    def __init__(self,index):
        self.state(entryState.FREE)
        self.index=index

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
        self.entries = [CacheEntry(0)]
        self.N=1
        self.validEntries=0
        self.freeEntries = [0]
    
    def getEntry(self,index,name,type):
        for entry in self.entries:
            if (entry.status==entryState.VALID):
                if (entry.origin==entryOrigin.OTHERS and (time.time()-entry.timestamp > entry.ttl)):
                    entry.status=entryState.FREE
                    self.freeEntries.append(entry.index)
                    self.freeEntries.sort()
                elif (entry.index>=index):
                    if (entry.name==name and entry.type==type):
                        return entry.index
        return None
    

    def hasEntry(self,name,type,value,order):
        for entry in self.entries:
            if (entry.status==entryState.VALID):
                if (entry.origin==entryOrigin.OTHERS and (time.time()-entry.timestamp > entry.ttl)):
                    entry.status=entryState.FREE
                    self.freeEntries.append(entry.index)
                    self.freeEntries.sort()
                elif (entry.name==name and entry.type==type and entry.value==value and entry.order==order):
                    return entry
        return None

    def duplicateCache(self):
        oldN=self.N
        self.N*=2
        for i in range(oldN,self.N):
            self.entries.append(CacheEntry(i))
            self.freeEntries.append(i)
    
    def addEntry(self,name,type,value,ttl=20,order=None,origin=entryOrigin.OTHERS):
        if (self.validEntries==self.N): self.duplicateCache()
        if (origin!=entryOrigin.OTHERS):
            i = self.freeEntries.pop(0)
            self.validEntries+=1
            e = self.entries[i]
            e.name=name
            e.type=type
            e.value=value
            e.ttl=ttl
            e.order = None
            e.origin=origin
            e.timestamp=time.time()
            e.index=i
            e.status=entryState.VALID 
        else:
            e = self.hasEntry(name,type,value,order)
            if (not e):
                i = self.freeEntries.pop()
                e = self.entries[i]
                self.validEntries+=1
                e.name=name
                e.type=type
                e.value=value
                e.ttl=ttl
                e.order = None
                e.origin=origin
                e.timestamp=time.time()
                e.index=i
                e.status=entryState.VALID 
            elif(e.origin== entryOrigin.OTHERS):
                if (e.status==entryState.FREE):
                    self.freeEntries.remove(e.index)
                    self.validEntries+=1
                e.timestamp=time.time()
                e.status=entryState.VALID
    

    def setDomainFree(self,domain):
        for entry in self.entries:
            if (entry.name==domain):
                entry.status= entryState.FREE
                self.validEntries-=1
                self.freeEntries.append(entry.index)
        self.freeEntries.sort()


            

