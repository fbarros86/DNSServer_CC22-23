import socket
from src.cache import Cache

def readDB(db):
    with open(db, "r") as f:
            for line in f.readlines():
                if not (line[0] == "\n" or line == "#"):
                    words = line.split()

class SPServer:


    def __init__(self, db, transfSS, domains, stList, logs):
        cache=Cache()
        db=db
        self.readDB(db)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((socket.gethostname(), 1234))
        s.listen()
        while True:
            clientSock, address = s.accept()
        pass
