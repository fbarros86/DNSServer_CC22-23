import socket

from pdu import PDU
from cache import Cache, entryOrigin


class Server:
    
    def __init__(self,domain, domains, stList, logs,type) -> None:
        self.cache = Cache()
        self.domain = domain
        self.domains = domains #adicionar à cache
        self.sts = stList
        self.logs = logs
        self.sType = type

    
    def startServerUDP(self, port=None):
        # abrir socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        if not port:
            port = 1234
        s.bind((socket.gethostname(), port))
        print(f"Estou a  escuta no {socket.gethostbyname(socket.gethostname())}:{port}")

        # receber queries
        while True:
            msg, a = s.recvfrom(1024)
            print(f"Received a packet from {a}:")

            # guardar dados do cliente e mensagem quando introduzir paralelismo

            # abrir thread

            # processar pedido
            pdu = PDU(
                msg.decode("utf-8")
            )  # se não está completo esperar ou arranjar estratégia melhor
            print(pdu)
            # resposta à query
            pdu.rvalues = self.cache.getAllEntries(pdu.name, pdu.tov)
            # se tiver alguma coisa na cache
            if pdu.rvalues != []:
                pdu.nvalues = len(pdu.rvalues)
                pdu.auth = self.cache.getAllEntries(pdu.name, "NS")
                pdu.nauth = len(pdu.auth)
                for v in pdu.rvalues:
                    pdu.extra.extend(self.cache.getAllEntries(v.value, "A"))
                for v in pdu.auth:
                    pdu.extra.extend(self.cache.getAllEntries(v.value, "A"))
                pdu.nextra = len(pdu.extra)
                print("Going to send:")
                print(pdu)
                s.sendto(str(pdu).encode("utf-8"), (a[0], int(a[1])))
            else:
                # ver para onde é para enviar para chegar a resultado da query

                # enviar para traz ou para próximo servidor
                if not pdu.flagR:
                    pass
                else:
                    pass
