import subprocess

def open_new_terminal(commands):
    commands = "&".join(commands)
    subprocess.run(["start", "/wait", "cmd", "/c", f'{commands} & pause'], shell=True)

command_to_run = [
    'cd C:/Users/Admin/Desktop/cn-proj-1/',
    'python client.py 1 1'
    ]
open_new_terminal(command_to_run)
