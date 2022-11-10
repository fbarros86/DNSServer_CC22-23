import socket
from src.cache import Cache


class SPServer:
    
    def __init__(self, db, transfSS, domains, stList, logs):
        self.cache=Cache()
        self.db=db
        self.readDB(db)
        self.transfSS = transfSS
        self.domains = domains
        self.sts = stList
        self.logs = logs
        self.startServer()


    def readDB(self,db):
        parameters = []
        # ler ficheiro e dividir linhas
        with open(db, "r") as f:
            for line in f.readlines():
                if not (line[0] == "\n" or line == "#"):
                    words = line.split()
                    parameters.append(words)
        for parameter in parameters:
            p = parameter[0]
            s_type = parameter[1]
            value = parameter[2]
            ttl = parameter[3]
            order = parameter[4]
            if s_type == "DEFAULT":
                pass #não é obrigatório -> para implementar dps
            elif s_type == "SOASP":
                pass
            elif s_type == "SOAADMIN":
                pass
            elif s_type == "SOSERIAL":
                pass
            elif s_type == "SOAREFRESH":
                pass
            elif s_type == "SOARETRY":
                pass
            elif s_type == "SOAEXPIRE":
                pass
            elif s_type == "NS":
                pass
            elif s_type == "A":
                pass
            elif s_type == "CNAME":
                pass
            elif s_type == "MX":
                pass
            elif s_type == "PTR":
                pass
    
    def startServer():
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((socket.gethostname(), 1234))
        s.listen()
        while True:
            clientSock, address = s.accept()

                        

