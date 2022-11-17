from server import Server
from cenas import getIPandPort



class SSServer(Server):
    
    def getDB(self):
        pass
        
    
    def __init__(self, spIP, domains, stList, logs):
        self.spIP, self.spPort = getIPandPort(spIP)
        super().__init__(domains, stList, logs,"SS",[self.spIP,self.spPort,-1])
        self.startServerUDP()
