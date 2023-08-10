import socket
import threading
import pickle
import json
import os
import subprocess
import sys

# Choosing Nickname
nickname = sys.argv[1] if len(sys.argv) > 1 else input("Choose your nickname: ")

# Connecting To Server
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(('192.168.0.73', 49153))

PM = False
beginChatting = True
nicknames = []
beginChatting = True

# Receive Message From Server

# Listening to Server and Sending Nickname
def receive():
    # print ('receiving')
    dataDict = {
        "text" : None,
        "array": None,
        # 'room': '*' 
    }
    
    while True:
        try:
            data = client.recv(4096)
            dataDict = json.loads(data.decode())
            
            if dataDict["text"] == '\\update_list':
                global nicknames
                nicknames = dataDict["array"]
                print(nicknames)
            
#           *** SENDING FILES *** 
            elif dataDict["text"][:5] == '\\FILE':
                # server confimation
                FILENAME = dataDict['text'].split(' ')[1]
                # send file
                    # open file
                file = open(f'./{FILENAME}', "rb")
                    # send file
                client.sendall(file.read())
                    # send a msg to end file stream
                client.sendall(json.dumps(dataDict).encode())
                print (f'>> File {FILENAME} sent!')
                
                    # close file
                file.close()
                
#           *** RECEVING FILES ***
            elif dataDict["text"][:14] == '\\INCOMING_FILE':
                # analyze file receive signal
                    # get FILENAME
                FILENAME = f'./{nickname}_rf/'
                os.makedirs(os.path.dirname(FILENAME), exist_ok=True)
                # create file
                    # open file
                FILENAME = f'./{nickname}_rf/' + dataDict['array']
                file = open(FILENAME, "wb")
                # listen for file chunks
                    # checkif chunks belong to file stream
                while True:
                    chunk = client.recv(4096)
                    try:
                        json.loads(chunk.decode())
                        break
                    except:
                        file.write(chunk)
                        continue            
                # write file
                    # stop listen
                print ('>> File {} received!'.format(dataDict['array']))
                # print (f">> File {dataDict['array']} received!")
                    # close file
                file.close()

#           *** PCR ***
            elif dataDict['text'] == '>> INVOKE PCR':
                if dataDict['array'] != 'pcr': print ('>> INVOKE FAILED!')
                pcr()

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
    # print ('writing')
    dataDict = {
        "text" : None,
        "array": None,
        # 'room': '*'
    }

    while True:
        takenInput = input('')

        if (takenInput[:2] == "/*"):
            client.close()
            break

        if (takenInput[:8] == "\\online"):
            print(nicknames)
            continue

        if (takenInput[:4] == '\\pm ' or takenInput[:4] == '\\sf ' or takenInput[:4] == '\\pcr'):
            dataDict["text"] = takenInput
        else:
            dataDict["text"] = '{}: {}'.format(nickname, takenInput)

        client.sendall(json.dumps(dataDict).encode())

def pcr():
        # PRIVATE CHATROOM
    def open_new_terminal(commands):
        commands = " & ".join(commands)
        subprocess.run(["start", "cmd", "/c", f'{commands}'], shell=True)

    command_to_run = [
    f'cd {os.getcwd()}',
    f'python client.py {nickname}'
    ]

    # threading.Thread(target= open_new_terminal, args=(command_to_run, )).start()
    open_new_terminal(command_to_run)

while True:
    # If 'getnickname' Send Nickname``
    data = client.recv(4096)
    dataDict = json.loads(data.decode())

    # Identify pcr
    if len(sys.argv) > 1: 
        dataDict['array'] = 'pcr'

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