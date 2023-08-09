import socket
import threading
import json
import tqdm
import os
import math

# Choosing Nickname
nickname = input("Choose your nickname: ")

# Connecting To Server
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(('127.0.0.1', 55555))

SEPARATOR = "<SEPARATOR>"
BUFFER_SIZE = 1024

inMainRoom = True
savedMessage = [[]]
nicknames = []
startToWrite = False
file_path = ""
file_size = - 1
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


# \sendF text.txt
# \sendF <d> text.txt
# \sendF img.png

def sendF_func(file_name):
    global startToWrite
    global times
    startToWrite = False
    
    print(">> Ready to send file {}".format(file_name))

    times =  math.ceil(int(file_size)/BUFFER_SIZE)
    # print("times = {}".format(times))
    with open(file_path, 'rb') as f:
        for i in range(times):
            data = f.read(1024)
            client.sendall(data)
            # print("i = {}".format(i))

    # client.send("<END>".encode())
    startToWrite = True
    print(">> Upload {} successfully !!!".format(file_name))

def rcvF_func(dataDict):
    global startToWrite
    startToWrite = False

    message = dataDict['text']
    sendNick = message[message.find(' <') + 2 : message.find('> ')]
    file_name = message[message.find('-f ') + 3 : message.find('-rcv') - 1]
    folder = "folder_" + nickname.replace(" ", "")
    if not os.path.exists(folder):
        os.makedirs(folder)
    file_path = folder + '/' + file_name
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

    # Print out 
    if ("public" in message):
        print ("{}: sent file {},\n saved as {}".format(sendNick, file_name, file_path))
    else:
        print ("{} (PM): sent file {},\n saved as".format(sendNick, file_name, file_path))



def getNickname(dataDict):
    global nicknames
    global nickname
    global startToWrite

    nicknames = dataDict['array']
    print("Online users list: {}".format(nicknames))
    while (nickname in nicknames):
        print("Nickname \'{}\' is used".format(nickname))
        nickname = input(">> Try a new nickname: ")

    dataDict['text'] = nickname
    startToWrite = True
    client.sendall(json.dumps(dataDict).encode())
    

# Listening to Server and Sending Nickname
def receive():
    global nicknames
    global nickname
    global startToWrite

    dataDict = {
        'text' : None,
        'array': None
    }

    while True:
        try:
            # Receive Message From Server
            
            # If 'getnickname' Send Nickname
            data = client.recv(4096)
            dataDict = json.loads(data.decode())

            if dataDict['text'] == '\\get_nickname':
                getNickname(dataDict)
                """ 
                nicknames = dataDict['array']
                print("Online users list: {}".format(nicknames))
                while (nickname in nicknames):
                    print("Nickname \'{}\' is used".format(nickname))
                    nickname = input(">> Try a new nickname: ")

                dataDict['text'] = nickname
                startToWrite = True
                client.sendall(json.dumps(dataDict).encode())
                """
            
            elif dataDict['text'][:7] == "\\sendF ":
                rcvF_func(dataDict)
                # message = dataDict['text']
                # sendNick = message[message.find(' <') + 2 : message.find('> ')]
                # file_name = message[message.find('-f ') + 3 : message.find('-rcv') - 1]
                # folder = "folder_" + nickname.replace(" ", "")
                # if not os.path.exists(folder):
                #     os.makedirs(folder)
                # file_path = folder + '/' + file_name
                # # print(file_path)
                # file_size = int(message[message.find(' (') + 2 : message.find(') ') ])
                # startToWrite = False
                # with open(file_path, 'wb') as f:
                #     times = math.ceil(int(file_size)/BUFFER_SIZE)
                #     # print("times = {}".format(times))
                #     for i in range(times):
                #         data = client.recv(1024)
                #         f.write(data)
                #         # print("i = {}".format(i))
                # startToWrite = True
                # # print(">> File received and saved as:", file_path)

                # if ("public" in message):
                #     print ("\'{}\' sent file {}, saved as {}".format(sendNick, file_name, file_path))
                # else:
                #     print ("\'{}\' (PM) sent file {}, saved as".format(sendNick, file_name, file_path))
            
            elif dataDict['text'][:7] == "\\ready":
                sendF_func("")

            elif dataDict['text'] == '\\update_list':
                nicknames = dataDict['array']
                
            elif dataDict['text'] == '\\close_all':
                client.close()
                break
            else:
                print(dataDict['text'],)
        except:
            # Close Connection When Error
            print("An error occured!")
            client.close()
            break



# Sending Messages To Server
def write():
    dataDict = {
        'text' : None,
        'array': None
    }

    global file_path
    global file_size
    global times

    while True:
        while (not startToWrite):
            pass
        takenInput = input('')

        if (takenInput[:8] == "\\online"):
            print(nicknames)
            continue

        # To pm:  "\pm <recv's name>  message"
        elif (takenInput[:4] == "\\pm "):
            dataDict['text'] = takenInput

        # To send file "\sendF <@all> file's path"
        elif (takenInput[:7] == "\\sendF "):
            if (not ('<' in takenInput)):
                takenInput = takenInput[:7] + "<@all> " + takenInput[7:]
            
            file_path = takenInput[takenInput.find("> ") + 2:]
            # print("<{}>".format(file_path))
            file_size = os.path.getsize(file_path)
            
            dataDict['text'] = "\\sendF <{}> ({}) -f {}".format(takenInput[takenInput.find('<') + 1: takenInput.find('>')], str(file_size), fPath2fName(file_path))
            print(dataDict['text'])
            client.sendall(json.dumps(dataDict).encode())
            continue
        else:
            dataDict['text'] = '{}: {}'.format(nickname, takenInput)

        client.sendall(json.dumps(dataDict).encode())



# Starting Threads For Listening And Writing
receive_thread = threading.Thread(target = receive)
receive_thread.start()

write_thread = threading.Thread(target = write)
write_thread.start()