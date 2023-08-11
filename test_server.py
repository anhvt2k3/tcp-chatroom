import socket
import threading
import json
import tqdm
import os
import math

# Connection Data
host = '127.0.0.1'
port = 55555

BUFFER_SIZE = 4096

# Starting Server
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((host, port))
server.listen()

# Lists For Clients and Their Nicknames
clients = []
nicknames = []
addresses = []

SERVER_FOLDER = "folder_server"

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

def targetSend(message, rname):
    i = nicknames.index(rname)
    rcver = clients[i]
    rcver.sendall(message)
    
def targetReceive(rname):
    dataDict = {
        'text' : None,
        'array': None
    }

    i = nicknames.index(rname)
    rcver = clients[i]
    data = rcver.recv(BUFFER_SIZE)
    dataDict = json.loads(data.decode())
    return dataDict



# Send folder to Client
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
                data = f.read(BUFFER_SIZE)
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
                data = f.read(BUFFER_SIZE)
                rcver.sendall(data)

    print("Done transfering file {}".format(file_name))

# Receive folder from Client
def recvFfromC(file_size, file_path, client):
    print("Ready to receive ...")
    times =  math.ceil(int(file_size)/BUFFER_SIZE)
    # print("times = {}".format(times))
    with open(file_path, 'wb') as f:                    
        for i in range(times):
            data = client.recv(BUFFER_SIZE)
            f.write(data)
            # print("i = {}".format(i))


def createDir(file_name):
    folder = SERVER_FOLDER
    if not os.path.exists(folder):
        os.makedirs(folder)
    return folder + '/' + file_name
    

def cleanServerFolder(file_path, file_name):
    if os.path.exists(file_path):
        os.remove(file_path)
        print(">> File \'{}\' deleted.".format(file_name))
    else:
        print(">> File \'{}\' not found.".format(file_name))




# Handling Messages From Clients
def handle(client):
    global times
    global nicknames

    dataDict = {
        'text' : None,
        'array': None
    }
    
    while True:
        try:
            data = client.recv(BUFFER_SIZE)
            dataDict = json.loads(data.decode())
            idx = clients.index(client)
            message = dataDict['text']

            # Private chat handle
            if (message[:len("\\pm ")] == "\\pm "):
                rcvNick = message[message.find('<') + 1 : message.find('>')]
                if not (rcvNick in nicknames):
                    dataDict['text'] = ">> \'{}\' is not existed!".format(rcvNick)
                    client.sendall(json.dumps(dataDict).encode())
                elif (rcvNick == nicknames[idx]):
                    dataDict['text'] = "Cannot send message to yourself"
                    client.sendall(json.dumps(dataDict).encode())
                else:
                    dataDict['text'] = "{} (PM): ".format(nicknames[idx]) + message[message.find('> ') + 2:]
                    idx = nicknames.index(rcvNick)
                    rcver = clients[idx]
                    rcver.sendall(json.dumps(dataDict).encode())
            
            elif (message[:len("\\sendF ")] == "\\sendF "):
                print("get sendF successfully")
                file_name = message[message.find('-f ') + 3:]
                
                print(file_name)
                
                file_path = createDir(file_name)

                file_size = message[message.find(' (') + 2: message.find(') ')]
                # print(file_size)

                dataDict['text'] = '\\ready -f {}'.format(file_name)
                client.sendall(json.dumps(dataDict).encode())

                # recvFfromC(file_size, file_path, client)
                print("Ready to receive ...")
                times =  math.ceil(int(file_size)/BUFFER_SIZE)
                # print("times = {}".format(times))
                with open(file_path, 'wb') as f:                    
                    for i in range(times):
                        data = client.recv(BUFFER_SIZE)
                        f.write(data)
                        # print("i = {}".format(i))

                if message[:14] == "\\sendF <@all> ":
                    sendF2C(file_path, file_name, client)
                else:
                    rcvNick = message[message.find('<') + 1 : message.find('>')]
                    sendF2C(file_path, file_name, client, True, rcvNick)

                # Delete temporary file in folder_server
                cleanServerFolder(file_path, file_name)
                """
                if os.path.exists(file_path):
                    os.remove(file_path)
                    print(">> File \'{}\' deleted.".format(file_name))
                else:
                    print(">> File \'{}\' not found.".format(file_name))
                """

            elif (message[:len("\\pChat ")] == "\\pChat "):
                if (message[:len("\\pChat -s")] == "\\pChat -s"):
                    sname = message[message.find("-s ") + 3: message.find(" -r")]
                    rname = message[message.find("-r ") + 3:]

                    sidx = nicknames.index(sname)
                    ridx = nicknames.index(rname)
                    sender = clients[sidx]
                    rcver = clients[ridx]

                    print("-s {} -r {}".format(sname, rname))
                    
                    dataDict['text'] = "\\pChat join? -s {}".format(sname)
                    rcver.sendall(json.dumps(dataDict).encode())
                    

                    data = rcver.recv(BUFFER_SIZE)
                    dataDict = json.loads(data.decode())
                    message = dataDict['text']

                    if (message == "Y"):
                        dataDict['text'] = "\pChat -begin {}".format(sname)
                        rcver.sendall(json.dumps(dataDict).encode())

                        dataDict['text'] = "\pChat -begin {}".format(rname)
                        rcver.sendall(json.dumps(dataDict).encode())


                    else:
                        dataDict['text'] = "{} do not want to have private chat with you :((".format(rcver)
                        client(json.dumps(dataDict).encode())

            elif (message == "\\hError"):
                idx = clients.index(client)
                nickname = nicknames[idx]
                address = addresses[idx]

                addresses.remove(address)
                clients.remove(client)
                nicknames.remove(nickname)

                dataDict['text'] = '\\close_all'
                client.close()
                print("Disconnected with \'{}\': {}".format(nickname, address))

                dataDict['text'] = '\\getOut -n {}'.format(nickname)
                dataDict['array'] = nicknames
                broadcast(json.dumps(dataDict).encode(), client)

            else:
                # Broadcasting Messages
                broadcast(json.dumps(dataDict).encode(), client)
                
                # Out room handle
                if (dataDict['text'] == nicknames[idx] + ': bye!'):
                    clients.remove(client)
                    nickname = nicknames[idx]
                    nicknames.remove(nickname)
                    address = addresses[idx]
                    addresses.remove(address)

                    print("Disconnected with \'{}\': {}".format(nickname, address))

                    dataDict['text'] = '\\close_all'
                    client.sendall(json.dumps(dataDict).encode())
                    client.close()

                    dataDict['text'] = '\\getOut -n {}'.format(nickname)
                    dataDict['array'] = nicknames
                    broadcast(json.dumps(dataDict).encode(), client)
                    
                    break
        
        except:
            # Removing And Closing Clients
            idx = clients.index(client)
            nickname = nicknames[idx]
            address = addresses[idx]

            addresses.remove(address)
            clients.remove(client)
            nicknames.remove(nickname)

            print("Disconnected with \'{}\': {}".format(nickname, address))

            client.close()            
            
            dataDict['text'] = '\\getOut -n {}'.format(nickname)
            dataDict['array'] = nicknames
            broadcast(json.dumps(dataDict).encode(), client)

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
        addresses.append(address)

        # Print And Broadcast Nickname
        print("New member: \'{}\'".format(nickname))

        dataDict['text'] = ">> {} joined!".format(nickname)
        broadcast(json.dumps(dataDict).encode(), client)

        broadcastCList()

        dataDict['text'] = '>> Connected to server!'
        client.sendall(json.dumps(dataDict).encode())

        # Start Handling Thread For Client
        thread = threading.Thread(target = handle, args = (client,))
        thread.start()


def write():
    global server
    while True:
        inp = input("")
        if (inp == "\shutdown"):
            print("Server is shutting down...")
            server.close()


print("Server is listening ...")

# write_thread = threading.Thread(target = write)
# write_thread.start()

receive()