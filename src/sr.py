from cache import Cache


class SRServer:
    def __init__(self, domains, stList, logs):
        self.cache = Cache()
        self.domains = domains #adicionar à cache
        self.sts = stList
        self.logs = logs
        #self.startServerUDP()
    
    
