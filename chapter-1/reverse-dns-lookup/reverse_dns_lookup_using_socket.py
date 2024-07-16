import socket

def reverse_dns_lookup(ip_address):
    try:
        host, _, _ = socket.gethostbyaddr(ip_address)
        return host
    except socket.herror:
        return None

# Example usage
if __name__ == "__main__":
    ip_address = "8.8.8.8"  # Example IP address (Google DNS)
    domain_name = reverse_dns_lookup(ip_address)
    if domain_name:
        print(f"The domain name for IP address {ip_address} is {domain_name}")
    else:
        print(f"No domain name found for IP address {ip_address}")
