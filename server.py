from pydoc import cli
from re import I
import socket
import threading
import queue
import sys
import random
import os
import pickle
import time

clients = set()
keepAlive = []
contador = 0
recvPackets = queue.Queue()

SERVER_PORT = 5000

def RecvDataMainLoop(sock,recvPackets, server_host):
    """
        Ouve mensagens referentes a novas conexões no sistema distribuido
    """
    while True:
        try:
            data,addr = sock.recvfrom(1024)
            data = data.decode()
            if data == "connected":
                clients.add(addr)
                sock.sendto("client-connected".encode(),(server_host,SERVER_PORT+1))
            if data == "connected_list":
                print(f"<SERVER>: Mandando lista de endereços para {addr}")
                sock.sendto(pickle.dumps(clients),addr)
            else:
                recvPackets.put((data,addr))
        except:
            pass

def mainLoop(server_host):
    """
        Funcao principal do servidor
    """
    print('Rodando server no endereço -> '+ str(server_host))
    s = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    s.bind((server_host,SERVER_PORT))

    threading.Thread(target=RecvDataMainLoop,args=(s,recvPackets, server_host)).start()

    while True:
        data,addr = recvPackets.get()
        print(f"<SERVER>: {data}")
        if data == "rebuild-tree":
            print("remontando arvore de encaminhamento")
            backup = clients.copy()
            clients.clear()
            for c in backup:
                try:
                    print(f"enviando msg para reconectar para {c}")
                    s.sendto("rebuild-tree".encode(),c)
                    s.sendto(pickle.dumps(clients),addr)
                    time.sleep(1)
                except:
                    pass


        if data.endswith("connected") and addr not in clients:
            print(f"<SERVER>: Adicionando endereço {addr} na lista de endereços")
            clients.add(addr)
            s.sendto("client-connected".encode(),(server_host,SERVER_PORT+1))
            continue

        if data.endswith('qqq'):
            print(f"<SERVER>: Removendo endereço {addr} da lista de endereços")
            clients.remove(addr)
            continue

    s.close()

def RecvDataCheckConnected(socket):
    """
        Funcao utilizada em thread em conjunto com a CheckConnectedLoop para ouvir as mensagens dos clientes
    """
    while True:
        try:
            data,addr = socket.recvfrom(1024)
            data = data.decode()
            if data == "keep-alive":
                keepAlive.append(addr)
                print(f"recebeu de {addr}")
            elif data == "client-connected":
                keepAlive.append(addr)

            elif data == "client-disconnected":
                keepAlive.remove(addr)
        except:
            pass

def checkConnectedLoop(server_host):
    """
        Envia uma mensagem a todos os nós e verifica se todos responderam. Caso algum nó não responda
        a uma mensagem para reconstruir a arvore é enviada aos nós remanescentes.
    """
    socketKeepAlive = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    socketKeepAlive.bind((server_host,SERVER_PORT+1))

    threading.Thread(target=RecvDataCheckConnected,args=(socketKeepAlive,)).start()
    while True:
        time.sleep(5)
        print("TESTANDO....")
        try:
            keepAlive.clear()
            for c in clients:
                print(f"enviando para {c}")
                socketKeepAlive.sendto("keep-alive".encode(),c)
        except:
            print("ERRO DURANTE VERIFICAÇÃO. DEIXADO PARA PROXIMA")
        time.sleep(5)

        if len(keepAlive) != len(clients):
            socketKeepAlive.sendto("rebuild-tree".encode(),(server_host,SERVER_PORT))
            print("DEU ERRO")

def main():
    
    if len(sys.argv) < 1:
        print("Argumentos insuficientes!")
        print("Uso: <ip>")
        os.exit(1)
    
    threading.Thread(target=mainLoop, args=(sys.argv[1],)).start()
    threading.Thread(target=checkConnectedLoop, args=(sys.argv[1],)).start()

if __name__ == "__main__":
    main()