from cache import Cache, entryOrigin
from server import Server


# podia estar bem melhor, mas é o que é
def decodeEmail(email):
    new_email = ""
    size = 0
    beggining = True
    for i in range(len(email)):
        if email[i] != ".":
            new_email += email[i]
            size += 1
        elif new_email[size - 1] == "\\":
            new_email = new_email[:-1]
            new_email += "."
        elif beggining:
            new_email += "@"
            size += 1
            beggining = False
        else:
            new_email += email[i]
            size += 1
    return new_email


class SPServer(Server):
    def __init__(self, domain, db, transfSS, domains, stList, logs):
        super().__init__(domain, domains, stList, logs,"SP")
        self.db = db
        self.readDB()
        self.transfSS = transfSS
        self.startServerUDP()

    def readDB(
        self,
    ):
        parameters = []
        # ler ficheiro e dividir linhas
        with open(self.db, "r") as f:
            for line in f.readlines():
                if not (line[0] == "\n" or line[0] == "#"):
                    words = line.split()
                    parameters.append(words)

        # adicionar à cache o conteúdo da base de dados
        for parameter in parameters:
            l = len(parameter)
            p = parameter[0]
            s_type = parameter[1]
            value = parameter[2]
            ttl = 0
            order = None
            if l > 3:
                ttl = parameter[3]
            if l > 4:
                order = parameter[4]
            # acrescentar aos logs e ao standard output no caso do modo debug
            # descodificar segundo macros
            if s_type == "DEFAULT":
                pass  # não é obrigatório -> para implementar dps - é só substituir
           # elif p.endswith(self.domain):
            else:
                if s_type == "SOAADMIN":
                    self.cache.addEntry(
                        p, s_type, decodeEmail(value), ttl, order, entryOrigin.FILE
                    )
                else:
                    self.cache.addEntry(p, s_type, value, ttl, order, entryOrigin.FILE)
