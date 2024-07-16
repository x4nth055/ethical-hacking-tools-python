import pikepdf

def remove_pdf_metadata(pdf_file, output_file):
    """
    Removes all metadata from a PDF file.

    Args:
        pdf_file (str): The path to the input PDF file.
        output_file (str): The path to the output PDF file with metadata removed.

    Returns:
        None
    """
    # Open the PDF file using the pikepdf library
    pdf = pikepdf.Pdf.open(pdf_file)

    # Open the PDF metadata and set the editor to False to avoid adding pikepdf as the editor
    with pdf.open_metadata(set_pikepdf_as_editor=False) as meta:
        # Get a list of all the metadata keys
        keys = list(meta.keys())
        # Loop through the metadata keys and delete each one
        for key in keys:
            del meta[key]

    # Save the PDF file with the metadata removed
    pdf.save(output_file)
    # Close the PDF file
    pdf.close()

# Example usage: Remove metadata from 'example.pdf' and save the result as 'cleaned_example.pdf'
remove_pdf_metadata('files/example.pdf', 'files/cleaned_example.pdf')
