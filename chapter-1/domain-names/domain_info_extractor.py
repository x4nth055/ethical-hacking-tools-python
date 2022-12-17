import requests
import whois
import dns.resolver
import argparse


def is_registered(domain_name):
    """
    A function that returns a boolean indicating 
    whether a `domain_name` is registered
    """
    try:
        w = whois.whois(domain_name)
    except Exception:
        return False
    else:
        return bool(w.domain_name)
    
    
def get_discovered_subdomains(domain, subdomain_list, timeout=2):
    # a list of discovered subdomains
    discovered_subdomains = []
    for subdomain in subdomain_list:
        # construct the url
        url = f"http://{subdomain}.{domain}"
        try:
            # if this raises a connection error, that means the subdomain does not exist
            requests.get(url, timeout=timeout)
        except requests.ConnectionError:
            # if the subdomain does not exist, just pass, print nothing
            pass
        else:
            print("[+] Discovered subdomain:", url)
            # append the discovered subdomain to our list
            discovered_subdomains.append(url)
            
    return discovered_subdomains

def resolve_dns_records(target_domain):
    """A function that resolves DNS records for a `target_domain`"""
    # List of record types to resolve
    record_types = ["A", "AAAA", "CNAME", "MX", "NS", "SOA", "TXT"]
    # Create a DNS resolver
    resolver = dns.resolver.Resolver()
    for record_type in record_types:
        # Perform DNS lookup for the target domain and record type
        try:
            answers = resolver.resolve(target_domain, record_type)
        except dns.resolver.NoAnswer:
            continue
        # Print the DNS records found
        print(f"DNS records for {target_domain} ({record_type}):")
        for rdata in answers:
            print(rdata)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Domain name information extractor, uses WHOIS db and scans for subdomains")
    parser.add_argument("domain", help="The domain name without http(s)")
    parser.add_argument("-t", "--timeout", type=int, default=2,
                        help="The timeout in seconds for prompting the connection, default is 2")
    parser.add_argument("-s", "--subdomains", default="subdomains.txt",
                        help="The file path that contains the list of subdomains to scan, default is subdomains.txt")
    parser.add_argument("-o", "--output",
                        help="The output file path resulting the discovered subdomains, default is {domain}-subdomains.txt")

    # parse the command-line arguments
    args = parser.parse_args()
    if is_registered(args.domain):
        whois_info = whois.whois(args.domain)
        # print the registrar
        print("Domain registrar:", whois_info.registrar)
        # print the WHOIS server
        print("WHOIS server:", whois_info.whois_server)
        # get the creation time
        print("Domain creation date:", whois_info.creation_date)
        # get expiration date
        print("Expiration date:", whois_info.expiration_date)
        # print all other info
        print(whois_info)
    print("="*50, "DNS records", "="*50)
    resolve_dns_records(args.domain)
    print("="*50, "Scanning subdomains", "="*50)
    # read all subdomains
    with open(args.subdomains) as file:
        # read all content
        content = file.read()
        # split by new lines
        subdomains = content.splitlines()
    discovered_subdomains = get_discovered_subdomains(args.domain, subdomains)
    # make the discovered subdomains filename dependant on the domain
    discovered_subdomains_file = f"{args.domain}-subdomains.txt"
    # save the discovered subdomains into a file
    with open(discovered_subdomains_file, "w") as f:
        for subdomain in discovered_subdomains:
            print(subdomain, file=f)