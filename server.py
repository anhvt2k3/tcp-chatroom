import socket
import threading
import pickle
import json

# Connection Data
host = '192.168.1.27'
port = 49153

# Starting Server
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((host, port))
server.listen()

# Lists For Clients and Their Nicknames
clients = []
nicknames = []
nickname = ''
room = {
    'id': None,
    'members': None # list of members' sockets
}

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
    dataDict["text"] = '\\update_list'
    dataDict["array"] = nicknames
    for client in clients:
            client.sendall(json.dumps(dataDict).encode())


def privateChat():
    print("privateChat()")


# Handling Messages From Clients
def handle(client):
    while True:
        dataDict = {
            "text" : None,
            "array": None,
            'room': 'default'
        }
        try:
            
            data = client.recv(4096)
            dataDict = json.loads(data.decode())
            idx = clients.index(client)
            message = dataDict["text"]

            # Private chat handle
            if (message[:4] == "\\pm "):
                rcvNick = message[message.find('<') + 1 : message.find('>')]
                if not (rcvNick in nicknames):
                    dataDict["text"] = ">> \'{}\' is not existed!".format(rcvNick)
                    client.sendall(json.dumps(dataDict).encode())
                else:
                    dataDict["text"] = "{} (PM): ".format(nicknames[idx]) + message[message.find('-m ') + 3:]
                    idx = nicknames.index(rcvNick)
                    rcver = clients[idx]
                    rcver.sendall(json.dumps(dataDict).encode())
            else:
                # Broadcasting Messages
                broadcast(json.dumps(dataDict).encode(), client)
                
                # Out room handle
                if (dataDict["text"] == nicknames[idx] + ': bye!'):
                    clients.remove(client)
                    dataDict["text"] = '\\close_all'
                    client.sendall(json.dumps(dataDict).encode())
                    client.close()
                    nickname = nicknames[idx]

                    dataDict["text"] = '>> {} left!'.format(nickname)
                    broadcast(json.dumps(dataDict).encode(), client)
                    
                    nicknames.remove(nickname)
                    break
        except:
            # Removing And Closing Clients
            idx = clients.index(client)
            clients.remove(client)
            client.close()
            nickname = nicknames[idx]
            dataDict["text"] = '{} left!'.format(nickname)
            broadcast(json.dumps(dataDict).encode(), client)
            
            nicknames.remove(nicknames[idx])
            break


# Receiving / Listening Function
def receive():
    dataDict = {
        "text" : None,
        "array": None
    }


    while True:
        # Accept Connection
        client, address = server.accept()
        print("Connected with {}".format(str(address)))
        
        # Request And Store Nickname
        dataDict["text"] = '\\get_nickname'
        client.sendall(json.dumps(dataDict).encode())


        # Receive nick name from client
        data = client.recv(4096)
        dataDict = json.loads(data.decode())
        nickname = dataDict["text"]
        if nickname in nicknames:
            dataDict["text"] = "\\available_nickname"
            dataDict["array"] = nicknames
            client.sendall(json.dumps(dataDict).encode())
            data = client.recv(4096)
            dataDict = json.loads(data.decode())
            nickname = dataDict["text"]
        nicknames.append(nickname)
        clients.append(client)

        # Print And Broadcast Nickname
        print("Nickname is {}".format(nickname))

        dataDict["text"] = ">> {} joined!".format(nickname)
        broadcast(json.dumps(dataDict).encode(), client)

        broadcastCList()
        
        # broadcastList()

        dataDict["text"] = '>> Connected to server!'
        client.sendall(json.dumps(dataDict).encode())

        # Start Handling Thread For Client
        thread = threading.Thread(target = handle, args = (client,))
        thread.start()

def newchatroom():
# having 2 chatters
# each chatroom should have an id
# chatroom can be created by:
# 1. (separate server) having different port on the same ip
# 2. having a thread for each chatroom
# choosing the 2nd way, 'cause it's hard :)
# and better expandabillity
# this version support only Private chatroom for 2 members
    # FLOW:
    # getting '\pcr [nickname]'
    # on new thread, run handle():
        # display member in room
        # list of nickname drawn from existed data
# same as default chat room...
# except:
    # messages sent through the same 'client.recv' command
        # but with non-'default' in 'room' field in dataDict
        # sample 'room': 'vta->dvt'
            # nickname 1: msg[0 : msg.find('-')]
            # nickname 2: msg[msg.find('>') : len(msg)-1]
    room

def forwardfile():
    # listen for FILE-SENDING call
        # identify GETTER, FILESTREAM_ID, FILENAME
    # announce GETTER
    # take file from SENDER
        # listen for file chunks
        # checkif chunk belongs to file stream
            # check dataDict['type']
# FUNCTION TO STORE TRADED FILES CAN BE IMPLEMENTED HERE
        # send chunk 
            # condition for stop listening
    # send file to GETTER

print("Server is listening ...")
receive()
