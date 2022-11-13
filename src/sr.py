from cache import Cache
from server import Server


class SRServer(Server):
    def __init__(self, domain, domains, stList, logs):
        super().__init__(domain, domains, stList, logs,"SR")
        self.startServerUDP()
