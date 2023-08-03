import socket
import threading
import pickle
import json

# Choosing Nickname
nickname = input("Choose your nickname: ")

# Connecting To Server
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(('127.0.0.1', 55555))

PM = False
beginChatting = True
nicknames = []
beginChatting = True


# Listening to Server and Sending Nickname
def receive():
    global nicknames
    while True:
        try:
            # Receive Message From Server
            dataDict = {
                "text" : None,
                "array": None
            }
            
            # If 'getnickname' Send Nickname
            data = client.recv(4096)
            dataDict = json.loads(data.decode())

            if dataDict["text"] == '\\get_nickname':
                dataDict["text"] = nickname
                nicknames = dataDict["array"]
                print("Online users list: {}".format(nicknames))
                client.sendall(json.dumps(dataDict).encode())

            elif dataDict["text"] == '\\update_list':
                nicknames = dataDict["array"]
                
            elif dataDict["text"] == '\\close_all':
                client.close()
                break
            else:
                print(dataDict["text"],)
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

        if (takenInput[:8] == "\\online"):
            print(nicknames)
            continue

        # To pm:  "\pm <recv's name>  message"
        if (takenInput[:4] == '\\pm '):
            dataDict["text"] = takenInput
        else:
            dataDict["text"] = '{}: {}'.format(nickname, takenInput)

        client.sendall(json.dumps(dataDict).encode())



# Starting Threads For Listening And Writing
receive_thread = threading.Thread(target = receive)
receive_thread.start()

write_thread = threading.Thread(target = write)
write_thread.start()