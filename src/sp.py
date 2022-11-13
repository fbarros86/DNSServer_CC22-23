import socket
from cache import Cache,entryOrigin,entryState
from pdu import PDU


# podia estar bem melhor, mas é o que é
def decodeEmail(email):
    new_email=""
    size=0
    beggining = True
    for i in range(len(email)):
        if (email[i]!="."):
            new_email+=email[i]
            size+=1
        elif(new_email[size-1]=="\\"):
            new_email = new_email[:-1]
            new_email+="."
        elif(beggining):
            new_email+="@"
            size += 1
            beggining=False
        else:
            new_email += email[i]
            size += 1            
    return new_email



class SPServer:
    
    def __init__(self, domain,db, transfSS, domains, stList, logs):
        self.cache=Cache()
        self.db=db
        self.domain=domain
        self.readDB()
        self.transfSS = transfSS
        self.domains = domains
        self.sts = stList
        self.logs = logs
        self.startServerUDP()


    def readDB(self,):
        parameters = []
        # ler ficheiro e dividir linhas
        with open(self.db, "r") as f:
            for line in f.readlines():
                if not (line[0] == "\n" or line == "#"):
                    words = line.split()
                    parameters.append(words)
        for parameter in parameters:
            l = len(parameter)
            p = parameter[0]
            s_type = parameter[1]
            value = parameter[2]
            ttl=0
            order=None
            if (l>3): ttl = parameter[3]
            if (l>4): order = parameter[4]
            #acrescentar aos logs e ao standard output no caso do modo debug
            #descodificar segundo macros
            if s_type == "DEFAULT":
                pass #não é obrigatório -> para implementar dps - é só substituir
            elif p.endswith(self.domain): 
                if s_type == "SOAADMIN":
                    self.cache.addEntry(p,s_type,decodeEmail(value),ttl,order,entryOrigin.FILE)
                else:
                    self.cache.addEntry(p,s_type,value,ttl,order,entryOrigin.FILE)

    
    def startServerUDP():
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.bind(socket.gethostname(), 1234)
        print(f"Estou a  escuta no {socket.gethostbyname(socket.gethostname())}:{1234}")
        while True:
            msg, clientAddress = s.recvfrom(1024)
            #abrir thread e processar pedido
            pdu = PDU(msg.decode('utf-8'))
            print(pdu)
            

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.bind((socket.gethostname(), 1234))
print(f"Estou a  escuta no {socket.gethostbyname(socket.gethostname())}:{1234}")
while True:
    msg, clientAddress = s.recvfrom(1024)
    print(clientAddress)
    #abrir thread e processar pedido
    pdu = PDU(udp=msg.decode('utf-8'))


