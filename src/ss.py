from cache import Cache
from server import Server


class SSServer(Server):
    def __init__(self, domain, spIP, domains, stList, logs):
        super().__init__(domain, domains, stList, logs,"SS")
        self.sp = spIP
        self.startServerUDP()
