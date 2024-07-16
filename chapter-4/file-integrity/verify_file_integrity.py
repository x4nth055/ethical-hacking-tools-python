import hashlib

def compute_file_hash(file_path):
    """
    Computes the SHA-256 hash of a file.
    
    Args:
    file_path (str): The path to the file whose hash is to be computed.
    
    Returns:
    str: The hexadecimal SHA-256 hash of the file.
    """
    sha256_hash = hashlib.sha256()
    # Open the file in binary mode to read it
    with open(file_path, 'rb') as file:
        # Read and update hash string value in blocks of 4K
        for byte_block in iter(lambda: file.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def verify_file_integrity(file_path, original_hash):
    """
    Verifies the integrity of a file by comparing its current hash with the original hash.
    
    Args:
    file_path (str): The path to the file to check.
    original_hash (str): The original hash of the file for comparison.
    
    Returns:
    bool: True if the file's integrity is confirmed, False otherwise.
    """
    current_hash = compute_file_hash(file_path)
    return current_hash == original_hash

# Example usage
# This should be the hash received or computed previously
original_hash = "9be104294df7d5a59c328241d49ac062e2c7b9660636e7f511e3a1dc3d919377"  
file_path = 'example.txt'
if verify_file_integrity(file_path, original_hash):
    print("File integrity verified.")
else:
    print("File integrity compromised!")

# Example usage
file_path = 'example.txt'
print(f"The SHA-256 hash of {file_path} is: {compute_file_hash(file_path)}")
