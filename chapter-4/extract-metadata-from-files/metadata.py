import ffmpeg
from tinytag import TinyTag
import sys
from pprint import pprint # for printing Python dictionaries in a human-readable way
from PIL import Image
from PIL.ExifTags import TAGS
import sys
import pikepdf


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



if __name__ == "__main__":
    file = sys.argv[1]
    if file.endswith(".pdf"):
        print(get_pdf_metadata(file))
    elif file.endswith(".jpg"):
        pprint(get_image_metadata(file))
    else:
        pprint(get_media_metadata(file))