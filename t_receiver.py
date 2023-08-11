import socket

# Connection Data
host = 'localhost'
port = 9999

# Starting Server
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((host, port))
server.listen()
print("Server listening...")


def receive_file(file_path, host = '', port = 9999):

    print("Server is ready to receive a file.")

    client, addr = server.accept()

    with open(file_path, 'wb') as f:
        i = 1
        while True:
            data = client.recv(1024)
            if not data:
                break
            f.write(data)

            print(i)
            i += 1 
    # client.close()
    # server.close()

file_path = "received_data/gotten_test_img.png"
receive_file(file_path)
print("File received and saved as:", file_path)