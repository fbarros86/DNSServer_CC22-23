from src import sr, ss, sp


class InvalidConfig(Exception):
    pass


class Server:
    def __init__(self, domain, server_type=None):
        parameters = []
        # ler ficheiro e dividir linhas
        with open(f".conf.{domain}", "r") as f:
            for line in f.readlines():
                if not (line[0] == "\n" or line == "#"):
                    words = line.split()
                    parameters.append(words)
        transfSS = []  # lista para SS que podem pedir informação da bd
        domains = (
            []
        )  # domínios para os quais o servidor responde ou encaminha para outro servidor
        logs = []  # ficheiros de logs para registar a atividade
        for p, t, v in parameters:
            s_type = self.verifyType(t)
            if not s_type:
                raise InvalidConfig("Invalid type of value")
            if s_type != "all":
                if not server_type:
                    server_type = s_type
                elif server_type != s_type:
                    raise InvalidConfig("Confliting types of server")
            if s_type == "DB":
                db = v  # é suposto verificar o parâmetro, que o domínio é igual???
            elif s_type == "SP":
                spIP = (v, p)
            elif s_type == "SS":
                transfSS.append(v)  # é suposto guardar o domínio??
            elif s_type == "DD":
                domains.append((v, p))
            elif s_type == "ST":
                if p != "all":
                    raise InvalidConfig("ST parameter invalid")
                stList = v
            elif s_type == "LG":
                logs.append((v, p))
        if not server_type:
            sr.SRServer(domains, stList, logs)
        elif server_type == "SP":
            sp.SPServer(db, transfSS, domains, stList, logs)
        else:
            ss.SSServer(spIP, domains, stList, logs)

    @staticmethod
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
