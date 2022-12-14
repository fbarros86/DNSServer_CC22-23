import socket
import threading
import time
from datetime import datetime
from pdu import PDU
from cache import Cache, entryOrigin
from cenas import decodeEmail,addSTsToCache
from logs import Logs


class SPServer:
    def __init__(self, db, transfSS, domains, stList, logs,port, timeout,ip):
        self.logs = logs
        self.ip = ip
        l:Logs
        l= self.logs["all"]
        l.addEntry(datetime.now(),"EV","@","Ficheiro de configuração lido")
        self.cache = Cache()
        self.db = db
        #try:
        self.nlinhas = self.readDB()
        #except:
        #    l.addEntry(datetime.now(),"FL","@","Erro a ler ficheiro de dados")
        l.addEntry(datetime.now(),"EV","@","Ficheiro de dados lido e armazenado em cache")
        self.transfSS = transfSS
        self.domains = domains
        try:
            addSTsToCache(self.cache,stList)
        except:
            l.addEntry(datetime.now(),"FL","@","Erro a ler ficheiro de dados")
        l.addEntry(datetime.now(),"EV","@","Ficheiro da lista dos STs lido e armazenado em cache")
        self.timeout = timeout
        l.addEntry(datetime.now(),"SP","@","Debug")
        self.starUDPSP(port)

    def defaultaux(self,default:dict, parameter:str):
        for key in default.keys():
            if key in parameter:
                parameter = parameter.replace(key,default[key])
        return parameter

    def defaultdot(self,default:dict, parameter):
        if not '@' in default:
            return parameter
        if parameter[-1] != '.':
            parameter+=default['@']
        return parameter

    def readDB(
        self,
    ):
        parameters = []
        nlines = 0
        default={}
        # ler ficheiro e dividir linhas
        with open(self.db, "r") as f:
            for line in f.readlines():
                if not (line[0] == "\n" or line[0] == "#"):
                    words = line.split()
                    parameters.append(words)
                    nlines += 1

        # adicionar à cache o conteúdo da base de dados
        for parameter in parameters:
            l = len(parameter)
            
            p=self.defaultaux(default,parameter[0])
            p=self.defaultdot(default,parameter[0])
                
            s_type=parameter[1]
            
            value = self.defaultaux(default,parameter[2])
            if s_type!="A":
                value = self.defaultdot(default,parameter[2])

            ttl = 0
            order = None
            if l > 3:
                ttl = self.defaultaux(default,parameter[3])
            if l > 4:
                order = self.defaultaux(default,parameter[4])
            # descodificar segundo macros
            if s_type == "DEFAULT":
                default[parameter[0]]=parameter[2]
            else:
                if s_type == "SOAADMIN":
                    self.cache.addEntry(
                        p, s_type, decodeEmail(value), ttl, order, entryOrigin.FILE
                    )
                else:
                    self.cache.addEntry(p, s_type, value, ttl, order, entryOrigin.FILE)
        return nlines

    def sendDBLines(self, s:socket.socket):
        i = 0
        s.listen()
        connection, address = s.accept()
        with open(self.db, "r") as f:
            for line in f.readlines():
                if not (line[0] == "\n" or line[0] == "#"):
                    msg = str(i) + " " + line
                    connection.sendall(msg.encode("utf-8"))
                    i += 1
        connection.close()

    def hasTransferPermissions(self, a):
        ss = f"{a[0]}:{a[1]}"
        b = ss in self.transfSS
        return b

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
            
    def handle_request(self,msg:bytes, a, s:socket,tcps:socket):
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
        if pdu.tov == "DBV":
            version = self.cache.getEntryTypeValue("SOASERIAL")
            pdu.name = str(version)
            s.sendto(pdu.encode(), (a[0], int(a[1])))
            l.addEntry(datetime.now(),"RP",f"{a[0]}:{a[1]}",pdu)
        elif pdu.tov == "SSDB":
            if self.hasTransferPermissions(a):  # verificar name
                pdu.name = str(self.nlinhas)
                pdu.tov = "DBL"
                s.sendto(pdu.encode(), (a[0], int(a[1])))
                l.addEntry(datetime.now(),"RP",f"{a[0]}:{a[1]}",pdu)
        elif pdu.tov == "DBL":
            if self.nlinhas == int(pdu.name):
                self.sendDBLines(tcps)
                l.addEntry(datetime.now(),"ZT",f"{a[0]}:{a[1]}","SP")
        elif(pdu.response==3):
            s.sendto(pdu.encode(), (a[0], int(a[1])))
            l.addEntry(datetime.now(),"ER",f"{a[0]}:{a[1]}","Erro a descodificar PDU")
        # resposta à query
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
        


    def starUDPSP(self, port=3000):
        # abrir socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        tcps = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((self.ip, int(port)))
        tcps.bind((self.ip, int(port)))
        # receber queries
        try:
            while True:
                msg, a = s.recvfrom(1024)
                t = threading.Thread(target=self.handle_request, args = (msg,a,s,tcps))
                t.start()
        except Exception as e:  
            s.close()
            tcps.close()        
            l= self.logs["all"]
            l.addEntry(datetime.now(),"SP","@","Paragem de SP - " + str(e))
        

