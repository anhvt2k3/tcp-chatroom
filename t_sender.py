import socket



host = 'localhost'
port = 9999

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(('localhost', 9999))



def send_file(file_path, host = 'localhost', port = 9999):
    i = 1
    with open(file_path, 'rb') as f:
        while True:
            data = f.read(1024)
            if not data:
                break
            client.sendall(data)
            
            print(i)
            i += 1 

    # client.close()
                    

file_path = "img.png"
send_file(file_path)
print("File sent:", file_path)