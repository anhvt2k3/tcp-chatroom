# Python program to implement client side of chat room.
import socket
import select
import sys

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
if len(sys.argv) != 3:
	print ("Correct usage: script, IP address, port number")
	exit()
IP_address = str(sys.argv[1])
Port = int(sys.argv[2])
server.connect((IP_address, Port))

while True:
    try:
        # Check if the server socket is still valid
        if server.fileno() < 0:
            print("Server disconnected.")
            break

        # maintains a list of possible input streams
        sockets_list = [sys.stdin, server] 

        """ There are two possible input situations. Either the
        user wants to give manual input to send to other people,
        or the server is sending a message to be printed on the
        screen. Select returns from sockets_list, the stream that
        is reader for input. So for example, if the server wants
        to send a message, then the if condition will hold true
        below.If the user wants to send a message, the else
        condition will evaluate as true"""
        read_sockets,write_socket,error_socket = select.select(sockets_list,[],[])

        for socks in read_sockets:
            if socks == server:
                try:
                    message = socks.recv(2048)
                    print (message)
                except (OSError, ConnectionResetError):
                    print("Server disconnected.")
                    server.close()
                    break
                else:
                    message = sys.stdin.readline().strip()
                    server.send(message.encode('utf-8'))
                    sys.stdout.write("<You>")
                    sys.stdout.write(message)
                    sys.stdout.flush()

    except :
        continue

server.close()
