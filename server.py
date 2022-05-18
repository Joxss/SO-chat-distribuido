import socket
import threading
import queue
import sys
import random
import os
import pickle
import time

#Server Code
def RecvData(sock,recvPackets):
    while True:
        data,addr = sock.recvfrom(1024)
        recvPackets.put((data,addr))


SERVER_HOST = "192.168.1.107"
SERVER_PORT = 5000

print('Rodando server no endereço -> '+str(SERVER_HOST))
s = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
s.bind((SERVER_HOST,SERVER_PORT))
clients = set()
recvPackets = queue.Queue()

print('Server Running...')

threading.Thread(target=RecvData,args=(s,recvPackets)).start()

while True:
    data,addr = recvPackets.get()
    data = data.decode()
    print(f"<SERVER>: {data}")
    if data.endswith("connected") and addr not in clients:
        print(f"<SERVER>: Adicionando endereço {addr} na lista de endereços")
        clients.add(addr)
        continue

    if data.endswith("connected_list"):
        print(f"<SERVER>: Mandando lista de endereços para {addr}")
        s.sendto(pickle.dumps(clients),addr)
        continue

    if data.endswith('qqq'):
        print(f"<SERVER>: Removendo endereço {addr} da lista de endereços")
        clients.remove(addr)
        continue

s.close()
#Serevr Code Ends Here