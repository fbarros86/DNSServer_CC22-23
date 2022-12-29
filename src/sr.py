import socket
from cache import Cache
from cenas import addSTsToCache, getIPandPort
from cache import entryOrigin
from pdu import PDU
from logs import Logs
from datetime import datetime
import threading
import time


class SRServer:
    
    def __init__(self, domains, stList, logs,port, timeout):
        self.cache = Cache()
        for domain,ip in domains:
            self.cache.addEntry(name=domain, type="ServerIP", value=ip,entryOrigin=entryOrigin.FILE)
        addSTsToCache(self.cache,stList)
        self.logs = logs
        self.timeout = int(timeout)
        self.requests = {}
        self.lock = threading.Lock()
        self.startUDPSR(port)
    
    def handle_request(self,pdu:PDU, s:socket, l:Logs, q:list):
        if(pdu.response==3):
            a,_ = self.requests[pdu.id]
            s.sendto(pdu.encode(), a)
            l.addEntry(datetime.now(),"ER",f"{a[0]}:{a[1]}","Erro a descodificar PDU")
        # resposta à query
        elif (pdu.flagQ==True):
            pdu.rvalues = self.cache.getAllEntries(pdu.name, pdu.tov)
            if (pdu.rvalues!=[]):
                pdu.flagQ = False
                pdu.nvalues = len(pdu.rvalues)
                pdu.auth = self.cache.getAllEntries(pdu.name, "NS")
                pdu.nauth = len(pdu.auth)
                pdu.response = 0
                for v in pdu.rvalues:
                    pdu.extra.extend(self.cache.getAllEntries(v.value, "A"))
                for v in pdu.auth:
                    pdu.extra.extend(self.cache.getAllEntries(v.value, "A"))
                pdu.nextra = len(pdu.extra)
                cli,_ = self.requests[pdu.id]
                s.sendto(pdu.encode(),cli)
                l.addEntry(datetime.now(),"QE",f"{cli[0]}:{cli[1]}",pdu)
            else:
                entries = self.cache.getAllEntries(pdu.name,"ServerIP")
                if (entries==[]):
                    entries = self.cache.getAllEntries("ST","ST")
                for entry in entries:
                    ip,port = getIPandPort(entry.value)
                    pdu.flagQ=False
                    if ((pdu.name,pdu.tov) not in self.requests): self.requests[(pdu.name,pdu.tov)]=[]
                    s.sendto(pdu.encode(), (ip,int(port)))
                    l.addEntry(datetime.now(),"QE",f"{ip}:{port}",pdu)
                    _,signal = self.requests[pdu.id]
                    signal: threading.Event
                    result = signal.wait(timeout=self.timeout)
                    if result:
                        with self.lock:
                            for p in q:
                                if p.id==pdu.id:
                                    new_pdu = p
                                    q.remove(p)
                                    break
                        self.handle_request(new_pdu,s,l,q)
                        break
        else:
            for rvalue in pdu.rvalues:
                res = rvalue.split(",")
                if (res[3]=="" and res[4]==""):  self.cache.addEntry(res[0],res[1],res[2])
                elif (res[4]==""):self.cache.addEntry(res[0],res[1],res[2],int(res[3]))
                elif (res[3]!=""):self.cache.addEntry(res[0],res[1],res[2],order=res[4])
                else:self.cache.addEntry(res[0],res[1],res[2],int(res[3]),res[4])
            for auth in pdu.auth:
                res = auth.split(",")
                if (res[3]=="" and res[4]==""):  self.cache.addEntry(res[0],res[1],res[2])
                elif (res[4]==""):self.cache.addEntry(res[0],res[1],res[2],int(res[3]))
                elif (res[3]!=""):self.cache.addEntry(res[0],res[1],res[2],order=res[4])
                else:self.cache.addEntry(res[0],res[1],res[2],int(res[3]),res[4])
            for ipServer in pdu.extra:
                res = ipServer.split(",")
                if (res[3]=="" and res[4]==""):  self.cache.addEntry(res[0],res[1],res[2])
                elif (res[4]==""):self.cache.addEntry(res[0],res[1],res[2],int(res[3]))
                elif (res[3]!=""):self.cache.addEntry(res[0],res[1],res[2],order=res[4])
                else:self.cache.addEntry(res[0],res[1],res[2],int(res[3]),res[4])
            if pdu.response==2:
                nexthop = []
                nexthopIP = []
                pduname = pdu.name
                while pduname and nexthop==[]:
                    for auth in pdu.auth:
                        res = auth.split(",")
                        n=res[0]
                        v=res[2]
                        if n==pduname:
                            nexthop.append(v)
                    while not nexthop and pduname and pduname[0]!=".":
                        pduname = pduname[1:]
                for ipServer in pdu.extra:
                    res = ipServer.split(",")
                    n=res[0]
                    v=res[2]
                    if n in nexthop:
                        nexthopIP.append(v)
                for next in nexthopIP:
                    ip,port = getIPandPort(next)

                    pdu.auth=[]
                    pdu.extra=[]
                    pdu.rvalues=[]
                    pdu.nauth=0
                    pdu.nextra=0
                    pdu.nvalues=0

                    s.sendto(pdu.encode(),(ip, int(port)))
                    l.addEntry(datetime.now(),"QE",f"{ip}:{port}",pdu)
                    _,signal = self.requests[pdu.id]
                    signal: threading.Event
                    result = signal.wait(timeout=self.timeout)
                    if result:
                        with self.lock:
                            for p in q:
                                if p.id==pdu.id:
                                    new_pdu = p
                                    q.remove(p)
                                    break
                        self.handle_request(new_pdu,s,l,q)
                        break
                
            else:
                pdu.flagA = False
                cli,_ = self.requests[pdu.id]
                s.sendto(pdu.encode(),cli)
                l.addEntry(datetime.now(),"QE",f"{cli[0]}:{cli[1]}",pdu)
            
            
                    
    def startUDPSR(self, port=3000):
        # abrir socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) #socket udp
        s.bind((socket.gethostname(), int(port)))
        print(
            f"Listening in {socket.gethostbyname(socket.gethostname())}:{port}"
        )
        q = list()
        # receber queries
        while True:
            msg, a = s.recvfrom(1024)
            # processar pedido
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
            if (pdu.id in self.requests):
                with self.lock:
                    q.append(pdu)
                _,signal = self.requests[pdu.id]
                signal.set()
                signal.clear()
            else:
                t = threading.Thread(target=self.handle_request, args = (pdu,s,l,q))
                signal = threading.Event()
                self.requests[pdu.id] = ((a[0],int(a[1])),signal)
                t.start()                           
            #timer = threading.Timer(4.0, self.timeout, args=(t))
            #timer.start()
        l= self.logs["all"]
        l.addEntry(datetime.now(),"SP","@","Paragem de SR")      
