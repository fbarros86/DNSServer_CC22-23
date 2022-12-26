from pdu import PDU
import threading

class Logs:
    lock = threading.Lock()
    def __init__(self, path=None, mode=0):
        self.path = path
        self.mode = mode
        if path:
            with open(self.path, "w") as f:
                pass
        # por locks

    def addEntry(self,time,type, address, pdu:PDU):
        s= f"{time} {type} {address} {str(pdu)}\n"
        if (self.mode==0): print(s)
        if (self.path):
            with self.lock:
                with open(self.path, "a") as f:
                    f.write(s)
