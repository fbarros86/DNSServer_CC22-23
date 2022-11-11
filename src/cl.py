import socket
from src.cenas import getIPandPort
from src.query import Query


class Client:
    def __init__(self,ipServer,queryInfo,name,typeofvalue,flag=N):
        ip,port = getIPandPort(ipServer)
        if not port: port = 4000
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        msg = Query(queryInfo,name,typeofvalue,flag)
        s.sendto(msg.encode('utf-8'), (ip, port))
        