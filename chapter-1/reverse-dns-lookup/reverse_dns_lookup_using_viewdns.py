# Import the necessary libraries
import argparse
import ipaddress
import requests

API_KEY = "YOUR_VIEWDNS_API_KEY"

# Function to Check if IP address is valid.
def is_valid_ip(ip):
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False


# Get domains on the same IP
def get_domains_on_same_ip(ip):
    url = f"https://api.viewdns.info/reverseip/?host={ip}&apikey={API_KEY}&output=json"
    response = requests.get(url)
    if response.status_code == 200:
        try:
            data = response.json()
        except:
            print("[-] Error parsing JSON response.")
            print(response.text)
            return []
        domain_count = data["response"]["domain_count"]
        print(f"\n[*] Found {domain_count} domains on {ip}:")
        if "response" in data and "domains" in data["response"]:
            websites = data["response"]["domains"]
            return websites
    return []


# Get user arguments and execute.
def main():
    parser = argparse.ArgumentParser(description="Perform IP reverse lookup. Requires a ViewDNS API key.")
    parser.add_argument("ips", nargs="+", help="IP address(es) to perform reverse lookup on.")
    args = parser.parse_args()

    for ip in args.ips:
        if not is_valid_ip(ip):
            print(f"[-] Invalid IP address: {ip}")
            continue
        # Get other domains on the same IP
        domains = get_domains_on_same_ip(ip)
        if domains:
            for d in domains:
                print(f"[+] {d}")
        else:
            print("[-] No other domains found on the same IP.")


if __name__ == "__main__":
    main()
