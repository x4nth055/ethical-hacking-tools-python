import ffmpeg
from tinytag import TinyTag
import sys
from pprint import pprint # for printing Python dictionaries in a human-readable way
from PIL import Image
from PIL.ExifTags import TAGS
import sys
import pikepdf
from docx import Document


def get_media_metadata(media_file):
    # uses ffprobe command to extract all possible metadata from the media file
    ffmpeg_data = ffmpeg.probe(media_file)["streams"][0]
    tt_data = TinyTag.get(media_file).as_dict()
    # add both data to a single dict
    return {**tt_data, **ffmpeg_data}
    
    

def get_image_metadata(image_file):
    # read the image data using PIL
    image = Image.open(image_file)
    # extract other basic metadata
    info_dict = {
        "Filename": image.filename,
        "Image Size": image.size,
        "Image Height": image.height,
        "Image Width": image.width,
        "Image Format": image.format,
        "Image Mode": image.mode,
        "Image is Animated": getattr(image, "is_animated", False),
        "Frames in Image": getattr(image, "n_frames", 1)
    }  
    # extract EXIF data
    exifdata = image.getexif()
    # iterating over all EXIF data fields
    for tag_id in exifdata:
        # get the tag name, instead of human unreadable tag id
        tag = TAGS.get(tag_id, tag_id)
        data = exifdata.get(tag_id)
        # decode bytes 
        if isinstance(data, bytes):
            data = data.decode()
        # print(f"{tag:25}: {data}")
        info_dict[tag] = data
    return info_dict


def get_pdf_metadata(pdf_file):
    # read the pdf file
    pdf = pikepdf.Pdf.open(pdf_file)
    # .docinfo attribute contains all the metadata of
    # the PDF document
    return dict(pdf.docinfo)


def get_docx_metadata(docx_file):
    """
    Extracts metadata from a DOCX file.
    
    Args:
    docx_file (str): The path to the .docx file.
    
    Returns:
    dict: A dictionary containing metadata information.
    """
    # Load the DOCX file
    doc = Document(docx_file)
    
    # Accessing document properties
    props = doc.core_properties
    return {
        "author": props.author,
        "category": props.category,
        "comments": props.comments,
        "content_status": props.content_status,
        "created": props.created,
        "identifier": props.identifier,
        "keywords": props.keywords,
        "language": props.language,
        "last_modified_by": props.last_modified_by,
        "last_printed": props.last_printed,
        "modified": props.modified,
        "revision": props.revision,
        "subject": props.subject,
        "title": props.title,
        "version": props.version
    }


if __name__ == "__main__":
    file = sys.argv[1]
    if file.endswith(".pdf"):
        print(get_pdf_metadata(file))
    elif file.endswith(".jpg"):
        pprint(get_image_metadata(file))
    elif file.endswith(".docx"):
        pprint(get_docx_metadata(file))
    else:
        pprint(get_media_metadata(file))