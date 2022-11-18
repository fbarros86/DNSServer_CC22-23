from cenas import getIPandPort
import socket
import time
from pdu import PDU
from cache import Cache, entryOrigin
from cenas import decodeEmail


class SSServer:
    def __init__(self, spIP, domains, stList, logs):
        self.spDomain = spIP[1]
        self.spIP, self.spPort = getIPandPort(spIP[0])
        self.cache = Cache()
        self.domains = domains  # adicionar à cache
        self.sts = stList
        self.logs = logs
        self.dbv = -1
        self.dbtime = -1
        self.texpire = -1
        self.startUDPSS()

    def parseDBLine(self, msg: str, i):
        parameter = msg.split()
        l = len(parameter)
        id = parameter[0]
        if id != i:
            return False
        p = parameter[1]
        s_type = parameter[2]
        value = parameter[3]
        ttl = 0
        order = None
        if l > 4:
            ttl = parameter[4]
        if l > 5:
            order = parameter[5]
        # acrescentar aos logs e ao standard output no caso do modo debug
        if s_type == "SOAADMIN":
            self.cache.addEntry(
                p, s_type, decodeEmail(value), ttl, order, entryOrigin.SP
            )
        else:
            self.cache.addEntry(p, s_type, value, ttl, order, entryOrigin.SP)
        return True

    def verifyVersion(self, s: socket.socket):
        msg = str(PDU(name="????", typeofvalue="DBV"))
        print("Going to send:")
        print(msg)
        print("\n")
        s.sendto(msg.encode("utf-8"), (self.spIP, int(self.spPort)))
        msg = s.recv(1024)
        print(f"Received a packet:")
        rsp = PDU(udp=msg.decode("utf-8"))
        print(rsp)
        print("\n")
        return self.dbv == int(rsp.name)

    def updateDB(self, sUDP: socket.socket):
        # ver a versão --> para dps
        msg = str(PDU(name="192.168.1.76:3001", typeofvalue="SSDB"))
        print("Going to send:")
        print(msg)
        print("\n")
        sUDP.sendto(msg.encode("utf-8"), (self.spIP, int(self.spPort)))
        msg = sUDP.recv(1024)
        print(f"Received a packet :")
        rsp = PDU(udp=msg.decode("utf-8"))
        print(rsp)
        print("\n")
        nLinhas = int(rsp.name)
        print("Going to send:")
        print(msg)
        print("\n")
        sUDP.sendto(msg, (self.spIP, int(self.spPort)))

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((self.spIP, int(self.spPort)))
        s.listen()
        connection, address = s.accept()
        line = connection.makefile()
        for i in range(0, nLinhas):
            msg = line.readline()
            if not self.parseDBLine(i, msg.decode("uft-8")):
                pass  # se não for por ordem
            # verificar se já passou o tempo definido
        connection.close()
        s.close()
        print(self.cache)

    def startUDPSS(self, port=3001):
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
            if (
                self.dbv == -1 or time.time() - self.dbtime > self.texpire
            ):  # e verificar se é preciso fazer refresh
                if self.dbv == 1 or not self.verifyVersion(s):
                    self.updateDB(s)
                else:
                    self.dbtime = time.time()
            msg, a = s.recvfrom(1024)
            print(f"Received a packet from {a}:")

            # processar pedido
            pdu = PDU(
                msg.decode("utf-8")
            )  # se não está completo esperar ou arranjar estratégia melhor
            print(pdu)
            print("\n")
            # resposta à query
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
            # ver para onde é para enviar se não tem a resposta
