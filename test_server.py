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
SERVER_FOLDER = "folder_server"

# Starting Server
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((host, port))
server.listen()

# Lists For Clients and Their Nicknames
clients = []
nicknames = []
addresses = []


# Sending Messages To All Connected Clients
# def broadcast(message, sender, list = ""):
#     global clients
#     if list == "": 
#         list = clients

#     for rcver in list:
#         if rcver != sender:
#             rcver.sendall(message)

def broadcast(message, sender, rcvers):
    for rcver in rcvers:
        if rcver != sender:
            rcver.sendall(message)

def broadcastAll(message, clientList):
    for client in clientList:
            client.sendall(message)

def broadcastCList(rcvers, nicknameList):
    dataDict = {
        'text': None,
        'array': None
    }

    dataDict['text'] = '\\update_list'
    dataDict['array'] = nicknameList

    for rcver in rcvers:
            rcver.sendall(json.dumps(dataDict).encode())

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

def checkParent(pcr_client, pcr_clientList, pcr_nickList, nickList):
    idx = pcr_clientList.index(pcr_client)
    name = pcr_nickList[idx]
    if (name in nickList):
        return True
    else: return False

    pass


# Send folder to Client
def sendF2C(file_path, file_name, sender, clientList, nickList, pm = False, rcvNick = ""):
    global clients

    dataDict = {
        'text' : None,
        'array': None
    }

    # print("\'{}\' _ \'{}\' _ {}".format(file_path, file_name, sender))
    idx = clientList.index(sender)
    sendNick = nickList[idx]

    if (not pm):
        file_size = os.path.getsize(file_path)
        dataDict['text'] = "\\rcvF <{}> ({}) -f {} -rcv public".format(sendNick, file_size, file_name)
        broadcast(json.dumps(dataDict).encode(), sender, clientList)

        with open(file_path, 'rb') as f:
            for i in range(times):
                data = f.read(BUFFER_SIZE)
                broadcast(data, sender, clientList)
                # print("i = {}".format(i))

    else:
        idx = nickList.index(rcvNick)
        rcver = clientList[idx]
        
        file_size = os.path.getsize(file_path)
        dataDict['text'] = "\\rcvF <{}> ({}) -f {} -rcv".format(sendNick, file_size, file_name)
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
        # print(">> File \'{}\' deleted.".format(file_name))
    else:
        print(">> File \'{}\' not found.".format(file_name))




# Handling Messages From Clients
def handle(client, clientList, nickList, pcr = False):
    global times
    global nicknames
    global clients
    
    dataDict = {
        'text' : None,
        'array': None
    }
    
    while True:
        try:
            if (not pcr):
                # print("5")
                data = client.recv(BUFFER_SIZE)
                dataDict = json.loads(data.decode())
                message = dataDict['text']
                idx = clients.index(client)
                
            else:
                data = client.recv(BUFFER_SIZE)
                dataDict = json.loads(data.decode())
                message = dataDict['text']
                idx = clientList.index(client)
                
                if (not checkParent(client, clientList, nickList, nicknames)):
                    dataDict['text'] = '\\quit'
                    client.sendall(json.dumps(dataDict).encode())
                
                
            # Private chat handle
            if (message[:len("\\pm ")] == "\\pm "):
                rcvNick = message[message.find('<') + 1 : message.find('>')]
                dataDict['text'] = "{} (PM): ".format(nicknames[idx]) + message[message.find('> ') + 2:]
                idx = nicknames.index(rcvNick)
                rcver = clients[idx]
                rcver.sendall(json.dumps(dataDict).encode())
            
            elif (message[:len("\\sendF ")] == "\\sendF "):
                print("Get sendF successfully")
                file_name = message[message.find('-f ') + 3:]
                file_path = createDir(file_name)
                file_size = message[message.find(' (') + 2: message.find(') ')]
                print(file_name)
                
                print("Ready to receive ...")
                times =  math.ceil(int(file_size)/BUFFER_SIZE)
                with open(file_path, 'wb') as f:                    
                    for i in range(times):
                        data = client.recv(BUFFER_SIZE)
                        f.write(data)

                if message[:14] == "\\sendF <@all> ":
                    sendF2C(file_path, file_name, client, clientList, nickList, False, "")
                else:
                    rcvNick = message[message.find('<') + 1 : message.find('>')]
                    sendF2C(file_path, file_name, client, clientList, nickList, True, rcvNick)

                # Delete temporary file in folder_server
                cleanServerFolder(file_path, file_name)

            elif (message[:len("\\pcr ")] == "\\pcr "):
                if (message[:len("\\pcr -s")] == "\\pcr -s"):
                    sname = message[message.find("-s ") + 3: message.find(" -r")]
                    rname = message[message.find("-r ") + 3:]
                    
                    sender = client
                    ridx = nicknames.index(rname)
                    rcver = clients[ridx]
                    
                    dataDict['text'] = "\\invoke_pcr -n {}".format(sname)
                    rcver.sendall(json.dumps(dataDict).encode())
                    
                    dataDict['text'] = "\\invoke_pcr -n {}".format(rname)
                    sender.sendall(json.dumps(dataDict).encode())        

            elif (message == "\\hError"):
                if (not pcr):
                    if (client in clients):
                        idx = clients.index(client)
                        clients.remove(client)
                        nickname = nicknames[idx]
                        address = addresses[idx]

                        nicknames.remove(nickname)
                        addresses.remove(address)

                        print("Disconnected with \'{}\': {}".format(nickname, address))

                    dataDict['text'] = '\\close_all'
                    client.sendall(json.dumps(dataDict).encode())
                    client.close()

                    dataDict['text'] = '\\getOut -n {}'.format(nickname)
                    dataDict['array'] = nicknames
                    broadcast(json.dumps(dataDict).encode(), client, clients)

                else:
                    dataDict['text'] = '\\close_all'
                    client.sendall(json.dumps(dataDict).encode())
                    client.close()
                break

            else:
                # Broadcasting Messages
                if (not pcr):
                    broadcast(json.dumps(dataDict).encode(), client, clients)
                else:
                    broadcast(json.dumps(dataDict).encode(), client, clientList)


                # Out room handle
                if (dataDict['text'] == nicknames[idx] + ': bye!'):
                    if (not pcr):
                        if (client in clients):
                            idx = clients.index(client)
                            clients.remove(client)
                            nickname = nicknames[idx]
                            address = addresses[idx]

                        nicknames.remove(nickname)
                        addresses.remove(address)

                        print("Disconnected with \'{}\': {}".format(nickname, address))

                        dataDict['text'] = '\\close_all'
                        client.sendall(json.dumps(dataDict).encode())
                        client.close()

                        dataDict['text'] = '\\getOut -n {}'.format(nickname)
                        dataDict['array'] = nicknames
                        broadcast(json.dumps(dataDict).encode(), client, clients)

                    else:
                        dataDict['text'] = '\\close_all'
                        client.sendall(json.dumps(dataDict).encode())
                        client.close()
                    break
        
        except:
            # Removing And Closing Clients
            if (not pcr):
                if (client in clients):
                    idx = clients.index(client)
                    nickname = nicknames[idx]
                    address = addresses[idx]
                    
                    clients.remove(client)
                    addresses.remove(address)
                    nicknames.remove(nickname)

                    print("Disconnected with \'{}\': {}".format(nickname, address))

                client.close()            
                
                dataDict['text'] = '\\getOut -n {}'.format(nickname)
                dataDict['array'] = nicknames
                broadcast(json.dumps(dataDict).encode(), client, clients)
            else:
                dataDict['text'] = '\\close_all'
                client.sendall(json.dumps(dataDict).encode())
                client.close()
            break



# Receiving / Listening Function
def receive():
    dataDict = {
        'text' : None,
        'array': None
    }
    global clients
    global nicknames
    pcr_nicknames = []
    pcr_clients = []

    while True:
        # Accept connection
        client, address = server.accept()
        
        
        # Request and store nickname
        dataDict['text'] = '\\get_nickname'
        dataDict['array'] = nicknames
        client.sendall(json.dumps(dataDict).encode())

        

        # Receive nickname from client
        data = client.recv(BUFFER_SIZE)
        dataDict = json.loads(data.decode())
        nickname = dataDict['text']

        if (dataDict['array'] != 'pcr'):

            print("Connected with {}".format(str(address)))

            nicknames.append(nickname)
            clients.append(client)
            addresses.append(address)

            # Print and Broadcast Nickname
            print("\'{}\' joined".format(nickname))

            dataDict['text'] = ">> {} joined!".format(nickname)
            broadcast(json.dumps(dataDict).encode(), client, clients)
            broadcastCList(clients,nicknames)

            # Start Handling Thread For Client
            thread = threading.Thread(target = handle, args = (client, clients, nicknames, False,))
            thread.start()

        else:
            pcr_nicknames.append(nickname)
            pcr_clients.append(client)

            if (len(pcr_clients) >= 2):
                broadcastCList(pcr_clients[:2], pcr_nicknames[:2])
                for pcr_client in pcr_clients[:2]:
                    thread = threading.Thread(target = handle, args = (pcr_client, pcr_clients[:2], pcr_nicknames[:2], True,))
                    thread.start()

                pcr_nicknames = pcr_nicknames[2:]
                pcr_clients = pcr_clients[2:]


print("Server is listening ...")

receive()