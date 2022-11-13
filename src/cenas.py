def getIPandPort(ipServer):
    l = ipServer.split(":")
    if len(l) > 1:
        return l[0], l[1]
    else:
        return l[0], None
