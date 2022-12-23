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
        self.startUDPSR(port)
    
    def handle_request(self,pdu:PDU, a, s:socket, l:Logs):
        if(pdu.response==3):
            s.sendto(str(pdu).encode("utf-8"), (a[0], int(a[1])))
            l.addEntry(datetime.now(),"ER",f"{a[0]}:{a[1]}","Erro a transformar String em PDU")
        # resposta à query
        else:
            if (self.cache.getEntry(0,pdu.name,"ServerIP")):
                entry = self.cache.getEntry(0,pdu.name,"ServerIP")
            else:
                entry = self.cache.getEntry(0,"SP","SP")             
            ip,port = getIPandPort(entry.value)
            s.sendto(msg, (ip,port)) #no futuro se um dos sps/ipservers não der tentar outro???
            l.addEntry(datetime.now(),"QE",ip,pdu)
            response = False
            while (not response):
                msg, a = s.recvfrom(1024)
                try:
                    pdu = PDU(
                        msg.decode("utf-8")
                    )
                except:
                    pdu = str(pdu).encode("utf-8")
                    response=True
                if pdu.response==1:
                    nexthop = None
                    nexthopIP = None
                    for auth in pdu.auth:
                        n,_,v = auth.split(",")
                        if pdu.name.endswith(n):
                            nexthop = v
                            break
                    for ipServer in pdu.extra:
                        n,_,v = auth.split(",")
                        if ipServer==nexthop:
                            nexthopIP = v
                            break
                    ip,port = getIPandPort(nexthopIP)
                    s.sendto(str(pdu).encode("utf-8"),(ip, port))
                    l.addEntry(datetime.now(),"QE",ip,pdu)  
                else:
                    response = True
                    pdu.flagA = False
                    
            s.sendto(str(pdu).encode("utf-8"),(a[0], int(a[1])))
            l.addEntry(datetime.now(),"QE",ip,pdu)  
            
                    
    def starUDPSR(self, port=3000):
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
            except:
                pdu = PDU(error=3)
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
