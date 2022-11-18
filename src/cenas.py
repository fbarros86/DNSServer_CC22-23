from cache import Cache, entryOrigin

def getIPandPort(ipServer):
    l = ipServer.split(":")
    if len(l) > 1:
        return l[0], l[1]
    else:
        return l[0], None


# podia estar bem melhor, mas é o que é
def decodeEmail(email):
    new_email = ""
    size = 0
    beggining = True
    for i in range(len(email)):
        if email[i] != ".":
            new_email += email[i]
            size += 1
        elif new_email[size - 1] == "\\":
            new_email = new_email[:-1]
            new_email += "."
        elif beggining:
            new_email += "@"
            size += 1
            beggining = False
        else:
            new_email += email[i]
            size += 1
    return new_email

def addSTsToCache(c:Cache, STfile):
    with open(STfile, "r") as f:
        for line in f.readlines():
            if not (line[0] == "\n" or line[0] == "#"):
                c.addEntry(name="ST",type="ST",value=line,origin=entryOrigin.FILE)
