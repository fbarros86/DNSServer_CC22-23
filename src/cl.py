import socket
import sys
from cenas import getIPandPort
from pdu import PDU


class Client:
    def __init__(self, ipServer, name, typeofvalue, flag=None):
        # enviar query para o servidor
        ip, port = getIPandPort(ipServer)
        if not port:
            port = 4000
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        datagram = PDU(name=name, typeofvalue=typeofvalue, flag=flag)
        s.sendto(str(datagram).encode("utf-8"), (ip, int(port)))

        # receber resposta
        s.bind(socket.gethostname(), port)
        msg, a = s.recvfrom(1024)

        # verificar se é a resposta ou é preciso reenviar a outro servidor


Client(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
