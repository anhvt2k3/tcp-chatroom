import subprocess
import socket

def open_new_terminal(commands):
    commands = " & ".join(commands)
    subprocess.run(["start", "cmd", "/c", f'{commands}'], shell=True)

command_to_run = [
    'cd C:/Users/Admin/Desktop/cn-proj-1/',
    'python client.py'
    ]

command_to_run = " & ".join(command_to_run)
# open_new_terminal(command_to_run)

def run_command_and_auto_close_window(command):
    try:
        # Use check_call to raise an exception on non-zero exit status
        subprocess.check_call(command, shell=True)
    except subprocess.CalledProcessError:
        # An error occurred, handle it here
        print("An error occurred")

# Example command that will result in an error (command not found)
# command_to_run = "nonexistent_command"

run_command_and_auto_close_window(command_to_run)
