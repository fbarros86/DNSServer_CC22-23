from cenas import getIPandPort
import socket
import time
from datetime import datetime
from pdu import PDU
from cache import Cache, entryOrigin
from cenas import decodeEmail,addSTsToCache
from logs import Logs


class SSServer:
    def __init__(self, spIP, domains, stList, logs,port, timeout):
        self.logs = logs
        l= self.logs["all"]
        self.spDomain = spIP[1]
        self.spIP, self.spPort = getIPandPort(spIP[0])
        self.cache = Cache()
        self.domains = domains
        self.spDomain = spIP[0]
        try:
            addSTsToCache(self.cache,stList)
        except: 
            l.addEntry(datetime.now(),"FL","@","Erro a ler ficheiro de dados")
        self.dbv = -1
        self.dbtime = -1
        self.texpire = -1
        self.timeout = timeout
        l.addEntry(datetime.now(),"SP","@","Debug")
        self.startUDPSS(port)

    def verifyVersion(self, s: socket.socket):
        msg = (PDU(name="DVB", typeofvalue="DBV"))
        l:Logs
        if (msg.name in self.logs): l= self.logs[msg.name]
        else: l= self.logs["all"]
        s.sendto(str(msg).encode("utf-8"), (self.spIP, int(self.spPort)))
        l.addEntry(datetime.now(),"QE",f"{self.spIP}:{self.spPort}",msg)
        msg = s.recv(1024)
        rsp = PDU(udp=msg.decode("utf-8"))
        l.addEntry(datetime.now(),"RR",f"{self.spIP}:{self.spPort}",rsp)
        return int(self.dbv) == int(rsp.name)

    def parseDBLine(self, i,msg:str):
        parameter = msg.split()
        l = len(parameter)
        id = parameter[0]
        if int(id) != i:
            return False
        p = parameter[1]
        s_type = parameter[2]
        value = parameter[3]
        ttl = 0
        order = None
        if l > 4:
            ttl = parameter[4]
        if l > 5:
            order = parameter[5]
        if s_type == "SOAADMIN":
            self.cache.addEntry(
                p, s_type, decodeEmail(value), ttl, order, entryOrigin.SP
            )
        else:
            self.cache.addEntry(p, s_type, value, ttl, order, entryOrigin.SP)
        return True

    def updateDB(self, sUDP: socket.socket,port):
        msg = PDU(name=self.spDomain, typeofvalue="SSDB")
        l:Logs
        if (msg.name in self.logs): l= self.logs[msg.name]
        else: l= self.logs["all"]
        sUDP.sendto(str(msg).encode("utf-8"), (self.spIP, int(self.spPort)))
        l.addEntry(datetime.now(),"QE",f"{self.spIP}:{self.spPort}",msg)
       
        msg = sUDP.recv(1024)
        rsp = PDU(udp=msg.decode("utf-8"))
        l.addEntry(datetime.now(),"RR",f"{self.spIP}:{self.spPort}",rsp)
        nLinhas = int(rsp.name)
        
        
        sUDP.sendto(msg, (self.spIP, int(self.spPort)))
        l.addEntry(datetime.now(),"QE",f"{self.spIP}:{self.spPort}",rsp)

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((socket.gethostname(), int(port)))
        s.listen()
        connection, address = s.accept()
        line = connection.makefile()
        for i in range(0, nLinhas):
            msg = line.readline()
            if not self.parseDBLine(i, msg):
                pass  # se não for por ordem
            # verificar se já passou o tempo definido
        l.addEntry(datetime.now(),"ZT",f"{self.spIP}:{self.spPort}","SS")
        connection.close()
        s.close()
        self.dbv = self.cache.getEntryTypeValue("SOASERIAL")
        self.dbtime = time.time()
        self.texpire = self.cache.getEntryTypeValue("SOAEXPIRE")
    
    def verifiyDomain(self,d:str):
        r = False
        for domain in self.domains:
            if d==domain:
                r=True
                break
            if d.endswith(domain):
                r=True
                break
        return r

    def handle_request(self,pdu:PDU, a , s:socket, l:Logs):
        if(pdu.response==3):
            s.sendto(str(pdu).encode("utf-8"), (a[0], int(a[1])))
            l.addEntry(datetime.now(),"ER",f"{a[0]}:{a[1]}","Erro a transformar String em PDU")
        elif (self.verifiyDomain(pdu.name)):
            # resposta à query
            pdu.rvalues = self.cache.getAllEntries(pdu.name, pdu.tov)
            pdu.nvalues = len(pdu.rvalues)
            pdu.auth = self.cache.getAllEntries(pdu.name, "NS")
            pdu.nauth = len(pdu.auth)
            # se tiver alguma coisa na cache
            if pdu.nvalues == 0 and pdu.nauth > 0:
                pdu.response = 1
            for v in pdu.rvalues:
                pdu.extra.extend(self.cache.getAllEntries(v.value, "A"))
            for v in pdu.auth:
                pdu.extra.extend(self.cache.getAllEntries(v.value, "A"))
            pdu.nextra = len(pdu.extra)
            s.sendto(str(pdu).encode("utf-8"), (a[0], int(a[1])))
            l.addEntry(datetime.now(),"RP",f"{a[0]}:{a[1]}",pdu)
        else:
            pdu.response=2
            pdu.auth = self.cache.getAllTypeEntries("NS")
            pdu.nauth = len(pdu.auth)
            for v in pdu.auth:
                pdu.extra.extend(self.cache.getAllEntries(v.value, "A"))
            pdu.nextra = len(pdu.extra)
            s.sendto(str(pdu).encode("utf-8"), (a[0], int(a[1])))
            l.addEntry(datetime.now(),"RP",f"{a[0]}:{a[1]}",pdu)

        

    def startUDPSS(self, port=3001):
        # abrir socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.bind((socket.gethostname(), int(port)))
        print(
            f"Listening in {socket.gethostbyname(socket.gethostname())}:{port}\n"
        )

        # receber queries
        while True:
            if (
                self.dbv == -1 or time.time() - float(self.dbtime) > float(self.texpire)
            ):
                if self.dbv == -1 or not self.verifyVersion(s):
                    self.updateDB(s,port)
                else:
                    self.dbtime = time.time()
            msg, a = s.recvfrom(1024)
            try:
                pdu = PDU(
                    msg.decode("utf-8")
                )
            except:
                pdu = PDU(error=3)
            l:Logs
            if (pdu.name in self.logs): l= self.logs[pdu.name]
            else: l= self.logs["all"]
            l.addEntry(datetime.now(),"QR",f"{a[0]}:{a[1]}",pdu)


            
        l= self.logs["all"]
        l.addEntry(datetime.now(),"SP","@","Paragem de SP")
