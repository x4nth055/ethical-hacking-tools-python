from PIL import Image

def remove_image_metadata(image_file, output_file):
    """
    Removes the metadata (EXIF data) from an image file.

    Args:
        image_file (str): The path to the input image file.
        output_file (str): The path to the output image file without metadata.

    Returns:
        None
    """
    with Image.open(image_file) as img:
        # Get the image data
        data = img.getdata()

        # Create a new image without the EXIF data
        image_without_exif = Image.new(img.mode, img.size)
        image_without_exif.putdata(data)

        # Save the new image to the output file
        image_without_exif.save(output_file)

# Example usage
remove_image_metadata('files/image.jpg', 'files/cleaned_image.jpg')
