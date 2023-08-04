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
dataDict = {
    "text" : None,
    "array": None
}

# Listening to Server and Sending Nickname
def receive():
    while True:
        try:
            data = client.recv(4096)
            dataDict = json.loads(data.decode())

            if dataDict["text"] == '\\update_list':
                global nicknames
                nicknames = dataDict["array"]
                print(nicknames)
                
            elif dataDict["text"] == '\\close_all':
                client.close()
                break
            else:
                print(dataDict["text"],)

        # except (OSError, ConnectionResetError):
        except:
            # Close Connection When Error 
            print("An error occured!")
            client.close()
            break




# Sending Messages To Server
def write():
    dataDict = {
        "text" : None,
        "array": None
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