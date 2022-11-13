import socket
from cache import Cache
from server import Server


class SSServer(Server):
    def __init__(self, domain, spIP, domains, stList, logs):
        self.cache = Cache()
        self.domain = domain
        self.sp = spIP
        self.domains = domains
        self.sts = stList
        self.logs = logs
        self.startServerUDP()
