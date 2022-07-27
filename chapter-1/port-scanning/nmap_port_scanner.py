import nmap
import sys

# get the target host(s) from the command-line arguments
target = sys.argv[1]
# initialize the Nmap port scanner
nm = nmap.PortScanner()
print("[*] Scanning...")
# scanning my router
nm.scan(target)
# get scan statistics
scan_stats = nm.scanstats()
print(f"[{scan_stats['timestr']}] Elapsed: {scan_stats['elapsed']}s  " \
    f"Up hosts: {scan_stats['uphosts']}  Down hosts: {scan_stats['downhosts']}  " \
        f"Total hosts: {scan_stats['totalhosts']}")

equivalent_commandline = nm.command_line()
print(f"[*] Equivalent command: {equivalent_commandline}")

# get all the scanned hosts
hosts = nm.all_hosts()
for host in hosts:
    # get host name
    hostname = nm[host].hostname()
    # get the addresses
    addresses = nm[host].get("addresses")
    # get the IPv4
    ipv4 = addresses.get("ipv4")
    # get the MAC address of this host
    mac_address = addresses.get("mac")
    # extract the vendor if available
    vendor = nm[host].get("vendor")
    # get the open TCP ports
    open_tcp_ports = nm[host].all_tcp()
    # get the open UDP ports
    open_udp_ports = nm[host].all_udp()
    # print details
    print("="*30, host, "="*30)
    print(f"Hostname: {hostname} IPv4: {ipv4}  MAC: {mac_address}")
    print(f"Vendor: {vendor}")
    if open_tcp_ports or open_udp_ports:
        print("-"*30, "Ports Open", "-"*30)
    for tcp_port in open_tcp_ports:
        # get all the details available for the port
        port_details = nm[host].tcp(tcp_port)
        port_state = port_details.get("state")
        port_up_reason = port_details.get("reason")
        port_service_name = port_details.get("name")
        port_product_name = port_details.get("product")
        port_product_version = port_details.get("version")
        port_extrainfo = port_details.get("extrainfo")
        port_cpe = port_details.get("cpe")
        print(f"  TCP Port: {tcp_port}  Status: {port_state}  Reason: {port_up_reason}")
        print(f"  Service: {port_service_name}  Product: {port_product_name}  Version: {port_product_version}")
        print(f"  Extra info: {port_extrainfo}  CPE: {port_cpe}")
        print("-"*50)
    
    if open_udp_ports:
        print(open_udp_ports)
