import subprocess
import socket

def open_new_terminal(commands):
    commands = "&".join(commands)
    subprocess.run(["start", "/wait", "cmd", "/c", f'{commands} & pause'], shell=True)

command_to_run = [
    'cd C:/Users/Admin/Desktop/cn-proj-1/',
    'python client.py 1 1'
    ]
# open_new_terminal(command_to_run)
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(('192.168.1.3', 49153))

print (client)