import fitz
from tqdm import tqdm

def crack_pdf(pdf_path, password_list):
    """Crack PDF password using a list of passwords
    Args:
        pdf_path (str): Path to the PDF file
        password_list (list): List of passwords to try
    Returns:
        [str]: Returns the password if found, else None"""
    # open the PDF
    doc = fitz.open(pdf_path)
    # iterate over passwords
    for password in tqdm(password_list, "Guessing password"):
        # try to open with the password
        if doc.authenticate(password):
            # when password is found, authenticate returns non-zero
            # break out of the loop & return the password
            return password
    
if __name__ == "__main__":
    import sys
    pdf_filename = sys.argv[1]
    wordlist_filename = sys.argv[2]
    # load the password list
    with open(wordlist_filename, "r", errors="replace") as f:
        # read all passwords into a list
        passwords = f.read().splitlines()
    # call the function to crack the password
    password = crack_pdf(pdf_filename, passwords)
    if password:
        print(f"[+] Password found: {password}")
    else:
        print("[!] Password not found")