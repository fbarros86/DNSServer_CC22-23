import random


class PDU:
    def __init__(self, udp=None, name=None, typeofvalue=None, flag=None):
        if udp:
            datagram = udp.split(";")
            header = datagram[0].split(",")
            data = datagram[1].split("\n")
            self.id = int(header[0])
            self.flag = header[1]
            self.parseFlags
            self.response = int(header[2])
            self.nvalues = int(header[3])
            self.nauth = int(header[4])
            self.nextra = int(header[5])
            queryInfo = data[0].split(",")
            self.name = queryInfo[0]
            self.tov = queryInfo[1]
            self.rvalues = []
            self.auth = []
            self.extra = []
            i = 1
            for _ in range(0, self.nvalues):
                self.rvalues.append(data[i])
                i += 1
            for _ in range(0, self.nauth):
                self.auth.append(data[i])
                i += 1
            for _ in range(0, self.nextra):
                self.extra.append(data[i])
                i += 1
        else:
            self.id = random.randint(1, 65535)
            self.flag = flag
            self.parseFlags()
            self.response = 0
            self.nvalues = 0
            self.nauth = 0
            self.nextra = 0
            self.name = name
            self.tov = typeofvalue
            self.rvalues = []
            self.auth = []
            self.extra = []

    def __repr__(self):
        header = f"{self.id},{self.flag},{self.response},{self.nvalues},{self.nauth},{self.nextra};"
        data = f"{self.name},{self.tov}\n"
        for r in self.rvalues:
            data += r + "\n"
        for r in self.auth:
            data += r + "\n"
        for r in self.extra:
            data += r + "\n"
        return header + data[:-1]

    def parseFlags(self):
        self.flagQ = False
        self.flagR = False
        self.flagA = False
        if self.flag:
            flags = self.flag.split("+")
            for f in flags:
                if f == "Q":
                    self.flagQ = True
                elif f == "R":
                    self.flagR = True
                elif f == "A":
                    self.flagA = True
