#! /usr/bin/env python
# DNS Enumeration Tool
# https://github.com/zweilosec

import dns.resolver
import dns.zone
import dns.ipv4
import dns.reversename
from colorama import Fore, Style, init
import sys
import argparse

def csvtype(choices):
    #Splits a comma-separated values string and returns a list of arguments to be parsed.
    def splitarg(arg):
        values = arg.split(',')
        for value in values:
            if value.to_upper() not in choices:
                raise argparse.ArgumentTypeError(
                    'invalid choice: {!r} (choose from {})'.format(value, ', '.join(map(repr, choices))))
            return values
        return splitarg

record_list = ('A','AAAA','CNAME', 'MX', 'SPF', 'TXT', 'CAA', 'SRV', 'PTR', 'SOA', 'DS', 'DNSKEY')

#Parse arguments from the command line
parser = argparse.ArgumentParser(description='A simple DNS enumeration script.')
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument('-d','--domain', help='A hostname to resolve')
group.add_argument('-i','--ip', help='An IP to do a reverse lookup on')
parser.add_argument('-r', '--record', type=csvtype((record_list, 'ALL')),help=(f'The DNS record type(s) to look up (comma separated list)\nFrom: {record_list}'), required= True)
parser.add_argument('-z','--zone_transfer', help='Attempt a DNS zone transfer', action='store_true') #store_true makes this argument True if the flag is specified
args = parser.parse_args()

def createStyle():
    global success, informational, warning, fail
    success, informational, warning, fail = Fore.GREEN + Style.NORMAL, Fore.CYAN + Style.NORMAL, Fore.YELLOW + Style.DIM, Fore.RED + Style.BRIGHT

def rLookup(domain, records):
    #Lookup DNS records of the specified type(s) for the specified domain
    try:
        print( informational + f"\nLooking up {records} records for the domain '{domain}':")

        #If the user specified the 'all' argument, use the whole records type list
        if 'all' in records:
            record_types = record_list
        else:
            record_types = records

        for record in record_types:
            try:
                answer = dns.resolver.resolve(domain, record)
                print( informational + f"\n{record}:")
                for server in answer:
                    print(success + f"\t{server.to_text()}")

            except dns.resolver.NoAnswer:
                print( warning + f"\nNo {record} record found for {domain}.")
                continue

    except dns.resolver.NXDOMAIN:
        print( fail + f"The specified domain '{domain}' could not be found.  (Check your spelling?)")
        quit()

    except dns.exception.SyntaxError:
        print(fail + 'There is a typo in your hostname. Did you type an IP by mistake? (use the --reverse flag to do a reverse lookup.')
        quit()

def reverseLookup(ip_addr):
    #Convert IPv4 and IPv6 addresses to/from their corresponding DNS reverse map names:
    try:
        reverseHostname = dns.reversename.from_address(ip_addr)
        hostname = str(dns.resolver.resolve(reverseHostname,'PTR')[0])
        print( informational + f"Host names for {ip_addr}:")
        print(success + f"\t{hostname}")
        
        return hostname

    except dns.exception.SyntaxError:
        print(fail + 'There is a typo in your IP address. Did you type a hostname by mistake?')
        quit()

def zoneTransfer(domain):

    name_servers = dns.resolver.resolve(domain, 'NS')

    print( informational + f'\nTesting {domain} for zone transfers. This may take a minute...')

    for nameServer in name_servers:
        ip_list = dns.resolver.resolve(nameServer.target, 'A')

        for ip_addr in ip_list:
            try:
                transfers = dns.zone.from_xfr(dns.query.xfr(str(ip_addr), domain))
                print(informational + f'\nZone transfer records for {nameServer} at {ip_addr}\n')
                for zone in transfers:
                    print(success + zone.to_text())

            except dns.xfr.TransferError:
                print(fail + f'\nZone Transfer refused for {nameServer}')
                pass

            except TimeoutError:
                print(fail + f'\nZone Transfer attempt timed out.')
                pass

            except dns.resolver.NoAnswer:
                pass
            except Exception:
                pass

if __name__ == "__main__":
    try:
        init()
        createStyle()

        if args.ip is not None:
            domain = reverseLookup(args.ip)
            rLookup(domain, args.record)

        if args.domain is not None:        
            rLookup(args.domain, args.record)

        if args.zone_transfer == True:
            zoneTransfer(args.domain)

    except KeyboardInterrupt:
        print(warning + '\nCtrl-C detected, exiting...')
        quit()
