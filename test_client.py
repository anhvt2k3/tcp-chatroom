import socket
import threading
import json
import os
import math
import shutil
from pathlib import Path



# Choosing Nickname
nickname = input("Choose your nickname: ")

# Connecting To Server
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(('127.0.0.1', 55555))

RECEIVE_STATUS = True
WRITE_STATUS = True

SEPARATOR = "<SEPARATOR>"
BUFFER_SIZE = 4096

inMainRoom = True
savedMessage = [[]]
nicknames = []
able2Write = False
file_path = ""
file_size = - 1
folder = ""
times = -1

# resPCR: response for private chat room:
# -2: normally input, -1: response for PCR, 0: not accept PCR, 1: accept PCR   
resPCR = -2

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
    able2Write = False
    
    # print(">> Ready to send file {}".format(file_name))

    times =  math.ceil(int(file_size)/BUFFER_SIZE)
    # print("times = {}".format(times))
    with open(file_path, 'rb') as f:
        for i in range(times):
            data = f.read(BUFFER_SIZE)
            client.sendall(data)
            # print("i = {}".format(i))

    # client.send("<END>".encode())
    able2Write = True
    print(">> Sent file {} successfully !!!".format(file_name))

def rcvF_func(dataDict):
    global able2Write
    global folder

    able2Write = False

    message = dataDict['text']
    sendNick = message[message.find(' <') + 2 : message.find('> ')]
    file_name = message[message.find('-f ') + 3 : message.find('-rcv') - 1]
    folder = "folder_" + nickname.replace(" ", "")
    # print(folder)
    if not os.path.exists(folder):
        os.makedirs(folder)
    file_path = folder + '/' + file_name
    file_size = int(message[message.find(' (') + 2 : message.find(') ') ])


    able2Write = False
    with open(file_path, 'wb') as f:
        times = math.ceil(int(file_size)/BUFFER_SIZE)
        # print("times = {}".format(times))
        for i in range(times):
            data = client.recv(BUFFER_SIZE)
            f.write(data)
            # print("i = {}".format(i))


    able2Write = True
    # print(">> File received and saved as:", file_path)

    # Print out 
    if ("public" in message):
        print ("{}: sent file {}, saved as {}".format(sendNick, file_name, file_path))
    else:
        print ("{} (PM): sent file {}, saved as {}".format(sendNick, file_name, file_path))


def getNickname(dataDict):
    global nicknames
    global nickname
    global able2Write

    nicknames = dataDict['array']
    print("Online users list: {}".format(nicknames))
    while (nickname in nicknames):
        print("Nickname \'{}\' is used".format(nickname))
        nickname = input(">> Try a new nickname: ")

    dataDict['text'] = nickname
    able2Write = True
    client.sendall(json.dumps(dataDict).encode())


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
    # print(dataDict['text'])
    client.sendall(json.dumps(dataDict).encode())


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

    while RECEIVE_STATUS:
        try:
            # Receive Message From Server
            
            # If 'getnickname' Send Nickname
            data = client.recv(4096)
            dataDict = json.loads(data.decode())
            message = dataDict['text']

            if (message == '\\get_nickname'):
                getNickname(dataDict)
                """ 
                nicknames = dataDict['array']
                print("Online users list: {}".format(nicknames))
                while (nickname in nicknames):
                    print("Nickname \'{}\' is used".format(nickname))
                    nickname = input(">> Try a new nickname: ")

                message = nickname
                startToWrite = True
                client.sendall(json.dumps(dataDict).encode())
                """
            
            elif (message[:len("\\sendF ")] == "\\sendF "):
                rcvF_func(dataDict)
                """
                message = message
                sendNick = message[message.find(' <') + 2 : message.find('> ')]
                file_name = message[message.find('-f ') + 3 : message.find('-rcv') - 1]
                folder = "folder_" + nickname.replace(" ", "")
                if not os.path.exists(folder):
                    os.makedirs(folder)
                file_path = folder + '/' + file_name
                # print(file_path)
                file_size = int(message[message.find(' (') + 2 : message.find(') ') ])
                startToWrite = False
                with open(file_path, 'wb') as f:
                    times = math.ceil(int(file_size)/BUFFER_SIZE)
                    # print("times = {}".format(times))
                    for i in range(times):
                        data = client.recv(1024)
                        f.write(data)
                        # print("i = {}".format(i))
                startToWrite = True
                # print(">> File received and saved as:", file_path)

                if ("public" in message):
                    print ("\'{}\' sent file {}, saved as {}".format(sendNick, file_name, file_path))
                else:
                    print ("\'{}\' (PM) sent file {}, saved as".format(sendNick, file_name, file_path))
                """

            elif (message[:len("\\ready ")] == "\\ready "):
                tmp = message
                file_name = tmp[tmp.find('-f ') + 3:]
                sendF_func(file_name)

            elif (message[:len("\\pChat ")] == "\\pChat "):
                if (message[:len("\\pChat join? ")] == "\\pChat join? "):
                    sname = message[message.find('-s ') + 3:]
                    print("{} invites you to a Private chat room (Y/n): ".format(sname))
                    continue
                    # resPCR = -1
                    # while(resPCR != 0 and resPCR != 1):
                    #     pass
                    # ans = resPCR
                    # # resPCR = -2
                    # print("ans = {}".format(ans))
                    # if (ans == 1): dataDict['text'] = "Yes"
                    # else: dataDict['text'] = "No"

                    # client.sendall(json.dumps(dataDict).encode())
                # elif (message[:len("\pChat -begin ")] == "\pChat -begin "):
                #     chatter = message[len("\pChat -begin "):]
                #     pass          

            elif (message == '\\update_list'):
                nicknames = dataDict['array']
                
            elif (message == "\\close_all"):
                print(">> You left the chat!")
                client.close()
                WRITE_STATUS = False

                folder = "folder_" + nickname.replace(" ", "")
                remove_directory(folder)

                break

            elif (message[:len("\\getOut ")] == "\\getOut "):
                nicknames = dataDict['array']
                tmp_nick = message[message.find("-n ") + 3:]
                print(">> {} left the chat!".format(tmp_nick))   

            else:
                print(message)
            
        except:
            # Close Connection When Error
            print("An error occured!")

            dataDict['text'] = "\\hError"
            client.sendall(json.dumps(dataDict).encode())
            WRITE_STATUS = False
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
            checkNick = takenInput[takenInput.find(' <') + 2: takenInput.find('> ')]
            checkVar = nickCheck(checkNick)
            if checkVar == 1:
                dataDict['text'] = takenInput
            elif checkVar == -1:
                print(">> {} is not existed!".format(checkNick))
                continue
            else:
                # print(">> Cannot private chat with yourself!")
                continue

        # To send file "\sendF <@all> file's path"
        elif (takenInput[:len("\\sendF ")] == "\\sendF "):    
            if ('<' in takenInput):
                checkNick = takenInput[takenInput.find(' <') + 2: takenInput.find('> ')]
                checkVar = nickCheck(checkNick)
            else: checkVar = 1 
            
            if (checkVar == 1):
                sendF_processing(takenInput)
                continue
            elif (checkVar == -1):
                print(">> {} is not existed!".format(checkNick))
                continue
            else:
                # print(">> Cannot private chat with yourself!")
                continue

            
        
        # To invite user to private chat room "\pChat <name>"
        elif (takenInput[:len("\\pChat ")] == "\\pChat "):
            if (takenInput[:len("\\pChat <")] == "\\pChat <"):
                checkNick = takenInput[takenInput.find(' <') + 2: takenInput.find('> ')]
                checkVar = nickCheck(checkNick)
                # print("\'{}\': {}".format(checkNick, checkVar))
                if (checkVar == 1):
                    dataDict['text'] = "\\pChat -s {} -r {}".format(nickname, checkNick)
                    # private chat -sender ... -receiver ...
                elif (checkVar == -1):
                    print(">> {} is not existed!".format(checkNick))
                    continue
                else:
                    print(">> Cannot do private chat yourself!")
                    continue
            elif (takenInput[:len("\\pChat ")] == "\\pChat "):
                dataDict['text'] = takenInput[len("\\pChat "):]
        
        # To response to the private chatroom "\pChat Yes/No"
        # elif (takenInput[:len("\\pChat ")] == "\\pChat "):
        #     dataDict['text'] = takenInput[len("\\pChat "):]
        # if (takenInput == "bye!"):
        #     dataDict['text'] = "\\bye -n {}".format(nickname)

        # if it is normal text
        else:
            dataDict['text'] = '{}: {}'.format(nickname, takenInput)

        if WRITE_STATUS:
            client.sendall(json.dumps(dataDict).encode())
        
        if (takenInput == "bye!"):
            WRITE_STATUS = False



# Starting Threads For Listening And Writing
receive_thread = threading.Thread(target = receive)
receive_thread.start()

write_thread = threading.Thread(target = write)
write_thread.start()
