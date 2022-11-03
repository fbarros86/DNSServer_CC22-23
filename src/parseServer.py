from src.sr import initializeSR
from src.ss import initializeSS
from src.sp import initializeSP


class InvalidConfig(Exception):
    pass

def verifyType(type):
    r=None
    if (type=="DB"): r="SP"
    elif (type=="SP"): r="SS"
    elif (type=="SS"): r="SP"
    elif (type=="DD"): r="all"
    elif (type=="ST"): r="all"
    elif (type=="LG"): r="all"
    return r

def parseConf(domain):
    parameters = []
    #ler ficheiro e dividir linhas
    with open(f'.conf.{domain}','r') as f:
        for line in f.readlines():
            if not (line[0]=="\n" or line=="#"):
                words = line.split()
                parameters.append(words)
    serverType=None
    transfSS = [] #lista para SS que podem pedir informação da bd
    domains = [] #domínios para os quais o servidor responde ou encaminha para outro servidor
    logs = [] #ficheiros de logs para registar a atividade
    for p,t,v in parameters:
        type = verifyType(t)
        if (not type): raise InvalidConfig("Invalid type of value")
        if (type != "all"): 
            if (not serverType): serverType=type
            elif (serverType!=type): raise InvalidConfig("Confliting types of server")
        if (type=="DB"): db = v #é suposto verificar o parâmetro, que o domínio é igual???
        elif (type=="SP"): spIP = (v,p)
        elif (type=="SS"): transfSS.append(v) #é suposto guardar o domínio??
        elif (type=="DD"): domains.append((v,p))
        elif (type=="ST"):
            if (p!="all"): raise InvalidConfig("ST parameter invalid")
            stList = v
        elif (type=="LG"):logs.append((v,p))
    if (serverType==None): initializeSR(domains,stList,logs)
    elif (serverType=="SP"):initializeSP(db,transfSS,domains,stList,logs)
    else: initializeSS(spIP,domains,stList,logs)
        