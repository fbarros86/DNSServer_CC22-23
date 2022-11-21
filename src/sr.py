from cache import Cache
from cenas import addSTsToCache


class SRServer:
    def __init__(self, domains, stList, logs,port, timeout):
        self.cache = Cache()
        self.domains = domains  # adicionar à cache
        addSTsToCache(self.cache,stList)
        self.logs = logs
        self.timeout = timeout
        # self.startServerUDP()
