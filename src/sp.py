import socket
import time
from datetime import datetime
from pdu import PDU
from cache import Cache, entryOrigin
from cenas import decodeEmail,addSTsToCache
from logs import Logs


class SPServer:
    def __init__(self, db, transfSS, domains, stList, logs,port, timeout):
        self.logs = logs
        l:Logs
        l= self.logs["all"]
        l.addEntry(datetime.now(),"EV","@","Ficheiro de configuração lido")
        self.cache = Cache()
        self.db = db
        try:
            self.nlinhas = self.readDB()
        except:
            l.addEntry(datetime.now(),"FL","@","Erro a ler ficheiro de dados")
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
        
    def readDB(
        self,
    ):
        parameters = []
        nlines = 0
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
            p = parameter[0]
            s_type = parameter[1]
            value = parameter[2]
            ttl = 0
            order = None
            if l > 3:
                ttl = parameter[3]
            if l > 4:
                order = parameter[4]
            # descodificar segundo macros
            if s_type == "DEFAULT":
                pass  # não é obrigatório -> para implementar dps - é só substituir
            else:
                if s_type == "SOAADMIN":
                    self.cache.addEntry(
                        p, s_type, decodeEmail(value), ttl, order, entryOrigin.FILE
                    )
                else:
                    self.cache.addEntry(p, s_type, value, ttl, order, entryOrigin.FILE)
        return nlines

    def sendDBLines(self, ip, port):
        i = 0
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        time.sleep(1) #esperar que abra -> está mal
        s.connect((ip, port))
        with open(self.db, "r") as f:
            for line in f.readlines():
                if not (line[0] == "\n" or line[0] == "#"):
                    msg = str(i) + " " + line
                    s.sendall(msg.encode("utf-8"))
                    i += 1
        s.close()

    def hasTransferPermissions(self, a):
        ss = f"{a[0]}:{a[1]}"
        b = ss in self.transfSS
        return b

    def verifiyDomain(self,d):
        r = False
        for domain in self.domains:
            if d==domain:
                r=True
                break
        return r
            
    
    def starUDPSP(self, port=3000):
        # abrir socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.bind((socket.gethostname(), int(port)))
        print(
            f"Listening in {socket.gethostbyname(socket.gethostname())}:{port}"
        )

        # receber queries
        while True:
            msg, a = s.recvfrom(1024)
            # processar pedido
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
            if pdu.tov == "DBV":
                version = self.cache.getEntryTypeValue("SOASERIAL")
                pdu.name = str(version)
                s.sendto(str(pdu).encode("utf-8"), (a[0], int(a[1])))
                l.addEntry(datetime.now(),"RP",f"{a[0]}:{a[1]}",pdu)
            elif pdu.tov == "SSDB":
                if self.hasTransferPermissions(a):  # verificar name
                    pdu.name = str(self.nlinhas)
                    pdu.tov = "DBL"
                    s.sendto(str(pdu).encode("utf-8"), (a[0], int(a[1])))
                    l.addEntry(datetime.now(),"RP",f"{a[0]}:{a[1]}",pdu)
            elif pdu.tov == "DBL":
                if self.nlinhas == int(pdu.name):
                    self.sendDBLines(a[0],int(a[1]))
                    l.addEntry(datetime.now(),"ZT",f"{a[0]}:{a[1]}","SP")
            elif(pdu.response==3):
                s.sendto(str(pdu).encode("utf-8"), (a[0], int(a[1])))
                l.addEntry(datetime.now(),"ER",f"{a[0]}:{a[1]}","Erro a transformar String em PDU")
            # resposta à query
            elif (self.verifiyDomain(pdu.name)): #isto deve estar mal
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
        l= self.logs["all"]
        l.addEntry(datetime.now(),"SP","@","Paragem de SP")
        

# python3 parseServer.py ../testFiles/configtest.txt