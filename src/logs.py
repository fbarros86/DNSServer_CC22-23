from pdu import PDU

class Logs:
    def __init__(self, path=None):
        self.path = path
        # por locks

    def addEntry(self,time,type, address, pdu:PDU):
        s= f"{time} {type} {address} {str(pdu)}"
        print(s)
        if (self.path):
            with open(self.path, "w") as f:
                f.write(s)
