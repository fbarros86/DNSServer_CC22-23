import random
import bitarray

class PDU:
    def __init__(self, udp=None, name="", typeofvalue="", flag=None, error=0):
        if udp:
            datagram = udp.split(";")
            header = datagram[0].split(",")
            data = datagram[1].split("\n")
            self.id = int(header[0])
            self.flag = header[1]
            self.parseFlags()
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
            self.flagQ=True
            self.response = error
            self.nvalues = 0
            self.nauth = 0
            self.nextra = 0
            self.name = name
            self.tov = typeofvalue
            self.rvalues = []
            self.auth = []
            self.extra = []

    def __repr__(self):
        self.flag = ""
        if self.flagQ: self.flag+="Q+"
        if self.flagR: self.flag+="R+"
        if self.flagA: self.flag+="A+"
        if self.flag!="": self.flag = self.flag[:-1]
        header = f"{self.id},{self.flag},{self.response},{self.nvalues},{self.nauth},{self.nextra};"
        data = f"{self.name},{self.tov}\n"
        for r in self.rvalues:
            data += str(r) + "\n"
        for r in self.auth:
            data += str(r) + "\n"
        for r in self.extra:
            data += str(r) + "\n"
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

    def encode (self):
        ba= bitarray.bitarray()
        self.addint(ba,0,16,int(self.id))
        if self.flagQ == False: 
            ba.append(0) 
        elif self.flagQ==True : 
            ba.append(1)
        
        if self.flagR == False : 
            ba.append(0) 
        elif self.flagR == True : 
            ba.append(1)
        
        if self.flagA == False : 
            ba.append(0) 
        elif self.flagA==True: 
            ba.append(1)   

        #precisa de 2 bits
        self.addint(ba,19,2,int(self.response))
        #precisa de 8 bits
        self.addint(ba,21, 8,int(self.nvalues))
        
        #precisa de 8 bits
        self.addint(ba,29,8,int(self.nauth))
        
        #precisa de 8 bits
        self.addint(ba,37,8, int(self.nextra))

        ba.frombytes(self.name.encode('utf-8'))
        comma = ","
        slashn = "\n"
        ba.frombytes(comma.encode('utf-8'))
        ba.frombytes(self.tov.encode('utf-8'))
        ba.frombytes(slashn.encode('utf-8'))
        for rv in self.rvalues:
            ba.frombytes(str(rv).encode('utf-8'))
            ba.frombytes(slashn.encode('utf-8'))
        #ba.frombytes(comma.encode('utf-8'))

        for au in self.auth:
            ba.frombytes(str(au).encode('utf-8'))
            ba.frombytes(slashn.encode('utf-8'))

        #ba.frombytes(comma.encode('utf-8'))

        for ex in self.extra:
            ba.frombytes(str(ex).encode('utf-8'))
            ba.frombytes(slashn.encode('utf-8'))
        return ba.tobytes()

    def decode (self, b):
        ba = bitarray.bitarray()
        ba.frombytes(b)
        
        self.id= int(ba[:16].to01(),base=2)

        if ba[16]==1:
            self.flagQ=True
        else:
            self.flagQ=False
        
        if ba[17]==1 :
            self.flagR=True
        else:
            self.flagR=False
        
        if ba[18]==1 :
            self.flagA=True
        else:
            self.flagA=False
      
        self.response = int(ba[19:21].to01(), base=2)
        self.nvalues=int(ba[21:29].to01(),base=2)
        self.nauth=int(ba[29:37].to01(),base=2)
        self.nextra=int(ba[37:45].to01(),base=2)
        codedstring = ba[45:]
        string = codedstring.tobytes().decode('utf-8')
        
        resto = string.split("\n")
        queryInfo = resto[0].split(",")

        self.name= queryInfo[0]
        self.tov = queryInfo[1]
        i=1
        self.rvalues = []
        self.auth = []
        self.extra = []
        if(self.nvalues>0):
            for _ in range(0, self.nvalues):
                self.rvalues.append(resto[i])
                i+=1
        if(self.nauth >0):
            for _ in range(0, self.nauth):
                self.auth.append(resto[i])
                i+=1
        if(self.nextra>0):
            for _ in range(0, self.nextra):
                self.extra.append(resto[i])
                i+=1

    def addint(self, ba, index, bits, number):
        # Convert the number to a bitarray
        number_ba = bitarray.bitarray(format(number, 'b').zfill(bits))

        # Insert the number_ba into the ba at the specified index
        ba[index:index+bits] = number_ba
