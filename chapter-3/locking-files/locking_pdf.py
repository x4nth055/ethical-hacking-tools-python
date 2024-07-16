import fitz  # PyMuPDF

def lock_pdf(input_file, output_file, password):
    """
    Locks a PDF file with the given password.
    
    Args:
    input_file (str): The path to the PDF file to be locked.
    output_file (str): The path where the locked PDF will be saved.
    password (str): The password to encrypt the PDF.
    """
    # Open the existing PDF
    document = fitz.open(input_file)
    # Encrypt the document
    document.save(output_file, encryption=fitz.PDF_ENCRYPT_AES_256, owner_pw=password, user_pw=password, permissions=fitz.PDF_PERM_FORM)
    # Close the document
    document.close()
    print(f"PDF locked and saved as {output_file}")

# Example usage
lock_pdf("files/example.pdf", "files/locked_example.pdf", "secure1234")
