import whois # pip install python-whois

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
    
    
if __name__ == "__main__":
    print(is_registered("google.com"))
    print(is_registered("something-that-do-not-exist.com"))