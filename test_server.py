import socket
import threading
import json
import os
import math
import sys

# Connection Data
host = sys.argv[1]
port = sys.argv[2]

# Default
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

def getParent(name):
    global nicknames
    global clients

    i = nicknames.index(name)
    return clients[i]

def getChildIdx(clientStr, clientList):
    for _client in clientList:
        if (str(_client) == clientStr):
            return clientList.index(_client)
    
    return -1


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
                data = client.recv(BUFFER_SIZE)
                dataDict = json.loads(data.decode())
                message = dataDict['text']
                idx = clients.index(client)
                
            else:
                data = client.recv(BUFFER_SIZE)
                dataDict = json.loads(data.decode())
                message = dataDict['text']
                idx = clientList.index(client)                
                
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
                # print(file_name)
                
                # print("Ready to receive ...")
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
                # print(1)
                if (not pcr):
                    if (client in clients):
                        idx = clients.index(client)
                        clients.remove(client)
                        nickname = nicknames[idx]
                        address = addresses[idx]

                        nicknames.remove(nickname)
                        addresses.remove(address)

                        print("Disconnected with \'{}\': {}".format(nickname, address))

                    dataDict['text'] = "\\close_all"
                    client.sendall(json.dumps(dataDict).encode())
                    client.close()

                    dataDict['text'] = "\\getOut -n {}".format(nickname)
                    dataDict['array'] = nicknames
                    broadcast(json.dumps(dataDict).encode(), client, clients)

                else:
                    idx = clientList.index(client)
                    nickname = nickList[idx]
                    clientList.remove(client)
                    
                    # parent = getParent(nickname)
                    # dataDict['text'] = "\\update_pcrlist -"
                    # dataDict['array'] = str(client)
                    # parent.sendall(json.dumps(dataDict).encode())

                    dataDict['text'] = "\\getOut -n {}".format(nickname)
                    dataDict['array'] = nickList
                    broadcast(json.dumps(dataDict).encode(), client, clientList)

                    client.close()
                break
            
            elif (message == "\\pcr_updateList"):
                if (pcr):
                    if (client in clientList):
                        i = clientList.index(client)
                        tmp = clientList[-i + 1]
                        clientList.remove(clientList[-i + 1])
                        nickList.remove(nickList[-i + 1])

            elif (message == "\\parentCheck"):
                tmp = dataDict['array']

                dataDict['array'] = "False"
                if (tmp in nicknames):
                    dataDict['array'] = "True"

                client.sendall(json.dumps(dataDict).encode())

            else:
                # Broadcasting Messages
                if (not pcr):
                    broadcast(json.dumps(dataDict).encode(), client, clients)
                else:
                    broadcast(json.dumps(dataDict).encode(), client, clientList)


                # Out room handle
                if (not pcr and dataDict['text'] == nicknames[idx] + ": bye!"):
                    idx = clients.index(client)
                    clients.remove(client)
                    nickname = nicknames[idx]
                    address = addresses[idx]

                    nicknames.remove(nickname)
                    addresses.remove(address)

                    print("Disconnected with \'{}\': {}".format(nickname, address))

                    dataDict['text'] = "\\getOut -n {}".format(nickname)
                    dataDict['array'] = nicknames
                    broadcast(json.dumps(dataDict).encode(), client, clients)

                    dataDict['text'] = "\\close_all"
                    client.sendall(json.dumps(dataDict).encode())

                    # data = client.recv(BUFFER_SIZE)
                    # dataDict = json.loads(data.decode())
                    # pcr_clients = dataDict['array']
                    # for str in pcr_clients:
                    #     i = getChildIdx(str, clientList)
                    #     child = clientList[i]
                    #     dataDict['text'] = "\\quit"
                    #     child.sendall(json.dumps(dataDict).encode())

                    client.close()
                    break
                

                if (pcr and dataDict['text'] == nickList[idx] + ': bye!'):
                    if (client in clientList):
                        idx = clientList.index(client)
                        nickname = nickList[idx]
                        
                        clientList.remove(client)
                        nickList.remove(nickname)

                        dataDict['text'] = "\\close_all"
                        client.sendall(json.dumps(dataDict).encode())

                        parent = getParent(nickname)
                        dataDict['text'] = "\\update_pcrlist -"
                        dataDict['array'] = str(client)
                        parent.sendall(json.dumps(dataDict).encode())

                        dataDict['text'] = "\\getOut -n {}".format(nickname)
                        dataDict['array'] = nickList
                        broadcast(json.dumps(dataDict).encode(), client, clientList)

                    client.close()
                    break              
        
        except:
            # Removing And Closing Clients
            # print(3)
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
                
                dataDict['text'] = "\\getOut -n {}".format(nickname)
                dataDict['array'] = nicknames
                broadcast(json.dumps(dataDict).encode(), client, clients)
            else:
                if (client in clientList):
                    idx = clientList.index(client)         
                    nickname = nickList[idx]
                    nickList.remove(nickname)

                    # parent = getParent(nickname)
                    # dataDict['text'] = "\\update_pcrlist -"
                    # dataDict['array'] = str(client)
                    # parent.sendall(json.dumps(dataDict).encode())

                    dataDict['text'] = "\\getOut -n {}".format(nickname)
                    dataDict['array'] = nickList
                    broadcast(json.dumps(dataDict).encode(), client, clientList)

                client.close()
                pass

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

                parent = getParent(pcr_nicknames[0])
                dataDict['text'] = "\\update_pcrlist +"
                dataDict['array'] = str(pcr_clients[0])
                parent.sendall(json.dumps(dataDict).encode())

                parent = getParent(pcr_nicknames[1])
                dataDict['text'] = "\\update_pcrlist +"
                dataDict['array'] = str(pcr_clients[1])
                parent.sendall(json.dumps(dataDict).encode())

                pcr_nicknames = pcr_nicknames[2:]
                pcr_clients = pcr_clients[2:]


print("Server is listening ...")

receive()