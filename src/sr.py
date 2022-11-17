from cache import Cache
from server import Server


class SRServer(Server):
    def __init__(self, domains, stList, logs):
        super().__init__( domains, stList, logs,"SR")
        self.startServerUDP()
