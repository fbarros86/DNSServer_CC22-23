import socket
from src.cache import Cache


class SSServer:
    def __init__(self,domain,spIP, domains, stList, logs):
        self.cache=Cache()
        self.domain = domain
        self.sp = spIP
        self.domains = domains
        self.sts = stList
        self.logs = logs
        self.startServer()
    
    def startServer():
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((socket.gethostname(), 1234))
        s.listen()
        while True:
            clientSock, address = s.accept()
