from cenas import getIPandPort
import socket
import time
from datetime import datetime
from pdu import PDU
from cache import Cache, entryOrigin
from cenas import decodeEmail,addSTsToCache
from logs import Logs
import threading
from contextlib import contextmanager
import signal

class TimeoutException(Exception): pass

@contextmanager
def time_limit(seconds):
    def signal_handler(signum, frame):
        raise TimeoutException("Timed out!")
    signal.signal(signal.SIGALRM, signal_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)



class SSServer:
    def __init__(self, spIP, domains, stList, logs,port, timeout,ip):
        self.ip = ip
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
        self.dbtime = -1 # tempo em que obteve a base de dados
        self.texpire = -1 # tempo para a bd expirar
        self.retry = 5
        self.soarefresh = 2
        self.timeout = timeout
        l.addEntry(datetime.now(),"SP","@","Debug")
        self.startUDPSS(port)

    def verifyVersion(self, s: socket.socket):
        if (self.dbv==-1): return False
        msg = (PDU(name="DVB", typeofvalue="DBV"))
        l:Logs
        if (msg.name in self.logs): l= self.logs[msg.name]
        else: l= self.logs["all"]
        s.sendto(msg.encode(), (self.spIP, int(self.spPort)))
        l.addEntry(datetime.now(),"QE",f"{self.spIP}:{self.spPort}",msg)
        msg = s.recv(1024)
        rsp = msg.decode()
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
        self.cache.setSPEntriesFree()
        msg = PDU(name=self.spDomain, typeofvalue="SSDB")
        l:Logs
        if (msg.name in self.logs): l= self.logs[msg.name]
        else: l= self.logs["all"]
        sUDP.sendto(msg.encode(), (self.spIP, int(self.spPort)))
        l.addEntry(datetime.now(),"QE",f"{self.spIP}:{self.spPort}",msg)
       
        msg = sUDP.recv(1024)
        rsp = PDU()
        rsp.decode(msg)
        l.addEntry(datetime.now(),"RR",f"{self.spIP}:{self.spPort}",rsp)
        nLinhas = int(rsp.name)
        
        
        sUDP.sendto(msg, (self.spIP, int(self.spPort)))
        l.addEntry(datetime.now(),"QE",f"{self.spIP}:{self.spPort}",rsp)

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.spIP,int(self.spPort)))
        
        line = s.makefile()
        for i in range(0, nLinhas):
            msg = line.readline()
            self.parseDBLine(i, msg)
        l.addEntry(datetime.now(),"ZT",f"{self.spIP}:{self.spPort}","SS")
        s.close()
        self.dbv = self.cache.getEntryTypeValue("SOASERIAL")
        self.texpire = self.cache.getEntryTypeValue("SOAEXPIRE")
        self.retry = self.cache.getEntryTypeValue("SOARETRY")
        self.soarefresh = self.cache.getEntryTypeValue("SOAREFRESH")
        self.dbtime = time.time()
    
    def verifiyDomain(self,d:str,tov):
        if (tov=="A"):
            while d and d[0]!=".": d = d[1:]
            if d:d = d[1:]
        r = False
        for domain,v in self.domains:
            if d==domain:
                r=True
                break
            if tov=="PTR" and d.endswith(domain):
                r=True
                break
        return r

    def handle_request(self,pdu:PDU, a , s:socket, l:Logs):
        if(pdu.response==3):
            s.sendto(pdu.encode(), (a[0], int(a[1])))
            l.addEntry(datetime.now(),"ER",f"{a[0]}:{a[1]}","Erro a descodificar PDU")
        elif (self.verifiyDomain(pdu.name,pdu.tov)):
            pdu.flagA=True
            pdu.rvalues = self.cache.getAllEntries(pdu.name, pdu.tov)
            pdu.nvalues = len(pdu.rvalues)
            pdu.auth = self.cache.getAllEntries(pdu.name, "NS")
            pdu.nauth = len(pdu.auth)
            pdu.response = 0
            # se tiver alguma coisa na cache
            if pdu.nvalues == 0 and pdu.nauth > 0:
                pdu.response = 1
            for v in pdu.rvalues:
                pdu.extra.extend(self.cache.getAllEntries(v.value, "A"))
            for v in pdu.auth:
                pdu.extra.extend(self.cache.getAllEntries(v.value, "A"))
            pdu.nextra = len(pdu.extra)
            if (pdu.nvalues == 0 and pdu.nauth == 0):
                pdu.flagA=False
                pdu.response=2
                pdu.auth = self.cache.getAllTypeEntries("NS")
                pdu.nauth = len(pdu.auth)
                for v in pdu.auth:
                    pdu.extra.extend(self.cache.getAllEntries(v.value, "A"))
                pdu.nextra = len(pdu.extra)
            s.sendto(pdu.encode(), (a[0], int(a[1])))
            l.addEntry(datetime.now(),"RP",f"{a[0]}:{a[1]}",pdu)
        else:
            pdu.response=2
            pdu.auth = self.cache.getAllTypeEntries("NS")
            pdu.nauth = len(pdu.auth)
            for v in pdu.auth:
                pdu.extra.extend(self.cache.getAllEntries(v.value, "A"))
            pdu.nextra = len(pdu.extra)
            s.sendto(pdu.encode(), (a[0], int(a[1])))
            l.addEntry(datetime.now(),"RP",f"{a[0]}:{a[1]}",pdu)

        

    def startUDPSS(self, port=3001):
        # abrir socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.bind((self.ip, int(port)))
        # receber queries
        try:
            while True:
                if (
                    self.dbv == -1 or time.time() - float(self.dbtime) > float(self.texpire)
                ):
                    flag=True
                    while (flag):
                        flag=False
                        try:
                            with time_limit(int(self.soarefresh)):
                                version = self.verifyVersion(s)
                            if not version:
                                with time_limit(int(self.timeout)):
                                    self.updateDB(s,port)
                            else:
                                self.dbtime = time.time()
                        except Exception as e:
                            self.logs["all"].addEntry(datetime.now(),"EZ",f"{self.spIP}:{self.spPort}","SS")
                            time.sleep(int(self.retry))
                            flag=True

                msg, a = s.recvfrom(1024)
                try:
                    pdu = PDU()
                    pdu.decode(msg)
                except Exception as e:
                    pdu = PDU(error=3)
                    print(e)
                l:Logs
                if (pdu.name in self.logs): l= self.logs[pdu.name]
                else: l= self.logs["all"]
                l.addEntry(datetime.now(),"QR",f"{a[0]}:{a[1]}",pdu)
                t = threading.Thread(target=self.handle_request, args = (pdu,a,s,l))
                t.start()  
        except Exception as e:
            s.close()
            l= self.logs["all"]
            l.addEntry(datetime.now(),"SP","@","Paragem de SS - " + str(e))
