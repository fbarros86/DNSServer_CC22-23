from cenas import getIPandPort
import socket
import time
from pdu import PDU
from cache import Cache, entryOrigin
from cenas import decodeEmail,addSTsToCache
from logs import Logs


class SSServer:
    def __init__(self, spIP, domains, stList, logs):
        self.spDomain = spIP[1]
        self.spIP, self.spPort = getIPandPort(spIP[0])
        self.cache = Cache()
        self.domains = domains
        addSTsToCache(self.cache,stList)
        self.logs = logs
        self.dbv = -1
        self.dbtime = -1
        self.texpire = -1
        self.startUDPSS()

    def verifyVersion(self, s: socket.socket):
        msg = (PDU(name="????", typeofvalue="DBV"))
        l:Logs
        if (msg.name in self.logs): l= self.logs[msg.name]
        else: l= self.logs["all"]
        s.sendto(str(msg).encode("utf-8"), (self.spIP, int(self.spPort)))
        l.addEntry(time.time(),"QE",f"{self.spIP}:{self.spPort}",msg)
        msg = s.recv(1024)
        rsp = PDU(udp=msg.decode("utf-8"))
        l.addEntry(time.time(),"RR",f"{self.spIP}:{self.spPort}",rsp)
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
        # acrescentar aos logs e ao standard output no caso do modo debug
        if s_type == "SOAADMIN":
            self.cache.addEntry(
                p, s_type, decodeEmail(value), ttl, order, entryOrigin.SP
            )
        else:
            self.cache.addEntry(p, s_type, value, ttl, order, entryOrigin.SP)
        return True

    def updateDB(self, sUDP: socket.socket,port):
        msg = PDU(name="192.168.1.76:3001", typeofvalue="SSDB")
        l:Logs
        if (msg.name in self.logs): l= self.logs[msg.name]
        else: l= self.logs["all"]
        sUDP.sendto(str(msg).encode("utf-8"), (self.spIP, int(self.spPort)))
        l.addEntry(time.time(),"QE",f"{self.spIP}:{self.spPort}",msg)
       
        msg = sUDP.recv(1024)
        rsp = PDU(udp=msg.decode("utf-8"))
        l.addEntry(time.time(),"RR",f"{self.spIP}:{self.spPort}",rsp)
        nLinhas = int(rsp.name)
        
        
        sUDP.sendto(msg, (self.spIP, int(self.spPort)))
        l.addEntry(time.time(),"QE",f"{self.spIP}:{self.spPort}",rsp)

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((socket.gethostname(), port))
        s.listen()
        connection, address = s.accept()
        line = connection.makefile()
        for i in range(0, nLinhas):
            msg = line.readline()
            if not self.parseDBLine(i, msg):
                pass  # se não for por ordem
            # verificar se já passou o tempo definido
        l.addEntry(time.time(),"ZT",f"{self.spIP}:{self.spPort}","SS")
        connection.close()
        s.close()
        self.dbv = self.cache.getEntryTypeValue("SOASERIAL")
        self.dbtime = time.time()
        self.texpire = self.cache.getEntryTypeValue("SOAREFRESH")
        print(self.cache)
    
    def verifiyDomain(self,d):
        r = False
        for ip,domain in self.domains:
            if d==domain:
                r=True
                break
        return r

    def startUDPSS(self, port=3001):
        # abrir socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        if not port:
            port = 1234
        s.bind((socket.gethostname(), port))
        print(
            f"Listening in {socket.gethostbyname(socket.gethostname())}:{port}\n"
        )

        # receber queries
        while True:
            print(time.time(),float(self.dbtime), float(self.texpire))
            if (
                self.dbv == -1 or time.time() - float(self.dbtime) > float(self.texpire)
            ):
                if self.dbv == 1 or not self.verifyVersion(s):
                    self.updateDB(s,port)
                else:
                    self.dbtime = time.time()
            msg, a = s.recvfrom(1024)
            pdu = PDU(
                msg.decode("utf-8")
            )  # se não está completo esperar ou arranjar estratégia melhor
            l:Logs
            if (pdu.name in self.logs): l= self.logs[pdu.name]
            else: l= self.logs["all"]
            l.addEntry(time.time(),"QR",a,pdu)
            if (self.verifiyDomain(pdu.name)):
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
                l.addEntry(time.time(),"RP",a,pdu)
                # ver para onde é para enviar se não tem a resposta
            else:
                pdu.response=3
                s.sendto(str(pdu).encode("utf-8"), (a[0], int(a[1])))
