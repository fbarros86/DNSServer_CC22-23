import socket
import sys
from datetime import datetime
from cenas import getIPandPort
from pdu import PDU
from logs import Logs


class Client:
    def __init__(self, ipServer, name, typeofvalue, flag=None):
        # enviar query para o servidor
        ip, port = getIPandPort(ipServer)
        l = Logs()
        if not port:
            port = 4000
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        datagram = PDU(name=name, typeofvalue=typeofvalue, flag=flag)
        s.sendto(str(datagram).encode("utf-8"), (ip, int(port)))
        l.addEntry(datetime.now(),"QE",ipServer,datagram)

        # receber resposta
        msg, a = s.recvfrom(1024)
        m = msg.decode("utf-8")
        rsp = PDU(udp=m)
        l.addEntry(datetime.now(),"RR",a,rsp)


Client(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])

# python3 cl.py 192.168.1.76:3000 iven.franz. MX R
