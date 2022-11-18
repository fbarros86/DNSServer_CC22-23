import os
import sys
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
    def __init__(self, confFile, server_type=None):
        parameters = []
        # ler ficheiro e dividir linhas
        with open(confFile, "r") as f:
            for line in f.readlines():
                if not (line[0] == "\n" or line[0] == "#"):
                    words = line.split()
                    parameters.append(words)
        transfSS = []  # lista para SS que podem pedir informação da bd
        domains = []  # dd
        logs = {}  # ficheiros de logs para registar a atividade
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
                db = v
            elif t == "SP":
                spIP = (v, p)
            elif t == "SS":
                transfSS.append(v)
            elif t == "DD":
                domains.append((v, p))
            elif t == "ST":
                if p != "root":
                    raise InvalidConfig("ST parameter invalid")
                stList = v
            elif t == "LG":
                logs[p] = Logs(v)
                if not os.path.exists(v):
                    f = open(v, "w")
                    f.close()
        if "all" not in logs:
            raise InvalidConfig("Missing log file by default")
        if not server_type:
            sr.SRServer(domains, stList, logs)
        elif server_type == "SP":
            sp.SPServer(db, transfSS, domains, stList, logs)
        else:
            ss.SSServer(spIP, domains, stList, logs)


InitServer(sys.argv[1])
