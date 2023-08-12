import socket
import threading
import json
import os
import math
from pathlib import Path
import subprocess
import sys

# Connection Data
host = '127.0.0.1'
port = 55555

#default
BUFFER_SIZE = 4096



# Input Nickname
nickname = sys.argv[1] if len(sys.argv) > 1 else input("Choose your nickname: ")

# 4 private chat room
inPCR = False
pcr_nickname = ""
if (len(sys.argv) > 1): 
    inPCR = True
    pcr_nickname = sys.argv[2]


# Connecting To Server
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((host, port))


RECEIVE_STATUS = True
WRITE_STATUS = True
PARENT_STATUS = True
FIRST_RUN = True

nicknames = []
pcr_clients = []
able2Write = False
file_path = ""
file_size = - 1
folder = ""
times = -1



# Get file_name from file_path
def path2Name(file_path):
    if ('/' in file_path):
        tmp = file_path[::-1]
        tmp = tmp[: tmp.find('/')]
        return tmp[::-1]

    elif ('\\' in file_path):
        tmp = file_path[::-1]
        tmp = tmp[: tmp.find('\\')]
        return tmp[::-1]
    else:
        return file_path    

def rcvF_func(dataDict):
    global able2Write
    global folder

    #Format: \senF <sender_name> file_name
    message = dataDict['text']
    sendNick = message[message.find(' <') + 2 : message.find('> ')]
    file_name = message[message.find('-f ') + 3 : message.find('-rcv') - 1]
    folder = "folder_" + nickname.replace(" ", "")

    if not os.path.exists(folder):
        os.makedirs(folder)
    file_path = folder + '/' + file_name
    file_size = int(message[message.find(' (') + 2 : message.find(') ') ])


    able2Write = False
    with open(file_path, 'wb') as f:
        times = math.ceil(int(file_size)/BUFFER_SIZE)
        for i in range(times):
            data = client.recv(BUFFER_SIZE)
            f.write(data)
            
    able2Write = True

    # Print out 
    if ("public" in message):
        print ("{}: sent file {}, saved as {}".format(sendNick, file_name, file_path))
    else:
        print ("{} (PM): sent file {}, saved as {}".format(sendNick, file_name, file_path))

def sendF_func(takenInput):
    global able2Write
    global file_path
    global file_size
    global times
    
    dataDict = {
        'text' : None,
        'array': None
    }

    if (not ('<' in takenInput)):
        takenInput = takenInput[:7] + "<@all> " + takenInput[7:]
    
    file_path = takenInput[takenInput.find("> ") + 2:]
    file_size = os.path.getsize(file_path)    
    able2Write = False

    dataDict['text'] = "\\sendF <{}> ({}) -f {}".format(takenInput[takenInput.find('<') + 1: takenInput.find('>')], str(file_size), path2Name(file_path))
    client.sendall(json.dumps(dataDict).encode())

    times =  math.ceil(int(file_size)/BUFFER_SIZE)
    with open(file_path, 'rb') as f:
        for i in range(times):
            data = f.read(BUFFER_SIZE)
            client.sendall(data)

    able2Write = True
    print(">> Sent file {} successfully !!!".format(path2Name(file_path)))

def getNickname(dataDict):
    global nicknames
    global nickname
    global able2Write
    global folder
    global pcr_nickname

    able2Write = False      

    if (not inPCR):
        print("Online users list: {}".format(nicknames))
        while (nickname in nicknames):
            print("!ERROR: Nickname \'{}\' is used".format(nickname))
            nickname = input(">> Try a new nickname: ")        

    dataDict['text'] = nickname

    if (inPCR): 
        dataDict['array'] = "pcr"
        print("PRIVATE CHAT ROOM (user: {})". format(nickname))
        print("\t>> Connected with {}".format(pcr_nickname))

    else: print(">> Connected to server!")

    client.sendall(json.dumps(dataDict).encode())
    
    able2Write = True
    folder = "folder_" + nickname.replace(" ", "")

def nickCheck(checkNick, sendF = False):
    global nickname
    global nicknames

    if (checkNick == "@all" and sendF):
        return 1
    elif (checkNick == nickname):
        return 0
    elif (not checkNick in nicknames):
        return -1
    return 1

def checkDir(path):
    if os.path.exists(path):
        if os.path.isfile(path):
            return 1
        elif os.path.isdir(path):
            return 0
        
    return -1

def removeDir(path):
    path = Path(path)
    if path.is_dir():
        for child in path.iterdir():
            if child.is_file():
                child.unlink()
            else:
                removeDir(child)
        path.rmdir()
        # print(f"Folder '{path}' and its contents removed.")

def createPCR(pcr_rcv):
    def open_new_terminal(commands):
        commands = " & ".join(commands)
        subprocess.run(["start", "cmd", "/c", f'{commands}'], shell = True)

    command_to_run = [
        'cd {}'.format(os.getcwd()),
        'python test_client.py {} {}'.format(nickname, pcr_rcv)
    ]

    # threading.Thread(target= open_new_terminal, args=(command_to_run, )).start()
    open_new_terminal(command_to_run)

def parentCheck():

    global able2Write
    
    dataDict = {
        'text': None,
        'array': None
    }

    dataDict['text'] = "\\parentCheck"
    dataDict['array'] = nickname

    client.sendall(json.dumps(dataDict).encode())



# Listening to Server and Sending Nickname
def receive():
    global RECEIVE_STATUS
    global WRITE_STATUS
    global PARENT_STATUS
    global able2Write

    global nicknames
    global nickname
    global folder
    global inMainRoom
    global pcr_nickname

    dataDict = {
        'text' : None,
        'array': None
    }



    while True:
        try:
            # Receive Message From Server
            data = client.recv(BUFFER_SIZE)
            dataDict = json.loads(data.decode())
            message = dataDict['text']


            # If 'getnickname' Send Nickname
            if (message == "\\get_nickname"):
                nicknames = dataDict['array']
                getnick_thread = threading.Thread(target = getNickname, args =(dataDict,))
                getnick_thread.start()

            elif (message == "\\connected"):
                message = ">> Connected to server!"

            elif (message[:len("\\rcvF ")] == "\\rcvF "):
                rcvF_func(dataDict)

            elif (message[:len("\\invoke_pcr ")] == "\\invoke_pcr "):
                name = message[message.find('-n ') + 3:]
                print(">> You will join private chat room with {}".format(name))
                createPCR(name)

            elif (message == "\\update_list"):
                nicknames = dataDict['array']

            elif (message[:len("\\update_pcrlist ")] == "\\update_pcrlist "):
                if ('+' in message):
                    pcr_clients.append(dataDict['array'])
                if ('-' in message):
                    pcr_clients.remove(dataDict['array'])

            elif (message == "\\parentCheck"):
                if (dataDict['array'] == "False"): 
                    PARENT_STATUS = False
                    # print("not OK")
                else:   pass # print("OK")

                able2Write = True

            elif (message == "\\close_all"):
                print(">> You left the chat!")
                
                WRITE_STATUS = False
                if (not inPCR):
                    folder = "folder_" + nickname.replace(" ", "")
                    removeDir(folder)


                dataDict['array'] = pcr_clients
                client.sendall(json.dumps(dataDict).encode())

                client.close()
                break

            elif (message[:len("\\getOut ")] == "\\getOut "):
                print(">> {} left the chat!".format(message[message.find("-n ") + 3:]))
                nicknames = dataDict['array']

                if (inPCR):
                    dataDict['text'] = "\\pcr_updateList"
                    client.sendall(json.dumps(dataDict).encode())
                    pass

            elif (message == "\\quit"):
                WRITE_STATUS = False
                dataDict['text'] = "\\hError"
                client.sendall(json.dumps(dataDict).encode())

                print(">> You left the chat!1")
                WRITE_STATUS = False
                
                if (not inPCR):
                    folder = "folder_" + nickname.replace(" ", "")
                    removeDir(folder)
                
                client.close()

            else:
                print(message)
            
        except:
            print("An error occured!")

            dataDict['text'] = "\\hError"
            client.sendall(json.dumps(dataDict).encode())
            
            print(">> You left the chat!2.1")
            WRITE_STATUS = False
            if (not inPCR):
                folder = "folder_" + nickname.replace(" ", "")
                removeDir(folder)
            
            client.close()
            break


# Sending Messages To Server
def write():
    global RECEIVE_STATUS
    global WRITE_STATUS
    global PARENT_STATUS
    global FIRST_RUN
    global able2Write

    global file_path
    global file_size
    global folder
    global times
    global inMainRoom
    
    okMess = True

    dataDict = {
        'text' : None,
        'array': None
    }

    while WRITE_STATUS:

        able2Write = False

        if (not FIRST_RUN and inPCR):
            parentCheck()
        
        if (not FIRST_RUN and not inPCR):
            able2Write = True

        

        while (not able2Write): pass
        FIRST_RUN = False

        if (inPCR): 
            if (not PARENT_STATUS):
                dataDict['text'] = "\\hError"
                dataDict["array"] = "\\deadParent"
                client.sendall(json.dumps(dataDict).encode())
                break

        takenInput = input('')
        if (takenInput == ""): continue

        # To check the online list: "\online"
        if (takenInput[:8] == "\\online"):
            print(nicknames)
            continue

        # To private message:  "\pm <recv's name>  message"
        elif (takenInput[:len("\\pm ")] == "\\pm "):
            if (inPCR):
                print("!ERROR: Cannot use private message in PCR")
                continue
            else:
                tmp = takenInput[takenInput.find(" <") + len(" <"): takenInput.find("> ")]
                checkVar = nickCheck(tmp)
                if checkVar == 1:
                    dataDict['text'] = takenInput
                elif checkVar == -1:
                    print("!ERROR: \'{}\' is not existed".format(tmp))
                    continue
                else:
                    print("!ERROR: Cannot use private message with yourself!")
                    continue

        # To send file "\sendF <@all> file's path"
        elif (takenInput[:len("\\sendF ")] == "\\sendF "):    
            if ('<' in takenInput):
                tmp = takenInput[takenInput.find(" <") + 2: takenInput.find('> ')]
                path = takenInput[takenInput.find("> ") + len("> "):]
                check = nickCheck(tmp)
            else: 
                check = 1
                path = takenInput[takenInput.find(" ") + len(" "):]
            
            if (check == 1):
                check = checkDir(path)

                if (check == 1):
                    sendF_func(takenInput)
                elif (check == 0):
                    print("!ERROR: Cannot send a folder")
                else: 
                    print("!ERROR: The inputted directory is not existed")
                continue
            elif (checkVar == -1):
                print("!ERROR: {} is not existed".format(checkNick))
                continue
            else:
                print("!ERROR: Cannot private send file to yourself")
                continue      
        
        # To invite user to private chat room "\pChat <name>"
        elif (takenInput[:len("\\pcr <")] == "\\pcr <"):
            if (inPCR):
                print("*NOTICE: Please create new PCR in Main chat!")
                continue
            else:
                checkNick = takenInput[takenInput.find(" <") + len(" <") : takenInput.find("> ")]
                checkVar = nickCheck(checkNick)
                if (checkVar == 1):
                    dataDict['text'] = "\\pcr -s {} -r {}".format(nickname, checkNick)
                elif (checkVar == -1):
                    print("!ERROR: \'{}\' is not existed".format(checkNick))
                    continue
                else:
                    print("!ERROR: Cannot join in PCR yourself!")
                    continue  
        
        # Normal input
        else:
            dataDict['text'] = "{}: {}".format(nickname, takenInput)


        
        if (WRITE_STATUS and okMess):
            client.sendall(json.dumps(dataDict).encode())
        
        if (takenInput == "bye!"):
            WRITE_STATUS = False

        


# Starting Threads For Listening And Writing
receive_thread = threading.Thread(target = receive)
receive_thread.start()

write_thread = threading.Thread(target = write)
write_thread.start()