import socket
from cache import Cache
from cenas import addSTsToCache, getIPandPort
from cache import entryOrigin
from pdu import PDU
from logs import Logs
from datetime import datetime


class SRServer:
    def __init__(self, domains, stList, logs,port, timeout):
        self.cache = Cache()
        for domain,ip in domains:
            self.cache.addEntry(name=domain, type="ServerIP", value=ip,entryOrigin=entryOrigin.FILE)
        addSTsToCache(self.cache,stList)
        self.logs = logs
        self.timeout = timeout
        self.startUDPSR(port)
    
    def startUDPSR(self, port=3000):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) #socket udp
        s.bind((socket.gethostname(), int(port)))
        print(
            f"Listening in {socket.gethostbyname(socket.gethostname())}:{port}"
        )
        # receber queries
        while True:
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
                s.sendto(msg, (ip,port))
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
                        pass
                    else:
                        response = True
                s.sendto(str(pdu).encode("utf-8"),(a[0], int(a[1])))
                
                        
                    
                
        l= self.logs["all"]
        l.addEntry(datetime.now(),"SP","@","Paragem de SR")      
