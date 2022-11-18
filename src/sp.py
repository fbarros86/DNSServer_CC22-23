import socket
from pdu import PDU
from cache import Cache, entryOrigin
from cenas import decodeEmail


class SPServer:
    def __init__(self, db, transfSS, domains, stList, logs):
        self.cache = Cache()
        self.db = db
        self.nlinhas = self.readDB()
        self.transfSS = transfSS
        self.domains = domains  # adicionar à cache
        self.sts = stList
        self.logs = logs
        self.starUDPSP()

    def readDB(
        self,
    ):
        parameters = []
        nlines = 0
        # ler ficheiro e dividir linhas
        with open(self.db, "r") as f:
            for line in f.readlines():
                if not (line[0] == "\n" or line[0] == "#"):
                    words = line.split()
                    parameters.append(words)
                    nlines += 1

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
        return nlines

    def sendDBLines(self, ip, port):
        i = 0
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        s.connect((ip, port))

        with open(self.db, "r") as f:
            for line in f.readlines():
                if not (line[0] == "\n" or line[0] == "#"):
                    msg = str(i) + " " + line
                    s.sendall(msg.encode("utf-8"))
                    i += 1
        print("Done sending DB lines\n")
        s.close()

    def hasTransferPermissions(self, a):
        return True
        return a in self.transfSS  # ver melhor isto

    def starUDPSP(self, port=3000):
        # abrir socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        if not port:
            port = 1234
        s.bind((socket.gethostname(), port))
        print(
            f"Estou a  escuta no {socket.gethostbyname(socket.gethostname())}:{port}\n"
        )

        # receber queries
        while True:
            msg, a = s.recvfrom(1024)
            print(f"Received a packet from {a}:")

            # processar pedido
            pdu = PDU(
                msg.decode("utf-8")
            )  # se não está completo esperar ou arranjar estratégia melhor
            print(pdu)
            print("\n")
            if pdu.tov == "DBV":
                version = self.cache.getEntryTypeValue("SOASERIAL")
                pdu.name = str(version)
                print("Going to send:")
                print(pdu)
                print("\n")
                s.sendto(str(pdu).encode("utf-8"), (a[0], int(a[1])))
            elif pdu.tov == "SSDB":
                if self.hasTransferPermissions(a):  # verificar name
                    pdu.name = str(version)
                    pdu.tov = "DBL"
                    s.sendto(str(pdu).encode("utf-8"), (a[0], int(a[1])))
            elif pdu.tov == "DBL":
                if self.nlinhas == pdu.name:
                    self.sendDBLines(port=port)
            # resposta à query
            else:
                pdu.rvalues = self.cache.getAllEntries(pdu.name, pdu.tov)
                pdu.nvalues = len(pdu.rvalues)
                pdu.auth = self.cache.getAllEntries(pdu.name, "NS")
                pdu.nauth = len(pdu.auth)
                # se tiver alguma coisa na cache
                if pdu.nvalues == 0 and pdu.nauth > 0:
                    pdu.response = 1
                for v in pdu.rvalues:
                    pdu.extra.extend(self.cache.getAllEntries(v.value, "A"))
                for v in pdu.auth:
                    pdu.extra.extend(self.cache.getAllEntries(v.value, "A"))
                pdu.nextra = len(pdu.extra)
                print("Going to send:")
                print(pdu)
                print("\n")
                s.sendto(str(pdu).encode("utf-8"), (a[0], int(a[1])))
