import socket
import threading
import pickle
import json

# Choosing Nickname
nickname = input("Choose your nickname: ")

# Connecting To Server
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(('192.168.1.27', 49153))

PM = False
beginChatting = True
nicknames = []
beginChatting = True

# Receive Message From Server

# Listening to Server and Sending Nickname
def receive(room):
    dataDict = {
        "text" : None,
        "array": None,
        'room': 'default' 
    }
    
    while True:
        try:
            data = client.recv(4096)
            dataDict = json.loads(data.decode())
            
            # if dataDict['room'] != room:
            #     continue

            if dataDict["text"] == '\\update_list':
                global nicknames
                nicknames = dataDict["array"]
                print(nicknames)
            
            elif dataDict["text"][:5] == '\\FILE':
                sendfile(dataDict)

            elif dataDict["text"][:14] == '\\INCOMING_FILE':
                recvfile(dataDict)

            elif dataDict["text"] == '\\close_all':
                client.close()
                break
            else:
                print(dataDict["text"],)

        # except (OSError, ConnectionResetError):
        except:
            # Close Connection When Error 
            print("You're disconnected!")
            client.close()
            break




# Sending Messages To Server
def write():
    dataDict = {
        "text" : None,
        "array": None,
        'room': 'default'
    }

    while True:
        takenInput = input('')

        if (takenInput[:8] == "\\exit"):
            client.close()
            break

        if (takenInput[:8] == "\\online"):
            print(nicknames)
            continue
        
        if (takenInput[:4] == '\\pm '):
            dataDict["text"] = takenInput
        else:
            dataDict["text"] = '{}: {}'.format(nickname, takenInput)

        client.sendall(json.dumps(dataDict).encode())

def pcr(room):
        # PRIVATE CHATROOM
# send out creating-chatroom command:
    # pcr [target_nickname]
# create new thread
# run both receive() and start()
    # messages are sent through dataDict with their specified room
        # sample 'room': 'vta->dvt'
# def receive():
#     while True:
#         try:
#             data = client.recv(4096)
#             dataDict = json.loads(data.decode())

#             if dataDict["text"] == '\\update_list':
#                 global nicknames
#                 nicknames = dataDict["array"]
#                 print(nicknames)
                
#             elif dataDict["text"] == '\\close_all':
#                 client.close()
#                 break
#             else:
#                 print(dataDict["text"],)

#         # except (OSError, ConnectionResetError):
#         except:
#             # Close Connection When Error 
#             print("You're disconnected!")
#             client.close()
#             break
    room

def sendfile(SNDcall):
    # dataDict receiving
        # send data
        # retrieve data
        # decode
        # loads to json
        # assign
    # server confimation
    FILENAME = SNDcall['text'].split(' ')[1]

    # send file
        # open file
    file = open(FILENAME, "r")

        # send file
    client.sendall(file.read().encode())
    
        # send a msg to end file stream
    client.sendall(json.dumps(SNDcall).encode())
    print (f'>> File {FILENAME} sent!')
     
        # close file
    file.close()

def recvfile(RECVcall):
    # analyze file receive signal
        # get FILENAME
    FILENAME = RECVcall['array']
    # create file
        # open file
    file = open(FILENAME, "x")
    # listen for file chunks
        # checkif chunks belong to file stream
    while True:
        chunk = client.recv(4096)
        try:
            msg = json.loads(chunk.decode())
            if (msg == RECVcall): break
        except:
            file.write(chunk)
            continue            
    # write file
        # stop listen
    print (f'>> File {FILENAME} received!')
        # close file
    file.close()


while True:
    # If 'getnickname' Send Nickname
    data = client.recv(4096)
    dataDict = json.loads(data.decode())

    if dataDict["text"] == '\\get_nickname':
        dataDict["text"] = nickname
        client.sendall(json.dumps(dataDict).encode())

    elif dataDict["text"] == '\\available_nickname':
        print("**********")
        print(dataDict["array"])
        while (nickname in dataDict["array"]):
            print("Again")
            nickname = input("Try a new nickname: ")
        dataDict["text"] = nickname
        client.sendall(json.dumps(dataDict).encode())

    else:
        break
    


# Starting Threads For Listening And Writing
receive_thread = threading.Thread(target = receive)
receive_thread.start()

write_thread = threading.Thread(target = write)
write_thread.start()