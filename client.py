import os
import sys
import socket
import threading
import pickle
import time
import queue
import random

SERVER_HOST = "191.52.64.158"
SERVER_PORT = 5000

"""
LISTA DE CONECTADOS. GUARDA APENAS OS ENDEREÇOS CONECTADOS AO ENDEREÇO DO SOCKET INICIALZADO (NÃO GUARDA TODOS OS ENDEREÇOS CONECTADOS AO SISTEMA)
"""
connected = [] 

def ReceiveData(sock,server):
    """
        Código da thread que fica rodando recebendo mensagens
    """
    while True:
        try:
            data,addr = sock.recvfrom(1024)
            dataDecoded = data.decode()

            if dataDecoded == "rebuild-tree":
                print("reconectando com o servidor")
                connected.clear()
                sock.sendto("connected_list".encode(),server) ## pede ao servidor uma lista com todos os endereços que participam do sistema
                connecteds, server_addr = sock.recvfrom(1024)
                connecteds = pickle.loads(connecteds)
                Connect(sock,connecteds, server)

            elif dataDecoded == "keep-alive":
                print("vericacao")
                sock.sendto("keep-alive".encode(),addr)

            elif dataDecoded == "connect": # OUTRO LADO CONECTOU COM ESSE ENDEREÇO
                print(f"CONEXAO ESTABELECIDA COM {addr}")
                connected.append(addr)

            elif dataDecoded == "latency": # OUTRO LADO ESTÁ TESTANDO A LETÊNCIA COM ESSE ENDEREÇO
                print(f"testando latencia com {addr}")
                sock.sendto("latency".encode(),addr)
            
            elif dataDecoded == "disconnect-self": ## MENSAGEM ENVIADA PELO PROPRIO ENDEREÇO PRA CHAMAR A FUNÇÃO DE DESCONECTAR DO SISTEMA
                Disconnect(sock)

            elif dataDecoded == "disconnect": ## DESCONCTA UM ENDEREÇO E SE CONECTA AOS OUTROS ENDEREÇO QUE ESTAVAM CONECTADOS NO ENDEREÇO DESLIGADO
                print(f"CONEXAO COM {addr} CORTADA")
                connected.remove(addr) ## remove o endereço que enviou a mensagem da lista de conectados
                data, addr = sock.recvfrom(1024) ## recebe do endereço q está se desconectando a lista de conectados daquele endereço
                otherAddr = pickle.loads(data)
                for address in otherAddr: ## loop que se conecta com os endereços que estavam conectados ao endereço q se desligou
                    print(f"CONEXAO ESTABELECIDA COM {address}")
                    sock.sendto("connect".encode(),address)
                    connected.append(address)
            
            elif dataDecoded == "disconnect-done": ## DESCONECTA UM ENDEREÇO
                print(f"CONEXAO COM {addr} CORTADA")
                connected.remove(addr)

            else: ## Mensagem recebida -> printa a mensagem na tela e repassa para a lista de sockets conectados
                print(f"<recebido de:{addr}> -- {dataDecoded}")
                for c in connected:
                    if c!= addr:
                        sock.sendto(data,c)
        except:
            pass

def Connect(sock: socket, connecteds, server):
    """
    """
    if len(connecteds) == 0: ## nenhum endereço retornado -> simplesmente diz ao servidor que se conectou
        sock.sendto("connected".encode(),server)
    else: ## lista de endereços retonada -> se conectar ao endereço com menor latência
        menor = 100000
        menor_addr = ()
        for c in connecteds: ## testa latência de cada endereço retornado
            start = time.time()
            sock.sendto("latency".encode(),c)
            sock.recvfrom(1024)
            end = time.time()
            if start-end < menor:
                menor = start-end
                menor_addr = c
        sock.sendto("connect".encode(),menor_addr) ## se conecta ao endereço com menor latência
        print(f"CONEXAO ESTABELECIDA COM {menor_addr}")
        connected.append(menor_addr)
        sock.sendto("connected".encode(),server) ## avisa ao servidor que se conectou ao sistema

def Disconnect(sock: socket):
    """
        Função para se desconectar do sistema
        Lógica: manda a lista de conectados para o primeiro endereço da lista, tal endereço se conecta com todos os demais endereços da lista.
        Os demais endereços simplesmente removem o endereço que está saindo do sistema de suas listas de conectados;
    """
    if len(connected) == 0:
        return
    first = connected[0]
    connected.remove(first)
    sock.sendto("disconnect".encode(),first) ## envia mensagem para o primeiro endereço sinalizando saida do sistema
    sock.sendto(pickle.dumps(connected),first) ## envia a lista com os demais endereços conectados para o primeiro endereço
    for c in connected:
        sock.sendto("disconnect-done".encode(),c) ## envia mensagem para os demais endereços sinalizando saida do sistema

def main():
    # Validando as entradas por CMD

    if len(sys.argv) < 3:
        print("Argumentos insuficientes!")
        print("Uso: <seu_ip> <sua_porta> <ip_servidor>")
        os.exit(1)

    clientHost = sys.argv[1]
    clientPort = sys.argv[2]
    serverHost = sys.argv[3]

    sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    HOST = clientHost
    PORT = int(clientPort)
    sock.bind((HOST,PORT))

    server = (serverHost,SERVER_PORT)

    print(f"Socket iniciado no endereço {sock.getsockname()}")

    name = input('Por favor forneca seu nome: ')

    sock.sendto("connected_list".encode(),server) ## pede ao servidor uma lista com todos os endereços que participam do sistema
    connecteds, server_addr = sock.recvfrom(1024)
    connecteds = pickle.loads(connecteds)

    Connect(sock, connecteds, server)

    threading.Thread(target=ReceiveData,args=(sock,server)).start()
    
    while True:
        data = input()
        if data == 'qqq': ## SAIR DO SISTEMA -> MANDA MENSAGEM PARA SI MESMO PARA A THREAD CHAMAR A FUNÇÃO DE DESCONECTAR
            sock.sendto("disconnect-self".encode(),(HOST,PORT))
            break
        elif data=='':
            continue
        data = '['+name+']' + '->'+ data
        for c in connected: ## repassa a mensagem digitada pelo usuário para todos os endereços na lista de conectados
            sock.sendto(data.encode(),c)
        sock.sendto(data.encode(),server)

    sock.sendto(data.encode(),server)
    time.sleep(5)
    sock.close()
    os._exit(1)


if __name__ == "__main__":
    main()

#Client Code Ends Here