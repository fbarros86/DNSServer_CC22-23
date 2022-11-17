from cenas import getIPandPort
import socket
from pdu import PDU
from cache import Cache,entryOrigin
from cenas import decodeEmail


class SSServer:
    
    def parseDBLine(self,msg:str,i):
        parameter = msg.split()
        l = len(parameter)
        id = parameter[0]
        if (id!=i): return False
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
    
    def atualizaDB(self,sUDP):
        # ver a versão --> para dps
        msg = str(PDU(name="enderecodele????",typeofvalue="SSDB"))
        sUDP.send(msg.encode('utf-8'))
        msg, a = sUDP.recv(1024)
        nLinhas = int(msg.encode('utf-8'))
        sUDP.send(msg)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.others[0], self.others[1]))
        line = s.makefile()
        for i in range(0,nLinhas):
            msg = line.readline()
            if not self.parseDBLine(i,msg.decode('uft-8')):
                pass # se não for por ordem 
            # verificar se já passou o tempo definido
        #se não acabou esperar e tentar outra vez
        s.close()
        
    
    def __init__(self, spIP, domains, stList, logs):
        self.spIP, self.spPort = getIPandPort(spIP)
        self.cache = Cache()
        self.domains = domains #adicionar à cache
        self.sts = stList
        self.logs = logs
        self.startUDPSS()
    
    def startServerUDP(self, port=None):
        # abrir socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        if not port:
            port = 1234
        s.bind((socket.gethostname(), port))
        print(f"Estou a  escuta no {socket.gethostbyname(socket.gethostname())}:{port}")

        # receber queries
        while True:
            if (self.sType=="SS"):
                if (self.others[2]==-1 ): #e verificar se é preciso fazer refresh
                    self.atualizaDB(s)
            msg, a = s.recvfrom(1024)
            print(f"Received a packet from {a}:")
            # guardar dados do cliente e mensagem quando introduzir paralelismo

            # abrir thread

            # processar pedido
            pdu = PDU(
                msg.decode("utf-8")
            )  # se não está completo esperar ou arranjar estratégia melhor
            print(pdu)
            if (pdu.tov=="SSDB"):
                if (self.sType == "SP"):
                    if (pdu.name in self.others):#verificar se o servidor que mandou tem permissões
                        pdu = PDU(name=str(self.getnlinhas()),typeofvalue="DBL")
            elif (pdu.tov=="LDB"):
                if (self.sType == "SP" and self.getnlinhas()==pdu.name):
                    self.sendDBLines()    
            # resposta à query
            pdu.rvalues = self.cache.getAllEntries(pdu.name, pdu.tov)
            pdu.nvalues = len(pdu.rvalues)
            pdu.auth = self.cache.getAllEntries(pdu.name, "NS")
            pdu.nauth = len(pdu.auth)
            # se tiver alguma coisa na cache
            if pdu.nvalues==0 and pdu.nauth>0:
                pdu.response=1
            for v in pdu.rvalues:
                pdu.extra.extend(self.cache.getAllEntries(v.value, "A"))
            for v in pdu.auth:
                pdu.extra.extend(self.cache.getAllEntries(v.value, "A"))
            pdu.nextra = len(pdu.extra)
            print("Going to send:")
            print(pdu)
            s.sendto(str(pdu).encode("utf-8"), (a[0], int(a[1])))
            # ver para onde é para enviar se não tem a resposta
