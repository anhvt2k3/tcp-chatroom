import socket
import threading
import json
import tqdm
import os
import math

# Connection Data
host = '127.0.0.1'
port = 55555

BUFFER_SIZE = 1024

# Starting Server
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((host, port))
server.listen()

# Lists For Clients and Their Nicknames
clients = []
nicknames = []
nickname = ''
times = -1

# Sending Messages To All Connected Clients
def broadcast(message, sender):
    for client in clients:
        if client != sender:
            client.sendall(message)

def broadcastAll(message):
    for client in clients:
            client.sendall(message)

def broadcastCList():
    dataDict = {}
    dataDict['text'] = '\\update_list'
    dataDict['array'] = nicknames
    for client in clients:
            client.sendall(json.dumps(dataDict).encode())


def sendF2C(file_path, file_name, sender, pm = False, rcvNick = ""):
    dataDict = {
        'text' : None,
        'array': None
    }

    # print("\'{}\' _ \'{}\' _ {}".format(file_path, file_name, sender))
    idx = clients.index(sender)
    sendNick = nicknames[idx]

    if (not pm):
        file_size = os.path.getsize(file_path)
        dataDict['text'] = "\sendF <{}> ({}) -f {} -rcv public".format(sendNick, file_size, file_name)
        broadcast(json.dumps(dataDict).encode(), sender)

        with open(file_path, 'rb') as f:
            for i in range(times):
                data = f.read(1024)
                broadcast(data, sender)
                # print("i = {}".format(i))

    else:
        idx = nicknames.index(rcvNick)
        rcver = clients[idx]
        
        file_size = os.path.getsize(file_path)
        dataDict['text'] = "\sendF <{}> ({}) -f {} -rcv".format(sendNick, file_size, file_name)
        rcver.sendall(json.dumps(dataDict).encode())  
                  
        with open(file_path, 'rb') as f:              
            for i in range(times):
                data = f.read(1024)
                rcver.sendall(data)

    print("Done transfering file {}".format(file_name))



# Handling Messages From Clients
def handle(client):
    global times
    dataDict = {
            'text' : None,
            'array': None
        }
    while True:
        
        try:
            
            data = client.recv(4096)
            dataDict = json.loads(data.decode())
            idx = clients.index(client)
            message = dataDict['text']

            # Private chat handle
            if (message[:4] == "\\pm "):
                rcvNick = message[message.find('<') + 1 : message.find('>')]
                if not (rcvNick in nicknames):
                    dataDict['text'] = ">> \'{}\' is not existed!".format(rcvNick)
                    client.sendall(json.dumps(dataDict).encode())
                elif (rcvNick == clients[idx]):
                    dataDict['text'] = "Cannot send message to yourself"
                    client.sendall(json.dumps(dataDict).encode())
                else:
                    dataDict['text'] = "{} (PM): ".format(nicknames[idx]) + message[message.find('> ') + 2:]
                    idx = nicknames.index(rcvNick)
                    rcver = clients[idx]
                    rcver.sendall(json.dumps(dataDict).encode())
            

            elif (message[:7] == "\\sendF "):
                print("get sendF successfully")
                file_name = message[message.find('-f ') + 3:]
                # print(file_name)
                folder = "folder_server"
                if not os.path.exists(folder):
                    os.makedirs(folder)
                file_path = folder + '/' + file_name

                file_size = message[message.find(' (') + 2: message.find(') ')]
                # print(file_size)

                dataDict['text'] = '\\ready'
                client.sendall(json.dumps(dataDict).encode())

                print("Ready to receive ...")
                times =  math.ceil(int(file_size)/BUFFER_SIZE)
                # print("times = {}".format(times))
                with open(file_path, 'wb') as f:
                    """
                    while True:
                        data = client.recv(1024)
                        if (not data or data.decode() == '<END>'):
                            break
                        f.write(data)
                        print(i)
                        i += 1
                    """
                    
                    for i in range(times):
                        data = client.recv(1024)
                        f.write(data)
                        print("i = {}".format(i))
                
                print(">> File received and saved as:", file_path)
                print(">> Message: {}".format(message))

                if message[:14] == "\\sendF <@all> ":
                    sendF2C(file_path, file_name, client)
                else:
                    rcvNick = message[message.find('<') + 1 : message.find('>')]
                    sendF2C(file_path, file_name, client, True, rcvNick)

                if os.path.exists(file_path):
                    os.remove(file_path)
                    print(">> File \'{}\' deleted.".format(file_name))
                else:
                    print(">> File \'{}\' not found.".format(file_name))


            else:
                # Broadcasting Messages
                broadcast(json.dumps(dataDict).encode(), client)
                
                # Out room handle
                if (dataDict['text'] == nicknames[idx] + ': bye!'):
                    clients.remove(client)
                    dataDict['text'] = '\\close_all'
                    client.sendall(json.dumps(dataDict).encode())
                    client.close()
                    nickname = nicknames[idx]

                    dataDict['text'] = '>> {} left!'.format(nickname)
                    broadcast(json.dumps(dataDict).encode(), client)
                    
                    nicknames.remove(nickname)
                    break
        except:
            # Removing And Closing Clients
            idx = clients.index(client)
            clients.remove(client)
            client.close()
            nickname = nicknames[idx]
            dataDict['text'] = '{} left!'.format(nickname)
            broadcast(json.dumps(dataDict).encode(), client)
            
            nicknames.remove(nicknames[idx])
            break



# Receiving / Listening Function
def receive():
    dataDict = {
        'text' : None,
        'array': None
    }


    while True:
        # Accept Connection
        client, address = server.accept()
        print("Connected with {}".format(str(address)))
        
        # Request And Store Nickname
        dataDict['text'] = '\\get_nickname'
        dataDict['array'] = nicknames
        client.sendall(json.dumps(dataDict).encode())


        # Receive nick name from client
        data = client.recv(4096)
        dataDict = json.loads(data.decode())
        nickname = dataDict['text']

        nicknames.append(nickname)
        clients.append(client)

        # Print And Broadcast Nickname
        print("Nickname is {}".format(nickname))

        dataDict['text'] = ">> {} joined!".format(nickname)
        broadcast(json.dumps(dataDict).encode(), client)

        broadcastCList()

        dataDict['text'] = '>> Connected to server!'
        client.sendall(json.dumps(dataDict).encode())

        # Start Handling Thread For Client
        thread = threading.Thread(target = handle, args = (client,))
        thread.start()


print("Server is listening ...")
receive()