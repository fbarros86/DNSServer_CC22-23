import socket
import time
from pdu import PDU
from cache import Cache, entryOrigin
from cenas import decodeEmail,addSTsToCache
from logs import Logs


class SPServer:
    def __init__(self, db, transfSS, domains, stList, logs,port, timeout):
        self.cache = Cache()
        self.db = db
        self.nlinhas = self.readDB()
        self.transfSS = transfSS
        self.domains = domains
        addSTsToCache(self.cache,stList)
        self.logs = logs
        self.timeout = timeout
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
            # acrescentar aos logs e ao standard output no caso do modo debug
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
        time.sleep(1)#esperar que abra -> está mal
        s.connect((ip, port))
        with open(self.db, "r") as f:
            for line in f.readlines():
                if not (line[0] == "\n" or line[0] == "#"):
                    msg = str(i) + " " + line
                    s.sendall(msg.encode("utf-8"))
                    i += 1
        s.close()

    def hasTransferPermissions(self, a):
        return True
        return a in self.transfSS  # ver melhor isto

    def verifiyDomain(self,d):
        r = False
        for ip,domain in self.domains:
            if d==domain:
                r=True
                break
        return r
            
    
    def starUDPSP(self, port=3000):
        # abrir socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        if not port:
            port = 1234
        s.bind((socket.gethostname(), port))
        print(
            f"Listening in {socket.gethostbyname(socket.gethostname())}:{port}"
        )

        # receber queries
        while True:
            msg, a = s.recvfrom(1024)

            # processar pedido
            pdu = PDU(
                msg.decode("utf-8")
            )  # se não está completo esperar ou arranjar estratégia melhor
            l:Logs
            if (pdu.name in self.logs): l= self.logs[pdu.name]
            else: l= self.logs["all"]
            l.addEntry(time.time(),"QR",a,pdu)
            if pdu.tov == "DBV":
                version = self.cache.getEntryTypeValue("SOASERIAL")
                pdu.name = str(version)
                s.sendto(str(pdu).encode("utf-8"), (a[0], int(a[1])))
                l.addEntry(time.time(),"RP",a,pdu)
            elif pdu.tov == "SSDB":
                if self.hasTransferPermissions(a):  # verificar name
                    pdu.name = str(self.nlinhas)
                    pdu.tov = "DBL"
                    s.sendto(str(pdu).encode("utf-8"), (a[0], int(a[1])))
                    l.addEntry(time.time(),"RP",a,pdu)
            elif pdu.tov == "DBL":
                if self.nlinhas == int(pdu.name):
                    self.sendDBLines(a[0],int(a[1]))
                    l.addEntry(time.time(),"ZT",a,"SP")
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
                l.addEntry(time.time(),"RP",a,pdu)


# python3 parseServer.py ../testFiles/configtest.txt