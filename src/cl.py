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
        msg, a = s.recvfrom(1024)
        m = msg.decode("utf-8")
        print(f"Received a packet from {a}:\n{m}")
        """rsp = PDU(udp=msg.decode("utf-8"))
        # se tiver que se reencaminhar
        if rsp.nvalues == 0:
            if PDU.flagR:
                PDU.flagR = False
            # enviar para o servidor que diz na query"""


Client(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
