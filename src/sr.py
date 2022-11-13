import socket
from cache import Cache
from server import Server


class SRServer(Server):
    def __init__(self, domain, domains, stList, logs):
        self.cache = Cache()
        self.domain = domain
        self.domains = domains  # adicionar à cache
        self.sts = stList
        self.logs = logs
        self.startServerUDP()
