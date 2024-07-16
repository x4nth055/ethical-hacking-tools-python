import ffmpeg

def remove_media_metadata(media_file, output_file):
    """
    Removes the metadata from a media file and saves it to a new file.

    Args:
        media_file (str): The path to the input media file.
        output_file (str): The path to the output media file where the cleaned version will be saved.

    Returns:
        None
    """
    (
        ffmpeg
        .input(media_file)
        .output(output_file, map_metadata=-1)
        .run()
    )

# Example usage
# This code removes the metadata from the 'example.mp3' file
# and saves the cleaned version to 'cleaned_example.mp3'
remove_media_metadata('files/example.mp3', 'files/cleaned_example.mp3')
