import threading
from enum import Enum
import time


class entryState(Enum):
    FREE = "free"
    VALID = "valid"


class entryOrigin(Enum):
    FILE = "file"
    SP = "SP"
    OTHERS = "others"


class CacheEntry:
    def __init__(self, index):
        self.status = entryState.FREE
        self.index = index
        self.name = None
        self.type = None
        self.value = None
        self.ttl = None
        self.order = None
        self.origin = None
        self.timestamp = None

    def __repr__(self):
        r = f"{self.name},{self.type},{self.value}"
        if self.ttl: r+=f",{self.ttl}"
        else:r+=","
        if self.order: r+=f",{self.order}"
        else:r+=","
        return r


class Cache:
    def __init__(self):
        self.entries = [CacheEntry(0)]
        self.N = 1
        self.validEntries = 0
        self.freeEntries = [0]
        self.lock = threading.Lock()

    def __repr__(self) -> str:
        r = ""
        for entry in self.entries:
            if (entry.status==entryState.VALID):
                r=r +str(entry)+ "\n"
        return r

    def getEntry(self, index, name, type):
        for i in range(index, self.N):
            entry = self.entries[i]
            if entry.status == entryState.VALID:
                if entry.origin == entryOrigin.OTHERS and (
                    time.time() - entry.timestamp > entry.ttl
                ):
                    entry.status = entryState.FREE
                    self.freeEntries.append(entry.index)
                    self.freeEntries.sort()
                elif entry.name == name and entry.type == type:
                    return entry.index
        return None

    def getAllEntries(self, name, type):
        with self.lock:
            i = 0
            entries = []
            while i != -1:
                v = self.getEntry(i, name, type)
                if v!=None:
                    entries.append(self.entries[v])
                    i = v + 1
                else:
                    i = -1
            return entries

    def hasEntry(self, name, type, value, order):
        for entry in self.entries:
            if entry.status == entryState.VALID:
                if entry.origin == entryOrigin.OTHERS and (
                    time.time() - entry.timestamp > entry.ttl
                ):
                    entry.status = entryState.FREE
                    self.freeEntries.append(entry.index)
                    self.freeEntries.sort()
                elif (
                    entry.name == name
                    and entry.type == type
                    and entry.value == value
                    and entry.order == order
                ):
                    return entry
        return None

    def getEntryTypeValue(self, type):
        with self.lock:
            for entry in self.entries:
                if entry.status == entryState.VALID:
                    if entry.origin == entryOrigin.OTHERS and (
                        time.time() - entry.timestamp > entry.ttl
                    ):
                        entry.status = entryState.FREE
                        self.freeEntries.append(entry.index)
                        self.freeEntries.sort()
                    elif entry.type == type:
                        return entry.value
            return None
    
    
    def getAllTypeEntries(self, type):
        with self.lock:
            r= []
            for entry in self.entries:
                if entry.status == entryState.VALID:
                    if entry.origin == entryOrigin.OTHERS and (
                        time.time() - entry.timestamp > entry.ttl
                    ):
                        entry.status = entryState.FREE
                        self.freeEntries.append(entry.index)
                        self.freeEntries.sort()
                    elif entry.type == type:
                        r.append(entry)
            return r

    def duplicateCache(self):
        oldN = self.N
        self.N *= 2
        for i in range(oldN, self.N):
            self.entries.append(CacheEntry(i))
            self.freeEntries.append(i)

    def addEntry(
        self, name, type, value, ttl=20, order=None, origin=entryOrigin.OTHERS
    ):
        with self.lock:

            if self.validEntries == self.N:
                self.duplicateCache()
            if origin != entryOrigin.OTHERS:
                i = self.freeEntries.pop(0)
                self.validEntries += 1
                e = self.entries[i]
                e.name = name
                e.type = type
                e.value = value
                e.ttl = ttl
                e.order = None
                e.origin = origin
                e.timestamp = time.time()
                e.index = i
                e.status = entryState.VALID
            else:
                e = self.hasEntry(name, type, value, order)
                if not e:
                    i = self.freeEntries.pop()
                    e = self.entries[i]
                    self.validEntries += 1
                    e.name = name
                    e.type = type
                    e.value = value
                    e.ttl = ttl
                    e.order = None
                    e.origin = origin
                    e.timestamp = time.time()
                    e.index = i
                    e.status = entryState.VALID
                elif e.origin == entryOrigin.OTHERS:
                    e.timestamp = time.time()

    def setSPEntriesFree(self):
        with self.lock:
            for entry in self.entries:
                if entry.status==entryState.VALID and entry.origin == entryOrigin.SP:
                    entry.status = entryState.FREE
                    self.validEntries -= 1
                    self.freeEntries.append(entry.index)
            self.freeEntries.sort()
