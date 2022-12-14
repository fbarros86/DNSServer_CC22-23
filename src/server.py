import os
import sys
import time
from datetime import datetime
import sr, ss, sp
from logs import Logs


class InvalidConfig(Exception):
    pass


def verifyType(s_type):
    r = None
    if s_type == "DB":
        r = "SP"
    elif s_type == "SP":
        r = "SS"
    elif s_type == "SS":
        r = "SP"
    elif s_type == "DD":
        r = "all"
    elif s_type == "ST":
        r = "all"
    elif s_type == "LG":
        r = "all"
    return r


class InitServer:
    def __init__(self, confFile, port, timeout, ip, mode=1):# modo debug/normal - 0/1
        server_type=None
        parameters = []
        # ler ficheiro e dividir linhas
        with open(confFile, "r") as f:
            for line in f.readlines():
                if not (line[0] == "\n" or line[0] == "#"):
                    words = line.split()
                    parameters.append(words)
        transfSS = []  
        domains = []  
        logs = {}  # ficheiros de logs para registar a atividade
        stList = None
        for p, t, v in parameters:
            s_type = verifyType(t)
            if not s_type:
                raise InvalidConfig("Invalid type of value")
            if s_type != "all":
                if not server_type:
                    server_type = s_type
                elif server_type != s_type:
                    raise InvalidConfig("Confliting types of server")
            if t == "DB":
                db = v # caminho para ficheiro de base de dados
            elif t == "SP":
                spIP = (v, p) #(domínio do servidor primário, endereço do serrvidor primário(ip:port))
            elif t == "SS":
                transfSS.append(v) #lista para SS que podem pedir informação da bd
            elif t == "DD":
                domains.append((p,v)) # dd
            elif t == "ST":
                if p != "root":
                    raise InvalidConfig("ST parameter invalid")
                stList = v #caminho para o ficheiro com a lista dos STs
            elif t == "LG":
                if not os.path.exists(v):
                    f = open(v, "w")
                    f.close()
                logs[p] = Logs(v,mode) #criar objeto Logs com o path v e o modo mode
                logs[p].addEntry(datetime.now(),"EV","@","Ficheiro Logs Criado")
        if "all" not in logs:
            raise InvalidConfig("Missing log file by default")
        if not server_type:
            sr.SRServer(domains, stList, logs,port, timeout,ip)
        elif server_type == "SP":
            sp.SPServer(db, transfSS, domains, stList, logs,port, timeout,ip)
        else:
            ss.SSServer(spIP, domains, stList, logs,port, timeout,ip)

if len(sys.argv)>5 : InitServer(sys.argv[1],sys.argv[2],sys.argv[3],sys.argv[4],sys.argv[5])
else: InitServer(sys.argv[1],sys.argv[2],sys.argv[3],sys.argv[4])
# ficheiro de configuração, porta de atendimento, timeout, modo


# python3 server.py ../trabalhoCC/SS_Franz1/configsssfranz1.txt 3001 10
# python3 server.py ../trabalhoCC/SS_Iven1/configsssiven1.txt 3003 10

# python3 server.py ../trabalhoCC/SP_Iven/configtestSP.txt 3002 10
# python3 server.py ../trabalhoCC/SP_Franz/configtestSP.txt 3000 10
# python3 server.py ../trabalhoCC/SR_Iven/configtesteSR.txt 3004 10
# python3 server.py ../trabalhoCC/ST1/configtesteST1.txt 3005 10