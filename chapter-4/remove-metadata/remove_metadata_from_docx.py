from docx import Document
from datetime import datetime

def remove_docx_metadata(docx_file, output_file):
    """Removes metadata from a docx file.

    Args:
        docx_file (str): The path to the input docx file.
        output_file (str): The path to save the cleaned docx file.

    Returns:
        None
    """
    # Open the document
    doc = Document(docx_file)
    # Get the core properties
    core_props = doc.core_properties
    # Remove all metadata fields
    core_props.author = ""
    core_props.title = ""
    core_props.subject = ""
    core_props.creator = ""
    core_props.keywords = ""
    core_props.description = ""
    core_props.last_modified_by = ""
    # Reset revision to 1
    core_props.revision = 1
    # Remove language and version information
    core_props.language = ""
    core_props.version = ""
    # Set modified and created dates to a dummy date
    core_props.modified = core_props.created = datetime(1970, 1, 1)
    # Save the cleaned document
    doc.save(output_file)

# Example usage: Remove metadata from 'example.docx' and save as 'cleaned_example.docx'
remove_docx_metadata('files/example.docx', 'files/cleaned_example.docx')
