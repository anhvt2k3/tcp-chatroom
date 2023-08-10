import subprocess
import socket

def open_new_terminal(commands):
    commands = "&".join(commands)
    subprocess.run(["start", "cmd", "/c", f'{commands}'], shell=True)

command_to_run = [
    'cd C:/Users/Admin/Desktop/cn-proj-1/',
    'python client.py'
    ]
open_new_terminal(command_to_run)

# client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# client.connect(('192.168.0.73', 49153))

# print (client)