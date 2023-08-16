import socket
import threading
import json
import os
import sys





# Connection Data
host = sys.argv[1] if len(sys.argv) > 2 else '127.0.0.1'
port = int(sys.argv[2]) if len(sys.argv) > 2 else 55555


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


# Sending Messages To All Connected Clients except the sender
def broadcast(message, sender, rcvers):
    for rcver in rcvers:
        if rcver != sender:
            rcver.sendall(message)

# Sending Messages To All Connected Clients
def broadcastAll(message, clientList):
    for client in clientList:
            client.sendall(message)

# Update list for all clients in list
def broadcastCList(rcvers, nicknameList):
    dataDict = {
        'text': None,
        'array': None
    }

    dataDict['text'] = '\\update_list'
    dataDict['array'] = nicknameList

    for rcver in rcvers:
            rcver.sendall(json.dumps(dataDict).encode())

# Send folder to Client
def sendF2C(file_path, file_name, sender, clientList, nickList, pm = False, rcvNick = ""):
    global clients
    dataDict = {
        'text' : None,
        'array': None
    }

    idx = clientList.index(sender)
    sendNick = nickList[idx]

    if (not pm):
        file_size = os.path.getsize(file_path)
        dataDict['text'] = "\\rcvF <{}> ({}) -f {} -rcv public".format(sendNick, file_size, file_name)
        broadcast(json.dumps(dataDict).encode(), sender, clientList)
    
        file = open(f'./{file_path}', "rb")
        broadcast(file.read(), sender, clientList)
        file.close()

    else:
        idx = nickList.index(rcvNick)
        rcver = clientList[idx]
        
        file_size = os.path.getsize(file_path)
        dataDict['text'] = "\\rcvF <{}> ({}) -f {} -rcv".format(sendNick, file_size, file_name)
        rcver.sendall(json.dumps(dataDict).encode())  

        file = open(f'./{file_path}', "rb")
        rcver.sendall(file.read())
        file.close()

# Create directory for server's folder
def createDir(file_name):
    folder = SERVER_FOLDER
    if not os.path.exists(folder):
        os.makedirs(folder)
    return folder + '/' + file_name

# Remove the inner file in folder_server
def cleanServerFolder(file_path, file_name):
    if os.path.exists(file_path):
        os.remove(file_path)
        # print(">> File \'{}\' deleted.".format(file_name))
    else:
        print(">> File \'{}\' not found.".format(file_name))

# Give the children socket of its parent
def getParent(name):
    global nicknames
    global clients

    i = nicknames.index(name)
    return clients[i]

# Check if the parent is alive
def checkParent(pcr_client, pcr_clientList, pcr_nickList, nickList):
    idx = pcr_clientList.index(pcr_client)
    name = pcr_nickList[idx]
    if (name in nickList):
        return True
    else: return False





# Handling messages from clients
def handle(client, clientList, nickList, pcr = False):
    global nicknames
    global clients
    
    dataDict = {
        'text' : None,
        'array': None
    }
    
    while True:
        try:
            data = client.recv(BUFFER_SIZE)
            dataDict = json.loads(data.decode())
            message = dataDict['text']
            idx = clients.index(client) if (not pcr) else clientList.index(client)    
                
            # Handke chatting privately in main chat room
            if (message[:len("\\pm ")] == "\\pm "):
                rcvNick = message[message.find('<') + 1 : message.find('>')]
                dataDict['text'] = "{} (PM): ".format(nicknames[idx]) + message[message.find('> ') + 2:]
                idx = nicknames.index(rcvNick)
                rcver = clients[idx]
                rcver.sendall(json.dumps(dataDict).encode())
            
            # Handle sending file
            elif (message[:len("\\sendF ")] == "\\sendF "):
                
                file_name = message[message.find('-f ') + 3:]
                file_path = createDir(file_name)
                file_size = int(message[message.find(' (') + 2: message.find(') ')])
                print("Receiving {}: in progress ...".format(file_name))

                chunk_size = int(dataDict['array'])

                file = open(file_path, "wb")
                chunk = client.recv(chunk_size)
                try: json.loads(chunk.decode())
                except: file.write(chunk)  
                file.close()

                if (pcr):
                    dataDict['text'] = "\\doneRecevingFile"
                    client.sendall(json.dumps(dataDict).encode())

                if message[:14] == "\\sendF <@all> ":
                    sendF2C(file_path, file_name, client, clientList, nickList, False, "")
                else:
                    rcvNick = message[message.find('<') + 1 : message.find('>')]
                    sendF2C(file_path, file_name, client, clientList, nickList, True, rcvNick)

                print("Done transfering file {}".format(file_name))

                # Delete temporary file in folder_server
                cleanServerFolder(file_path, file_name)

            # Invoke both sender and receiver to establish a PCR
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

            # Quit client when there is an error in client or unidentified parent of PCR
            elif (message == "\\exception" or message == "\\uParent"):
                if (not pcr):
                    if (client in clients):
                        idx = clients.index(client)
                        nickname = nicknames[idx]
                        address = addresses[idx]

                        clients.remove(client)
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

                    dataDict['text'] = "\\getOut -n {}".format(nickname)
                    dataDict['array'] = nickList
                    broadcast(json.dumps(dataDict).encode(), client, clientList)

                    client.close()
                break
            
            # Handle updating list for PCR
            elif (message == "\\pcr_updateList"):
                if (pcr):
                    if (client in clientList):
                        i = clientList.index(client)
                        tmp = clientList[-i + 1]
                        clientList.remove(clientList[-i + 1])
                        nickList.remove(nickList[-i + 1])

            # Check parent alive or not
            elif (message == "\\parentCheck"):
                tmp = dataDict['array']
                dataDict['array'] = "False"
                if (tmp in nicknames):
                    dataDict['array'] = "True"

                client.sendall(json.dumps(dataDict).encode())

            # Normal message
            else:
                # Broadcasting Messages
                if (not pcr):
                    broadcast(json.dumps(dataDict).encode(), client, clients)
                else:
                    broadcast(json.dumps(dataDict).encode(), client, clientList)


                # Handle exiting main chat room (MCR)
                if (not pcr and dataDict['text'] == nicknames[idx] + ": bye!"):
                    idx = clients.index(client)
                    clients.remove(client)
                    nickname = nicknames[idx]
                    address = addresses[idx]

                    nicknames.remove(nickname)
                    addresses.remove(address)

                    print("Disconnected with \'{}\': {}".format(nickname, address))
                    
                    dataDict['text'] = "\\close_all"
                    client.sendall(json.dumps(dataDict).encode())

                    dataDict['text'] = "\\getOut -n {}".format(nickname)
                    dataDict['array'] = nicknames
                    broadcast(json.dumps(dataDict).encode(), client, clients)

                    client.close()
                    break
                
                # Handle exiting private chat room (PCR)
                if (pcr and dataDict['text'] == nickList[idx] + ': bye!'):
                    idx = clientList.index(client)
                    nickname = nickList[idx]
                    
                    clientList.remove(client)
                    nickList.remove(nickname)

                    dataDict['text'] = "\\close_all"
                    client.sendall(json.dumps(dataDict).encode())

                    dataDict['text'] = "\\getOut -n {}".format(nickname)
                    dataDict['array'] = nickList
                    broadcast(json.dumps(dataDict).encode(), client, clientList)
                    
                    client.close()                
                    break              
        
        except:
            # Removing And Closing Clients
            if (not pcr):
                idx = clients.index(client)
                nickname = nicknames[idx]
                address = addresses[idx]
                
                clients.remove(client)
                addresses.remove(address)
                nicknames.remove(nickname)

                print("Disconnected with \'{}\': {}".format(nickname, address))
                
                dataDict['text'] = "\\getOut -n {}".format(nickname)
                dataDict['array'] = nicknames
                broadcast(json.dumps(dataDict).encode(), client, clients)

                client.close()
            else:
                if (client in clientList):
                    idx = clientList.index(client)         
                    nickname = nickList[idx]
                    nickList.remove(nickname)

                    dataDict['text'] = "\\getOut -n {}".format(nickname)
                    dataDict['array'] = nickList
                    broadcast(json.dumps(dataDict).encode(), client, clientList)

                client.close()

            break


# First receving from clients
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
        clients.append(client)
        addresses.append(address)
        
        # Receive nickname from client
        try:
            data = client.recv(BUFFER_SIZE)
            dataDict = json.loads(data.decode())
            nickname = dataDict['text']
            nicknames.append(nickname)
        except:
            clients.remove(client)
            addresses.remove(address)

        if (dataDict['array'] != 'pcr'):
            print("Connected with {}".format(str(address)))            

            # Print and Broadcast Nickname
            print("\'{}\' joined".format(nickname))

            dataDict['text'] = ">> {} joined!".format(nickname)
            broadcast(json.dumps(dataDict).encode(), client, clients)
            broadcastCList(clients,nicknames)

            # Start Handling Thread For Client
            thread = threading.Thread(target = handle, args = (client, clients, nicknames, False,))
            thread.start()

        else:
            nicknames.remove(nickname)
            clients.remove(client)
            addresses.remove(address)
            
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