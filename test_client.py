import socket
import threading
import json
import os
import math
from pathlib import Path
import subprocess
import sys


host = '127.0.0.1'
port = 55555
BUFFER_SIZE = 4096



# Choosing Nickname
nickname = sys.argv[1] if len(sys.argv) > 1 else input("Choose your nickname: ")
# if len(sys.argv) > 1: nickname = sys.argv[1]  
# else: nickname = input("Choose your nickname: ")

inPCR = False
if (len(sys.argv) > 1): inPCR = True



# Connecting To Server
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((host, port))


RECEIVE_STATUS = True
WRITE_STATUS = True

nicknames = []
pcr_nicknames = []

able2Write = False
file_path = ""
file_size = - 1
folder = ""
times = -1



# Get the file_name in the file_path
def fPath2fName(file_path):
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

def sendF_func(file_name):
    global able2Write
    global times
    global file_size
    # able2Write = False
    
    # print(">> Ready to send file {}".format(file_name))

    times =  math.ceil(int(file_size)/BUFFER_SIZE)
    # print("times = {}".format(times))
    with open(file_path, 'rb') as f:
        for i in range(times):
            data = f.read(BUFFER_SIZE)
            client.sendall(data)

    # able2Write = True
    print(">> Sent file {} successfully !!!".format(file_name))

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

def getNickname(dataDict):
    global nicknames
    global nickname
    global able2Write
    global folder

    able2Write = False      

    if (not inPCR):
        nicknames = dataDict['array']
        print("Online users list: {}".format(nicknames))
        while (nickname in nicknames):
            print("Nickname \'{}\' is used".format(nickname))
            nickname = input(">> Try a new nickname: ")        

    dataDict['text'] = nickname

    if (inPCR): 
        dataDict['array'] = "pcr"

    client.sendall(json.dumps(dataDict).encode())
    
    able2Write = True
    folder = "folder_" + nickname.replace(" ", "")

    print(">> Connected to server!")
    


def sendF_processing(takenInput):
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
    
    dataDict['text'] = "\\sendF <{}> ({}) -f {}".format(takenInput[takenInput.find('<') + 1: takenInput.find('>')], str(file_size), fPath2fName(file_path))
    client.sendall(json.dumps(dataDict).encode())

def sendF_func1(takenInput):
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
    # able2Write = False

    dataDict['text'] = "\\sendF <{}> ({}) -f {}".format(takenInput[takenInput.find('<') + 1: takenInput.find('>')], str(file_size), fPath2fName(file_path))
    client.sendall(json.dumps(dataDict).encode())

    times =  math.ceil(int(file_size)/BUFFER_SIZE)
    # print("times = {}".format(times))
    with open(file_path, 'rb') as f:
        for i in range(times):
            data = f.read(BUFFER_SIZE)
            client.sendall(data)

    # able2Write = True
    print(">> Sent file {} successfully !!!".format(fPath2fName(file_path)))



def nickCheck(checkNick, sendF = False):
    # global nickname
    # global nicknames

    if (checkNick == "@all" and sendF):
        return 1
    elif (checkNick == nickname):
        return 0
    elif (not checkNick in nicknames):
        return -1
    return 1

def remove_directory(path):
    path = Path(path)
    if path.is_dir():
        for child in path.iterdir():
            if child.is_file():
                child.unlink()
            else:
                remove_directory(child)
        path.rmdir()
        # print(f"Folder '{path}' and its contents removed.")

def clear_terminal():
    # Check the operating system
    if os.name == 'posix':  # Unix-like systems
        os.system('clear')
    elif os.name == 'nt':   # Windows
        os.system('cls')

def createPCR():
    def open_new_terminal(commands):
        commands = " & ".join(commands)
        subprocess.run(["start", "cmd", "/c", f'{commands}'], shell = True)

    command_to_run = [
        'cd {}'.format(os.getcwd()),
        'python test_client.py {}'.format(nickname)
    ]

    # threading.Thread(target= open_new_terminal, args=(command_to_run, )).start()
    open_new_terminal(command_to_run)



# Listening to Server and Sending Nickname
def receive():
    global RECEIVE_STATUS
    global WRITE_STATUS

    global nicknames
    global nickname
    global able2Write
    global folder
    global resPCR
    global inMainRoom

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
                getNickname(dataDict)
                if (inPCR): 
                    print("This is {}\'s PCR with {}".format(nickname, "..."))           

            # elif (message[:len("\\join")] == "\\join"):
            #     message = ">> \'{}\' joined!".format(message[len("\\join -n "):])

            elif (message == "\\connected"):
                message = ">> Connected to server!"

            elif (message[:len("\\rcvF ")] == "\\rcvF "):
                rcvF_func(dataDict)

            elif (message[:len("\\ready ")] == "\\ready "):
                tmp = message
                file_name = tmp[tmp.find('-f ') + 3:]
                sendF_func(file_name)

            elif (message[:len("\\invoke_pcr ")] == "\\invoke_pcr "):
                name = message[message.find('-n ') + 3:]
                print(">> You will join private chat room with {}".format(name))
                createPCR()

            elif (message == '\\update_list'):
                nicknames = dataDict['array']
                
            elif (message == "\\close_all"):
                print(">> You left the chat!")
                
                WRITE_STATUS = False

                # print("folder = {}".format(folder))
                if (not inPCR):
                    folder = "folder_" + nickname.replace(" ", "")
                    remove_directory(folder)

                client.close()
                break

            elif (message[:len("\\getOut ")] == "\\getOut "):
                nicknames = dataDict['array']
                tmp_nick = message[message.find("-n ") + 3:]
                print(">> {} left the chat!".format(tmp_nick))   

            elif (message == "\\quit"):
                WRITE_STATUS = False
                dataDict['text'] = "\\hError"
                client.sendall(json.dumps(dataDict).encode())

                print(">> You left the chat!")
                WRITE_STATUS = False
                if (not inPCR):
                    folder = "folder_" + nickname.replace(" ", "")
                    remove_directory(folder)

            else:
                print(message)
            
        except:
            # Close Connection When Error
            print("An error occured!")

            dataDict['text'] = "\\hError"
            client.sendall(json.dumps(dataDict).encode())
            
            print(">> You left the chat!")
            WRITE_STATUS = False
            if (not inPCR):
                folder = "folder_" + nickname.replace(" ", "")
                remove_directory(folder)
            
            client.close()
            break


# Sending Messages To Server
def write():
    global RECEIVE_STATUS
    global WRITE_STATUS

    global file_path
    global file_size
    global folder
    global times
    global resPCR
    global inMainRoom
    
    okMess = True

    dataDict = {
        'text' : None,
        'array': None
    }

    while WRITE_STATUS:
        
        while (not able2Write):
            pass

        takenInput = input('')

        if (takenInput[:8] == "\\online"):
            print(nicknames)
            continue

        # To pm:  "\pm <recv's name>  message"
        elif (takenInput[:len("\\pm ")] == "\\pm "):
            if (inPCR):
                print(">> Cannot use private message in PCR")
                continue
            else:
                checkNick = takenInput[takenInput.find(' <') + 2: takenInput.find('> ')]
                checkVar = nickCheck(checkNick)
                if checkVar == 1:
                    dataDict['text'] = takenInput
                elif checkVar == -1:
                    print(">> {} is not existed!".format(checkNick))
                    continue
                else:
                    print(">> Cannot private chat with yourself!")
                    continue

        # To send file "\sendF <@all> file's path"
        elif (takenInput[:len("\\sendF ")] == "\\sendF "):    
            if ('<' in takenInput):
                checkNick = takenInput[takenInput.find(' <') + 2: takenInput.find('> ')]
                checkVar = nickCheck(checkNick)
            else: checkVar = 1
            
            if (checkVar == 1):
                # sendF_processing(takenInput)
                sendF_func1(takenInput)
                # sendF_func(file_name)
                continue
            elif (checkVar == -1):
                print(">> {} is not existed!".format(checkNick))
                continue
            else:
                # print(">> Cannot private chat with yourself!")
                continue      
        
        # To invite user to private chat room "\pChat <name>"
        elif (takenInput[:len("\\pcr <")] == "\\pcr <"):
            if (inPCR):
                print(">> Please creare new PCR in Main chat!")
                continue
            else:
                checkNick = takenInput[takenInput.find(' <') + 2: takenInput.find('> ')]
                checkVar = nickCheck(checkNick)
                if (checkVar == 1):
                    dataDict['text'] = "\\pcr -s {} -r {}".format(nickname, checkNick)
                elif (checkVar == -1):
                    print(">> {} is not existed!".format(checkNick))
                    continue
                else:
                    print(">> Cannot make a PCR yourself!")
                    continue  

        else:
            dataDict['text'] = '{}: {}'.format(nickname, takenInput)


        
        if (WRITE_STATUS and okMess):
            client.sendall(json.dumps(dataDict).encode())
        
        if (takenInput == "bye!"):
            WRITE_STATUS = False



# Starting Threads For Listening And Writing
receive_thread = threading.Thread(target = receive)
receive_thread.start()

write_thread = threading.Thread(target = write)
write_thread.start()