import socket
import threading
import json
import os
from pathlib import Path
import subprocess
import sys





# Connection Data
host = sys.argv[1] if len(sys.argv) > 2 else '127.0.0.1'
port = int(sys.argv[2]) if len(sys.argv) > 2 else 55555

#default
BUFFER_SIZE = 4096

# Input Nickname
nickname = sys.argv[3] if len(sys.argv) > 3 else input("Choose your nickname: ")

# For private chat room (PCR)
inPCR = False
pcr_nickname = ""
if (len(sys.argv) > 3): 
    inPCR = True
    pcr_nickname = sys.argv[4]


# Connecting To Server
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((host, port))


RECEIVE_STATUS = True
WRITE_STATUS = True
PARENT_STATUS = True
FIRST_RUN = True

able2Write = False
mtx = True

nicknames = []
pcr_clients = []

file_path = ""
file_size = - 1
folder = ""


# Process for the valid nickname
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

# Check the if the valid receiver
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

# Sending file
def sendF_func(takenInput):
    global able2Write
    global file_path
    global file_size
    
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
    dataDict['array'] = file_size
    client.sendall(json.dumps(dataDict).encode())
    

    file = open(f'./{file_path}', "rb")
    client.sendall(file.read())
    file.close()
    
    able2Write = True
    print ('>> File {} sent!'.format(file_path))

# Receiving file
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

    chunk_size = file_size
    able2Write = False

    file = open(file_path, "wb")
    
    chunk = client.recv(chunk_size)
    try: json.loads(chunk.decode())        
    except: file.write(chunk)  
         
    file.close()

    able2Write = True

    # Print out 
    if ("public" in message):
        print ("{}: sent file {}, saved as {}".format(sendNick, file_name, file_path))
    else:
        print ("{} (PM): sent file {}, saved as {}".format(sendNick, file_name, file_path))

# Check valid directory
def checkDir(file_path):
    if os.path.exists(file_path):
        if os.path.isfile(file_path):
            return 1
        elif os.path.isdir(file_path):
            return 0
        
    return -1

# Remove directory
def removeDir(file_path):
    file_path = Path(file_path)
    if file_path.is_dir():
        for child in file_path.iterdir():
            if child.is_file():
                child.unlink()
            else:
                removeDir(child)
        file_path.rmdir()

# Create Private chat room
def createPCR(pcr_rcver):
    def open_new_terminal(commands):
        commands = " & ".join(commands)
        subprocess.run(["start", "cmd", "/c", f'{commands}'], shell = True)

    command_to_run = [
        'cd {}'.format(os.getcwd()),
        'python test_client.py {} {} {} {}'.format(host, port,nickname, pcr_rcver)
    ]

    # threading.Thread(target= open_new_terminal, args=(command_to_run, )).start()
    open_new_terminal(command_to_run)

# Check the parent
def parentCheck():    
    global able2Write
    able2Write = False

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
    global mtx

    global nicknames
    global nickname
    global folder
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

            # Handle the when the server done it receving file work
            elif (message == "\\doneRecevingFile"):
                mtx = True

            # Handle receiving file from server
            elif (message[:len("\\rcvF ")] == "\\rcvF "):
                rcvF_func(dataDict)

            # Handle PCR invoke from server 
            elif (message[:len("\\invoke_pcr ")] == "\\invoke_pcr "):
                name = message[message.find('-n ') + 3:]
                print(">> You will join private chat room with {}".format(name))
                createPCR(name)
            
            # Handle the update normal list
            elif (message == "\\update_list"):
                nicknames = dataDict['array']

            # Handle the update PCR list
            elif (message[:len("\\update_pcrlist ")] == "\\update_pcrlist "):
                if ('+' in message):
                    pcr_clients.append(dataDict['array'])
                if ('-' in message):
                    pcr_clients.remove(dataDict['array'])

            # Handle the response from server if the parent of PCR is alive or not
            elif (message == "\\parentCheck"):
                PARENT_STATUS = True
                if (dataDict['array'] == "False"): 
                    PARENT_STATUS = False

                able2Write = True

            # Handle when you left the chat
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

            # Handle when another user is left the chat
            elif (message[:len("\\getOut ")] == "\\getOut "):
                print(">> {} left the chat!".format(message[message.find("-n ") + 3:]))
                nicknames = dataDict['array']

                if (inPCR):
                    dataDict['text'] = "\\pcr_updateList"
                    client.sendall(json.dumps(dataDict).encode())

            # Normal message
            else:
                print(message)
        
        # Eception handle
        except:
            print("An error occured!")

            dataDict['text'] = "\\exception"
            client.sendall(json.dumps(dataDict).encode())
            
            print(">> You left the chat!")
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
    global mtx

    global file_path
    global file_size
    global folder

    dataDict = {
        'text' : None,
        'array': None
    }

    while WRITE_STATUS:
        if (inPCR and (not FIRST_RUN)):
            while (not mtx): pass
            parentCheck()

        if ((not inPCR) and (not FIRST_RUN)):
            able2Write = True


        while (not able2Write): pass
        FIRST_RUN = False
        
        if (inPCR):
            if (not PARENT_STATUS):
                dataDict['text'] = "\\uParent"
                client.sendall(json.dumps(dataDict).encode())
                break
        


        # Take input from keyboard
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
                checkNick = takenInput[takenInput.find(" <") + len(" <"): takenInput.find("> ")]
                check = nickCheck(checkNick)
                if (check == 1):
                    dataDict['text'] = takenInput
                elif check == -1:
                    print("!ERROR: \'{}\' is not existed".format(checkNick))
                    continue
                else:
                    print("!ERROR: Cannot use private message with yourself!")
                    continue

        # To send file "\sendF <@all> file's path"
        elif (takenInput[:len("\\sendF ")] == "\\sendF "):    
            if ('<' in takenInput):
                checkNick = takenInput[takenInput.find(" <") + 2: takenInput.find('> ')]
                path = takenInput[takenInput.find("> ") + len("> "):]
                check = nickCheck(checkNick)
            else: 
                check = 1
                path = takenInput[takenInput.find(" ") + len(" "):]
            
            if (check == 1):
                check = checkDir(path)

                if (check == 1):
                    if (inPCR): mtx = False
                    sendF_func(takenInput)
                elif (check == 0):
                    print("!ERROR: Cannot send a folder")
                else: 
                    print("!ERROR: The inputted directory is not existed")
                continue
            elif (check == -1):
                print("!ERROR: {} is not existed".format(checkNick))
                continue
            else:
                print("!ERROR: Cannot private send file to yourself")
                continue      
        
        # To invite user to private chat room "\pChat <name>"
        elif (takenInput[:len("\\pcr <")] == "\\pcr <"):
            if (inPCR):
                print("*NOTICE: Please create new PCR in Main chat room!")
                continue
            else:
                checkNick = takenInput[takenInput.find(" <") + len(" <") : takenInput.find("> ")]
                check = nickCheck(checkNick)
                if (check == 1):
                    dataDict['text'] = "\\pcr -s {} -r {}".format(nickname, checkNick)
                elif (check == -1):
                    print("!ERROR: \'{}\' is not existed".format(checkNick))
                    continue
                else:
                    print("!ERROR: Cannot join in PCR yourself!")
                    continue  
        
        # Normal input
        else:
            dataDict['text'] = "{}: {}".format(nickname, takenInput)


        if (WRITE_STATUS):
            client.sendall(json.dumps(dataDict).encode())
        
        # Handle when the message is "bye!"
        if (takenInput == "bye!"):
            WRITE_STATUS = False

        


# Starting Threads For Listening And Writing
receive_thread = threading.Thread(target = receive)
receive_thread.start()

write_thread = threading.Thread(target = write)
write_thread.start()