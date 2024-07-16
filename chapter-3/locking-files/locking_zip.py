import pyzipper

def create_protected_zip(output_zip, file_paths, password):
    """
    Creates a password-protected ZIP file with AES encryption.
    
    Args:
    output_zip (str): The name of the output ZIP file.
    file_paths (list): A list of paths to the files to be included in the ZIP.
    password (str): The password to secure the ZIP file.
    """
    # Use AES encryption
    with pyzipper.AESZipFile(output_zip, 'w', compression=pyzipper.ZIP_DEFLATED, encryption=pyzipper.WZ_AES) as zf:
        zf.setpassword(password.encode('utf-8'))
        # Add files to the ZIP file
        for file_path in file_paths:
            zf.write(file_path, arcname=file_path.split('/')[-1])

    print(f"ZIP file '{output_zip}' created and locked with a password.")

# Example usage
files_to_zip = ['files/example.pdf', 'files/image.jpg']
create_protected_zip("files/secure_example.zip", files_to_zip, password="secure1234")
