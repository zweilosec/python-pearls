#!/usr/bin/env python3

import dns.resolver
import argparse
from colorama import Fore, Style, init

#Parse arguments from the command line
parser = argparse.ArgumentParser(description='A simple subdomain enumeration script.')
parser.add_argument('-d','--domain', help='An IP address or hostname', required= True)
parser.add_argument('-w', '--wordlist',help=('The subdomain wordlist file to use.'), required= True)
parser.add_argument('-o', '--outfile',help=('The file to write output to.'))
args = parser.parse_args()

def createStyle():
    global success, informational, warning, fail
    success, informational, warning, fail = Fore.GREEN + Style.NORMAL, Fore.CYAN + Style.NORMAL, Fore.YELLOW + Style.DIM, Fore.RED + Style.BRIGHT

foundList = []

def validate_subdomain(domain,wordlist):
    try:
        print(informational + f"Checking for subdomains for domain '{domain}'")

        with open(wordlist) as subdomains:
            for subdomain in subdomains:
                #for some reason subdomain has \r or \n on them, need to strip it off
                print(informational + f'Testing: {subdomain.strip()}', end='\r', flush=True)
                try:
                    ip_list = dns.resolver.resolve(f'{subdomain.strip()}.{domain}', 'A')
                    if ip_list:
                        foundList.append(subdomain.strip())

                        print(informational + 'Subdomain '+ success + f'{subdomain.strip()}.{domain}' + informational + ' found at:')
                        for ip in ip_list:
                            print(success + f'\t{ip}')

                except dns.resolver.NXDOMAIN:
                    pass
                except dns.resolver.NoAnswer:
                    pass
                except dns.resolver.NoNameservers:
                    pass

    except FileNotFoundError:
        print(fail + 'The specified wordlist could not be found.')

def writeOutput():
    outfile = args.outfile
    with open(outfile, 'a'):
        for subdomain in foundList:
            outfile.write(subdomain)
    print(warning + f"Data written to {outfile}.")

if __name__ == "__main__":
    try:
        init()
        createStyle()
        validate_subdomain(args.domain,args.wordlist)
        if args.outfile:
            writeOutput()

    except KeyboardInterrupt:
        print(warning + 'Ctrl-C detected.  Exiting...')
