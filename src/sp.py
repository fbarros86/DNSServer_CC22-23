import socket
from src.parseServer import Server


class SPServer:

    def __init__(self, db, transfSS, domains, stList, logs):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((socket.gethostname(), 1234))
        s.listen()
        while True:
            clientSock, address = s.accept()
        pass
