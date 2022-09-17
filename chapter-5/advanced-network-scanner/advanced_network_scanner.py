from scapy.all import *
import ipaddress
import threading
import time
import pandas as pd
# remove scapy warning
import logging
log = logging.getLogger("scapy.runtime")
log.setLevel(logging.ERROR)

# printing lock to avoid overlapping prints
print_lock = threading.Lock()
# number of IP addresses per chunk
NUM_IPS_PER_CHUNK = 10

# a function to arping a network or single ip
def get_connected_devices_arp(ip, timeout=3):
    # create a list to store the connected devices
    connected_devices = []
    # create an arp request
    arp_request = Ether(dst="ff:ff:ff:ff:ff:ff")/ARP(pdst=ip) 
    # send the packet and receive a response
    answered_list = srp(arp_request, timeout=timeout, verbose=False)[0]
    # parse the response
    for element in answered_list:
        # create a dictionary to store the ip and mac address
        # and add it to the list
        connected_devices.append({"ip": element[1].psrc, "mac": element[1].hwsrc, "hostname": None, "vendor_id": None})
    # return the list of connected devices
    return connected_devices


# a function to scan a network via ICMP
def get_connected_devices_icmp(ip, timeout=3):
    # with print_lock:
    #     print(f"[*] Scanning {ip} using ICMP")
    # create a list to store the connected devices
    connected_devices = []
    # create an ICMP packet
    icmp_packet = IP(dst=ip)/ICMP()
    # send the packet and receive a response
    response = sr1(icmp_packet, timeout=timeout, verbose=False)
    # check if the response is not None
    if response is not None:
        # create a dictionary to store the ip and mac address
        # with print_lock:
        #     print(f"[*] ICMP response from {response.src}")
        # add the device to the list
        connected_devices.append({"ip": response.src, "mac": None, "hostname": None, "vendor_id": None})
    # return the list of connected devices
    return connected_devices


# a function to scan a network via UDP
def get_connected_devices_udp(ip, timeout=3):
    # with print_lock:
    #     print(f"[*] Scanning {ip} using UDP")
    # create a list to store the connected devices
    connected_devices = []
    # create a UDP packet
    udp_packet = IP(dst=ip)/UDP(dport=0)
    # send the packet and receive a response
    response = sr1(udp_packet, timeout=timeout, verbose=False)
    # check if the response is not None
    if response is not None:
        # create a dictionary to store the ip and mac address
        # with print_lock:
        #     print(f"[*] UDP response from {response.src}")
        # add the new device to the list
        connected_devices.append({"ip": response.src, "mac": None, "hostname": None, "vendor_id": None})
    # return the list of connected devices
    return connected_devices


def get_mac(ip, timeout=3):
    """Returns the MAC address of a device"""
    connected_device = get_connected_devices_arp(ip, timeout)
    # check if the connected device list is not empty
    if connected_device:
        try:
            # return the mac address
            return connected_device[0]["mac"]
        except (IndexError, KeyError):
            # if no response was received, return None
            return None


# a function to get a list of IP addresses from a subnet
def get_ip_subnet(subnet):
    # create a list to store the ip addresses
    ip_subnet = []
    # loop through the ip addresses in the subnet
    for ip_int in ipaddress.IPv4Network(subnet):
        # add the ip address to the list
        ip_subnet.append(str(ip_int))
    # return the list of ip addresses
    return ip_subnet


# a function to get the gateway, subnet, and netmask
def get_gateway_subnet_netmask(iface):
    """Returns the gateway, subnet, and netmask"""
    # get the interface name based on the OS
    iface_name = iface.network_name if os.name == "nt" else iface
    # get the routes for the interface
    routes = [ route for route in conf.route.routes if route[3] == iface_name ]
    subnet, gateway, netmask = None, None, None
    # loop through the routes
    for route in routes:
        if route[2] != "0.0.0.0":
            gateway = route[2]
        elif str(ipaddress.IPv4Address(route[0])).endswith(".0"):
            subnet = str(ipaddress.IPv4Address(route[0]))
            netmask = str(ipaddress.IPv4Address(route[1]))
            break
    return gateway, subnet, netmask
    

# a function to convert netmask from dotted decimal to CIDR
def netmask_to_cidr(netmask):
    """Converts netmask from dotted decimal to CIDR"""
    binary_str = ""
    for octet in netmask.split("."):
        # convert the octet to binary
        binary_str += bin(int(octet))[2:].zfill(8)
    # return the number of 1s in the binary string
    return str(len(binary_str.rstrip("0")))


def is_valid_subnet_cidr(subnet_cidr):
    """Determines whether a string is a valid <subnet>/<cidr> address"""
    try:
        # split the subnet and cidr
        subnet, cidr = subnet_cidr.split("/")
        # check if the cidr is valid
        if not 0 <= int(cidr) <= 32:
            return False
        # check if the subnet is valid
        ipaddress.IPv4Network(subnet_cidr) # throws ValueError if invalid
        # return True if the subnet and cidr are valid
        return True
    except ValueError:
        # return False if the subnet and cidr are not valid
        return False
    

# a function to validate an ip address range
def is_valid_ip_range(ip_range):
    """Determines whether a string is a valid <start>-<end> IP address range"""
    try:
        # split the start and end ip addresses
        start, end = ip_range.split("-")
        # check if the start and end ip addresses are valid
        if not is_valid_ip(start) or not is_valid_ip(end):
            return False
        # return True if the start and end ip addresses are valid
        return True
    except ValueError:
        # return False if the start and end ip addresses are not valid
        return False


def is_valid_ip(ip):
    """Determines whether a string is a valid IP address"""
    try:
        # check if the ip address is valid
        ipaddress.ip_address(ip)
        # return True if the ip address is valid
        return True
    except ValueError:
        # return False if the ip address is not valid
        return False

    
def ip_range_to_subnets(ip_range):
    """A function to convert an IP address range to a list of subnets, assuming the range is valid"""
    # split the start and end ip addresses
    start_ip, end_ip = ip_range.split("-")
    # return the list of subnets
    return [str(ip) for ip in ipaddress.summarize_address_range(ipaddress.IPv4Address(start_ip), ipaddress.IPv4Address(end_ip))]


class ARPScanner(threading.Thread):
    
    def __init__(self, subnets, timeout=3, interval=60):
        super().__init__()
        self.subnets = subnets
        self.timeout = timeout
        self.interval = interval
        # set a name for the thread
        self.name = f"ARPScanner-{subnets}-{timeout}-{interval}"
        self.connected_devices = []
        self.lock = threading.Lock()
        
    def run(self):
        try:
            while True:
                for subnet in self.subnets:
                    connected_devices = get_connected_devices_arp(subnet, self.timeout)
                    with self.lock:
                        self.connected_devices += connected_devices
                # with print_lock:
                #     print(f"[+] Got {len(self.connected_devices)} devices from {self.subnets} using ARP")
                time.sleep(self.interval)
        except KeyboardInterrupt:
            print(f"[-] Stopping {self.name}")
            return


# abstract scanner class
class Scanner(threading.Thread):
    
    def __init__(self, subnets, timeout=3, interval=60):
        super().__init__()
        self.subnets = subnets
        self.timeout = timeout
        self.interval = interval
        self.connected_devices = []
        self.lock = threading.Lock()
        
    def get_connected_devices(self, ip_address):
        # this method should be implemented in the child class
        raise NotImplementedError("This method should be implemented in UDPScanner or ICMPScanner")
    
    def run(self):
        while True:
            for subnet in self.subnets:
                # get the ip addresses from the subnet
                ip_addresses = get_ip_subnet(subnet)
                # split the ip addresses into chunks for threading
                ip_addresses_chunks = [ip_addresses[i:i+NUM_IPS_PER_CHUNK] for i in range(0, len(ip_addresses), NUM_IPS_PER_CHUNK)]
                # create a list to store the threads
                threads = []
                # loop through the ip addresses chunks
                for ip_addresses_chunk in ip_addresses_chunks:
                    # create a thread
                    thread = threading.Thread(target=self.scan, args=(ip_addresses_chunk,))
                    # add the thread to the list
                    threads.append(thread)
                    # start the thread
                    thread.start()
                # loop through the threads
                for thread in threads:
                    # join the thread, maybe this loop should be deleted as the other subnet is waiting 
                    # (if there are multiple subnets)
                    thread.join()
            time.sleep(self.interval)
            
    def scan(self, ip_addresses):
        for ip_address in ip_addresses:
            connected_devices = self.get_connected_devices(ip_address)
            with self.lock:
                self.connected_devices += connected_devices   


class ICMPScanner(Scanner):
    
    def __init__(self, subnets, timeout=3, interval=60):
        super().__init__(subnets, timeout, interval)
        # set a name for the thread
        self.name = f"ICMPScanner-{subnets}-{timeout}-{interval}"
    
    def get_connected_devices(self, ip_address):
        return get_connected_devices_icmp(ip_address, self.timeout)


class UDPScanner(Scanner):
    
    def __init__(self, subnets, timeout=3, interval=60):
        super().__init__(subnets, timeout, interval)
        # set a name for the thread
        self.name = f"UDPScanner-{subnets}-{timeout}-{interval}"
    
    def get_connected_devices(self, ip_address):
        return get_connected_devices_udp(ip_address, self.timeout)
                
        
class PassiveSniffer(threading.Thread):
    
    def __init__(self, subnets):
        super().__init__()
        self.subnets = subnets
        self.connected_devices = []
        self.lock = threading.Lock()
        self.networks = [ ipaddress.IPv4Network(subnet) for subnet in self.subnets ]
        # add stop event
        self.stop_sniff = threading.Event()
        
    def run(self):
        sniff(
            prn=self.process_packet, # function to process the packet
            store=0, # don't store packets in memory
            stop_filter=self.stop_sniffer, # stop sniffing when stop_sniff is set
        )
        
    def process_packet(self, packet):
        # check if the packet has an IP layer
        if packet.haslayer(IP):
            # get the source ip address
            src_ip = packet[IP].src
            # check if the source ip address is in the subnets
            if self.is_ip_in_network(src_ip):
                # get the mac address
                src_mac = packet[Ether].src
                # create a dictionary to store the device info
                device = {"ip": src_ip, "mac": src_mac, "hostname": None, "vendor_id": None}
                # add the device to the list
                if device not in self.connected_devices:
                    with self.lock:
                        self.connected_devices.append(device)
                    # with print_lock:
                    #     print(f"[+] Found {src_ip} using passive sniffing")
        # looking for DHCP packets
        if packet.haslayer(DHCP):
            # initialize these variables to None at first
            target_mac, requested_ip, hostname, vendor_id = [None] * 4
            # get the MAC address of the requester
            if packet.haslayer(Ether):
                target_mac = packet.getlayer(Ether).src
            # get the DHCP options
            dhcp_options = packet[DHCP].options
            for item in dhcp_options:
                try:
                    label, value = item
                except ValueError:
                    continue
                if label == "requested_addr":
                    requested_ip = value
                elif label == "hostname":
                    # get the hostname of the device
                    hostname = value.decode()
                elif label == "vendor_class_id":
                    # get the vendor ID
                    vendor_id = value.decode()
            # create a dictionary to store the device info
            device = {"ip": requested_ip, "mac": target_mac, "hostname": hostname, "vendor_id": vendor_id}
            with print_lock:
                print(f"[+] Found {requested_ip} using DHCP: {device}")
            # add the device to the list
            if device not in self.connected_devices:
                with self.lock:
                    self.connected_devices.append(device)
                    
    def is_ip_in_network(self, ip):
        # check if the ip address is in the subnet
        for network in self.networks:
            if ipaddress.IPv4Address(ip) in network:
                return True
        return False
                     
    def join(self):
        # set the stop sniff event
        self.stop_sniff.set()
        # join the thread
        super().join()
        
    def stop_sniffer(self, packet):
        return self.stop_sniff.is_set()

  
# an aggregator class between scanners
class NetworkScanner(threading.Thread):
        
    def __init__(self, subnets, timeout=3, **kwargs):
        super().__init__()
        self.subnets = subnets
        self.timeout = timeout
        self.daemon = True
        self.connected_devices = pd.DataFrame(columns=["ip", "mac"])
        self.arpscanner_interval = kwargs.get("arpscanner_interval", 60)
        self.udpscanner_interval = kwargs.get("udpscanner_interval", 60)
        self.icmpscanner_interval = kwargs.get("icmpscanner_interval", 60)
        self.interval = kwargs.get("interval", 5)
        self.lock = threading.Lock()
        # create a list to store the threads
        self.threads = []
        
    def run(self):
        # create a dataframe to store the connected devices
        connected_devices = pd.DataFrame(columns=["ip", "mac"]) 
        # create a thread for the ARP scanner
        if self.arpscanner_interval:
            thread = ARPScanner(self.subnets, self.timeout, self.arpscanner_interval)
            self.threads.append(thread)
            thread.start()
        # create a thread for the UDP scanner
        if self.udpscanner_interval:
            thread = UDPScanner(self.subnets, self.timeout, self.udpscanner_interval)
            self.threads.append(thread)
            thread.start()
        # create a thread for the ICMP scanner
        if self.icmpscanner_interval:
            thread = ICMPScanner(self.subnets, self.timeout, self.icmpscanner_interval)
            self.threads.append(thread)
            thread.start()
        while True:
            # loop through the threads
            for thread in self.threads:
                # add the connected devices to the dataframe
                with thread.lock:
                    connected_devices = pd.concat([connected_devices, pd.DataFrame(thread.connected_devices)])
            # get the MAC addresses when the MAC is None
            try:
                connected_devices["mac"] = connected_devices.apply(lambda x: get_mac(x["ip"]) if x["mac"] is None else x["mac"], axis=1)
            except ValueError:
                pass # most likely the dataframe is empty
            # set the connected devices
            with self.lock:
                self.connected_devices = pd.concat([self.connected_devices, connected_devices])
            time.sleep(self.interval)

    
# a function to aggregate the connected devices from the NetworkScanner class and the PassiveSniffer
def aggregate_connected_devices(previous_connected_devices, network_scanner, passive_sniffer):
    # get the connected devices from the network scanner
    with network_scanner.lock:
        connected_devices = network_scanner.connected_devices
    # get the connected devices from the passive sniffer
    if passive_sniffer:
        with passive_sniffer.lock:
            passive_devices = passive_sniffer.connected_devices
    else:
        # create an empty list
        passive_devices = []
    # combine the connected devices from the previous scan, the network scanner, and the passive sniffer
    connected_devices = pd.concat([
        previous_connected_devices, 
        connected_devices, 
        pd.DataFrame(passive_devices, columns=["ip", "mac", "hostname", "vendor_id"]) # convert the list to a dataframe
    ])
    # remove duplicate ip addresses with least info
    connected_devices = connected_devices.sort_values(["mac", "hostname", "vendor_id"], ascending=False).drop_duplicates("ip", keep="first")
    # connected_devices.drop_duplicates(subset="ip", inplace=True)
    # drop the rows with None IP Addresses
    connected_devices.dropna(subset=["ip"], inplace=True)
    # sort the connected devices by ip
    connected_devices = connected_devices.sort_values(by="ip")
    # reset the index
    connected_devices = connected_devices.reset_index(drop=True)
    # return the connected devices
    return connected_devices
    

def main(args):
    if not args.network:
        # get gsn
        _, subnet, netmask = get_gateway_subnet_netmask(conf.iface)
        # get the cidr
        cidr = netmask_to_cidr(netmask)
        subnets = [f"{subnet}/{cidr}"]
    else:
        # check if the network passed is a valid <subnet>/<cidr> format
        if is_valid_subnet_cidr(args.network):
            subnets = [args.network]
        elif is_valid_ip_range(args.network):
            # convert the ip range to a subnet
            subnets = ip_range_to_subnets(args.network)
            print(f"[+] Converted {args.network} to {subnets}")
        else:
            print(f"[-] Invalid network: {args.network}")
            # get gsn
            _, subnet, netmask = get_gateway_subnet_netmask(conf.iface)
            # get the cidr
            cidr = netmask_to_cidr(netmask)
            subnets = [f"{subnet}/{cidr}"]
            print(f"[*] Using the default network: {subnets}")
    # start the passive sniffer if specified
    if args.passive:
        passive_sniffer = PassiveSniffer(subnets)
        passive_sniffer.start()
    else:
        passive_sniffer = None
    connected_devices = pd.DataFrame(columns=["ip", "mac"])
    # create the network scanner object
    network_scanner = NetworkScanner(subnets, timeout=args.timeout, 
                                    arpscanner_interval=args.arp, udpscanner_interval=args.udp, 
                                    icmpscanner_interval=args.icmp, interval=args.interval)
    network_scanner.start()
    # sleep for 5 seconds, to give the user time to read some logging messages
    time.sleep(5)
    try:
        while True:
            # aggregate the connected devices
            connected_devices = aggregate_connected_devices(connected_devices, network_scanner, passive_sniffer)
            # make a copy dataframe of the connected devices
            printing_devices_df = connected_devices.copy() 
            # add index column at the beginning from 1 to n
            printing_devices_df.insert(0, "index", range(1, len(printing_devices_df) + 1))
            # rename the columns
            printing_devices_df.columns = ["Device", "IP Address", "MAC Address", "Hostname", "DHCP Vendor ID"]
            # clear the screen
            os.system("cls" if os.name == "nt" else "clear")
            # print the dataframe
            if not printing_devices_df.empty:
                with print_lock:
                    print(printing_devices_df.to_string(index=False))
            # sleep for few seconds
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("[+] Stopping the network scanner")
        # if the passive sniffer is running, stop it
        if passive_sniffer:
            passive_sniffer.join()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Advanced Network Scanner")
    parser.add_argument("-n", "--network", help="Network to scan, in the form <subnet>/<cidr>, e.g 192.168.1.0/24. " \
                                                "Or a range of IP addresses, e.g 192.168.1.1-192.168.1.255"
                                                "If not specified, the network will be automatically detected of the default interface")
    parser.add_argument("-t", "--timeout", help="Timeout for each scan, default is 3 seconds", type=float, default=3.0)
    parser.add_argument("-a", "--arp", help="ARP scanner interval in seconds, default is 60 seconds", type=int, default=60)
    parser.add_argument("-u", "--udp", help="UDP scanner interval in seconds, default is 60 seconds", type=int, default=60)
    parser.add_argument("-p", "--icmp", help="ICMP scanner interval in seconds, default is 60 seconds", type=int, default=60)
    parser.add_argument("-i", "--interval", help="Interval in seconds to print the connected devices, default is 5 seconds", type=int, default=5)
    parser.add_argument("--passive", help="Use passive sniffing", action="store_true")
    # parse the arguments
    args = parser.parse_args()
    # run the program
    main(args)
