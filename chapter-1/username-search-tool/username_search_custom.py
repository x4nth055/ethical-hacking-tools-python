import requests

def check_username(username, platform):
    """
    Checks if a username exists on a given platform.

    Args:
        username (str): The username to check.
        platform (str): The URL template for the platform, with '{username}' placeholder.

    Returns:
        bool: True if the username exists, False otherwise.
    """
    url = platform.format(username=username)
    response = requests.get(url)
    if response.status_code == 200:
        return True
    return False

def search_username(username):
    """
    Searches for a username across multiple social media platforms.

    Args:
        username (str): The username to search for.

    Returns:
        dict: A dictionary containing the platforms where the username was found,
              with the platform name as the key and the corresponding URL as the value.
              Returns an empty dictionary if no results are found.
    """
    platforms = {
        "GitHub": "https://github.com/{username}",
        "Twitter": "https://twitter.com/{username}",
        "Instagram": "https://www.instagram.com/{username}/",
        "Reddit": "https://www.reddit.com/user/{username}",
        "Facebook": "https://www.facebook.com/{username}",
        "LinkedIn": "https://www.linkedin.com/in/{username}",
    }
    results = {}
    for platform, url in platforms.items():
        if check_username(username, url):
            results[platform] = url.format(username=username)
    return results

# Example usage
if __name__ == "__main__":
    username = "exampleuser"
    results = search_username(username)
    if results:
        print(f"Found {username} on the following platforms:")
        for platform, url in results.items():
            print(f"{platform}: {url}")
    else:
        print(f"No results found for {username}")
