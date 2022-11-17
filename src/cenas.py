def getIPandPort(ipServer):
    l = ipServer.split(":")
    if len(l) > 1:
        return l[0], l[1]
    else:
        return l[0], None
    
'''
    
#servidor
def processamento (connection, address):
    while True:
        msg = connection.recv(1024)

        if not msg:
            print("IJGWUGRHJG ODEIO REDES GJEWGUJWRGJWRUG")
            break
        
        print(msg.decode('utf-8'))
        print(f"Recebi uma ligação do cliente {address}")


    connection.close()

def main():    
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    endereco = '10.0.0.10'
    porta = 3333
    s.bind((endereco, porta ))
    s.listen()
    print(f"Estou à escuta no {endereco}:{porta}")



#cliente
    
import socket
import time

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

s.connect(('10.0.0.10', 3333))

msg = "Adoro Redes :)"

while True:
    s.sendall(msg.encode('utf-8'))
    time.sleep(1)
    
s.close()

'''
