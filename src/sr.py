import socket
from cache import Cache
from cenas import addSTsToCache, getIPandPort
from cache import entryOrigin
from pdu import PDU
from logs import Logs
from datetime import datetime
import threading


class SRServer:
    def __init__(self, domains, stList, logs,port, timeout):
        self.cache = Cache()
        for domain,ip in domains:
            self.cache.addEntry(name=domain, type="ServerIP", value=ip,entryOrigin=entryOrigin.FILE)
        addSTsToCache(self.cache,stList)
        self.logs = logs
        self.timeout = timeout
        self.requests = {}
        self.startUDPSR(port)
    
    def handle_request(self,pdu:PDU, a, s:socket, l:Logs):
        if(pdu.response==3):
            s.sendto(str(pdu).encode("utf-8"), (a[0], int(a[1])))
            l.addEntry(datetime.now(),"ER",f"{a[0]}:{a[1]}","Erro a transformar String em PDU")
        # resposta à query
        elif (pdu.flagQ==True):
            if (self.cache.getEntry(0,pdu.name,"ServerIP")):
                entry = self.cache.getEntry(0,pdu.name,"ServerIP")
            else:
                entry = self.cache.getEntry(0,"ST","ST")
            entry = self.cache.entries[entry]          
            ip,port = getIPandPort(entry.value)
            pdu.flagQ=False
            if ((pdu.name,pdu.tov) not in self.requests): self.requests[(pdu.name,pdu.tov)]=[]
            self.requests[(pdu.name,pdu.tov)].append((a[0], int(a[1])))
            s.sendto(str(pdu).encode("utf-8"), (ip,int(port))) #no futuro se um dos sps/ipservers não der tentar outro???
            l.addEntry(datetime.now(),"QE",f"{ip}:{port}",pdu)
        else:
            if pdu.response==2:
                nexthop = None
                nexthopIP = None
                pduname = pdu.name
                while pduname and not nexthop:
                    for auth in pdu.auth:
                        n,_,v = auth.split(",")
                        if n==pduname:
                            nexthop = v
                            break
                    while not nexthop and pduname and pduname[0]!=".":
                        pduname = pduname[1:]
                for ipServer in pdu.extra:
                    n,_,v = ipServer.split(",")
                    if n==nexthop:
                        nexthopIP = v
                        break
                ip,port = getIPandPort(nexthopIP)
                new_pdu = PDU(name=pdu.name,typeofvalue=pdu.tov)
                new_pdu.flagA = pdu.flagA
                new_pdu.flagR = pdu.flagR
                new_pdu.flagQ = pdu.flagQ
                s.sendto(str(new_pdu).encode("utf-8"),(ip, int(port)))
                l.addEntry(datetime.now(),"QE",f"{ip}:{port}",new_pdu)  
            else:
                pdu.flagA = False
                for cli in self.requests[(pdu.name,pdu.tov)]:
                    s.sendto(str(pdu).encode("utf-8"),cli)
                    l.addEntry(datetime.now(),"QE",f"{cli[0]}:{cli[1]}",pdu)  
                    
            
            
                    
    def startUDPSR(self, port=3000):
         # abrir socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) #socket udp
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
            except Exception as e:
                pdu = PDU(error=3)
                print(e)
            l:Logs
            if (pdu.name in self.logs): l= self.logs[pdu.name]
            else: l= self.logs["all"]
            l.addEntry(datetime.now(),"QR",f"{a[0]}:{a[1]}",pdu)
            t = threading.Thread(target=self.handle_request, args = (pdu,a,s,l))
            #timer = threading.Timer(4.0, self.timeout, args=(t))
            #timer.start()
            t.start()                             
        l= self.logs["all"]
        l.addEntry(datetime.now(),"SP","@","Paragem de SR")      
