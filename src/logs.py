from pdu import PDU

class Logs:
    def __init__(self, path, mode):
        self.path = path
        self.mode = mode
        # por locks

    def addEntry(self,time,type, address, pdu:PDU):
        s= f"{time} {type} {address} {str(pdu)}"
        if (self.mode==0): print(s)
        if (self.path):
            with open(self.path, "w") as f:
                f.write(s)
