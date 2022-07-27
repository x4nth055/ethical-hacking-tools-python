import re
import argparse
import threading
from urllib.parse import urlparse, urljoin
from queue import Queue
import time
import warnings
warnings.filterwarnings("ignore")

import requests
from bs4 import BeautifulSoup
import colorama

# init the colorama module
colorama.init()

# initialize some colors
GREEN = colorama.Fore.GREEN
GRAY = colorama.Fore.LIGHTBLACK_EX
RESET = colorama.Fore.RESET
YELLOW = colorama.Fore.YELLOW
RED = colorama.Fore.RED

EMAIL_REGEX = r"""(?:[a-z0-9!#$%&'*+=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*|"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])*")@(?:(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?|\[(?:(?:(2(5[0-5]|[0-4][0-9])|1[0-9][0-9]|[1-9]?[0-9]))\.){3}(?:(2(5[0-5]|[0-4][0-9])|1[0-9][0-9]|[1-9]?[0-9])|[a-z0-9-]*[a-z0-9]:(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21-\x5a\x53-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f]){2,12})\])"""
# EMAIL_REGEX = r"[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]{2,12})*"

# forbidden TLDs, feel free to add more extensions here to prevent them identified as TLDs
FORBIDDEN_TLDS = [
    "js", "css", "jpg", "png", "svg", "webp", "gz", "zip", "webm", "mp3", 
    "wav", "mp4", "gif", "tar", "gz", "rar", "gzip", "tgz",
]
# a list of forbidden extensions in URLs, i.e 'gif' URLs won't be requested
FORBIDDEN_EXTENSIONS = [
    "js", "css", "jpg", "png", "svg", "webp", "gz", "zip", "webm", "mp3", 
    "wav", "mp4", "gif", "tar", "gz", "rar", "gzip", "tgz", 
]

# locks to assure mutex, one for output console & another for a file
print_lock = threading.Lock()
file_lock = threading.Lock()

def is_valid_email_address(email):
    """Verify whether `email` is a valid email address
    Args:
        email (str): The target email address.
    Returns: bool"""
    for forbidden_tld in FORBIDDEN_TLDS:
        if email.endswith(forbidden_tld):
            # if the email ends with one of the forbidden TLDs, return False
            return False
    if re.search(r"\..{1}$", email):
        # if the TLD has a length of 1, definitely not an email
        return False
    elif re.search(r"\..*\d+.*$", email):
        # TLD contain numbers, not an email either
        return False
    # return true otherwise
    return True


def is_valid_url(url):
    """
    Checks whether `url` is a valid URL.
    """
    parsed = urlparse(url)
    return bool(parsed.netloc) and bool(parsed.scheme)


def is_text_url(url):
    """Returns False if the URL is one of the forbidden extensions.
    True otherwise"""
    for extension in FORBIDDEN_EXTENSIONS:
        if url.endswith(extension):
            return False
    return True


class Crawler(threading.Thread):
    def __init__(self, first_url, delay, crawl_external_urls=False, max_crawl_urls=30):
        # Call the Thread class's init function
        super().__init__()
        self.first_url = first_url
        self.delay = delay
        # whether to crawl external urls than the domain specified in the first url
        self.crawl_external_urls = crawl_external_urls
        self.max_crawl_urls = max_crawl_urls
        # a dictionary that stores visited urls along with their HTML content
        self.visited_urls = {}
        # domain name of the base URL without the protocol
        self.domain_name = urlparse(self.first_url).netloc
        # simple debug message to see whether domain is extracted successfully
        # print("Domain name:", self.domain_name)
        # initialize the set of links (unique links)
        self.internal_urls = set()
        self.external_urls = set()
        # initialize the queue that will be read by the email spider
        self.urls_queue = Queue()
        # add the first URL to the queue
        self.urls_queue.put(self.first_url)
        # a counter indicating the total number of URLs visited
        # used to stop crawling when reaching `self.max_crawl_urls`
        self.total_urls_visited = 0

    def get_all_website_links(self, url):
        """
        Returns all URLs that is found on `url` in which it belongs to the same website
        """
        # all URLs of `url`
        urls = set()
        # make the HTTP request
        res = requests.get(url, verify=False, timeout=10)
        # construct the soup to parse HTML
        soup = BeautifulSoup(res.text, "html.parser")
        # store the visited URL along with the HTML
        self.visited_urls[url] = res.text
        for a_tag in soup.findAll("a"):
            href = a_tag.attrs.get("href")
            if href == "" or href is None:
                # href empty tag
                continue
            # join the URL if it's relative (not absolute link)
            href = urljoin(url, href)
            parsed_href = urlparse(href)
            # remove URL GET parameters, URL fragments, etc.
            href = parsed_href.scheme + "://" + parsed_href.netloc + parsed_href.path
            if not is_valid_url(href):
                # not a valid URL
                continue
            if href in self.internal_urls:
                # already in the set
                continue
            if self.domain_name not in href:
                # external link
                if href not in self.external_urls:
                    # debug message to see external links when they're found
                    # print(f"{GRAY}[!] External link: {href}{RESET}")
                    # external link, add to external URLs set
                    self.external_urls.add(href)
                    if self.crawl_external_urls:
                        # if external links are allowed to extract emails from,
                        # put them in the queue
                        self.urls_queue.put(href)
                continue
            # debug message to see internal links when they're found
            # print(f"{GREEN}[*] Internal link: {href}{RESET}")
            # add the new URL to urls, queue and internal URLs
            urls.add(href)
            self.urls_queue.put(href)
            self.internal_urls.add(href)
        return urls

    def crawl(self, url):
        """
        Crawls a web page and extracts all links.
        You'll find all links in `self.external_urls` and `self.internal_urls` attributes.
        """
        # if the URL is not a text file, i.e not HTML, PDF, text, etc.
        # then simply return and do not crawl, as it's unnecessary download
        if not is_text_url(url):
            return
        # increment the number of URLs visited
        self.total_urls_visited += 1
        with print_lock:
            print(f"{YELLOW}[*] Crawling: {url}{RESET}")
        # extract all the links from the URL
        links = self.get_all_website_links(url)
        for link in links:
            # crawl each link extracted if max_crawl_urls is still not reached
            if self.total_urls_visited > self.max_crawl_urls:
                break
            self.crawl(link)
            # simple delay for not overloading servers & cause it to block our IP
            time.sleep(self.delay)
            
    def run(self):
        # the running thread will start crawling the first URL passed
        self.crawl(self.first_url)
    


class EmailSpider:
    def __init__(self, crawler: Crawler, n_threads=20, output_file="extracted-emails.txt"):
        self.crawler = crawler
        # the set that contain the extracted URLs
        self.extracted_emails = set()
        # the number of threads 
        self.n_threads = n_threads
        self.output_file = output_file
        
        
    def get_emails_from_url(self, url):
        # if the url ends with an extension not in our interest, 
        # return an empty set
        if not is_text_url(url):
            return set()
        # get the HTTP Response if the URL isn't visited by the crawler
        if url not in self.crawler.visited_urls:
            try:
                with print_lock:
                    print(f"{YELLOW}[*] Getting Emails from {url}{RESET}")
                r = requests.get(url, verify=False, timeout=10)
            except Exception as e:
                with print_lock:
                    print(e)
                return set()
            else:
                text = r.text
        else:
            # if the URL is visited by the crawler already, 
            # then get the response HTML directly, no need to request again
            text = self.crawler.visited_urls[url]
        emails = set()
        try:
            # we use finditer() to find multiple email addresses if available
            for re_match in re.finditer(EMAIL_REGEX, text):
                email = re_match.group()
                # if it's a valid email address, add it to our set
                if is_valid_email_address(email):
                    emails.add(email)
        except Exception as e:
            with print_lock:
                print(e)
            return set()
        # return the emails set
        return emails
    
    def scan_urls(self):
        while True:
            # get the URL from the URLs queue
            url = self.crawler.urls_queue.get()
            # extract the emails from the response HTML
            emails = self.get_emails_from_url(url)
            for email in emails:
                with print_lock:
                    print("[+] Got email:", email, "from url:", url)
                if email not in self.extracted_emails:
                    # if the email extracted is not in the extracted emails set
                    # add it to the set and print to the output file as well
                    with file_lock:
                        with open(self.output_file, "a") as f:
                            print(email, file=f)
                    self.extracted_emails.add(email)
            # task done for that queue item
            self.crawler.urls_queue.task_done()
        
        
    def run(self):
        for t in range(self.n_threads):
            # spawn self.n_threads to run self.scan_urls
            t = threading.Thread(target=self.scan_urls)
            # daemon thread
            t.daemon = True
            t.start()
            
        # wait for the queue to empty
        self.crawler.urls_queue.join()
        print(f"[+] A total of {len(self.extracted_emails)} emails were extracted & saved.")


def track_stats(crawler: Crawler):
    # print some stats about the crawler & active threads every 5 seconds, 
    # feel free to adjust this on your own needs
    while is_running:
        with print_lock:
            print(f"{RED}[+] Queue size: {crawler.urls_queue.qsize()}{RESET}")
            print(f"{GRAY}[+] Total Extracted External links: {len(crawler.external_urls)}{RESET}")
            print(f"{GREEN}[+] Total Extracted Internal links: {len(crawler.internal_urls)}{RESET}")
            print(f"[*] Total threads running: {threading.active_count()}")
        time.sleep(5)
        

def start_stats_tracker(crawler: Crawler):
    # wrapping function to spawn the above function in a separate daemon thread
    t = threading.Thread(target=track_stats, args=(crawler,))
    t.daemon = True
    t.start()


if __name__ == "__main__":    
    parser = argparse.ArgumentParser(description="Advanced Email Spider")
    parser.add_argument("url", help="URL to start crawling from & extracting email addresses")
    parser.add_argument("-m", "--max-crawl-urls", 
                        help="The maximum number of URLs to crawl, default is 30.", 
                        type=int, default=30)
    parser.add_argument("-t", "--num-threads", 
                        help="The number of threads that runs extracting emails" \
                            "from individual pages. Default is 10",
                        type=int, default=10)
    parser.add_argument("--crawl-external-urls", 
                        help="Whether to crawl external URLs that the domain specified",
                        action="store_true")
    parser.add_argument("--crawl-delay", 
                        help="The crawl delay in seconds, useful for not overloading web servers",
                        type=float, default=0.01)
    # parse the command-line arguments
    args = parser.parse_args()
    url = args.url
    # set the global variable indicating whether the program is still running
    # helpful for the tracker to stop running whenever the main thread stops
    is_running = True
    # initialize the crawler and start crawling right away
    crawler = Crawler(url, max_crawl_urls=args.max_crawl_urls, delay=args.crawl_delay,
                      crawl_external_urls=args.crawl_external_urls)
    crawler.start()
    # give the crawler some time to fill the queue
    time.sleep(5)
    # start the statistics tracker, print some stats every 5 seconds
    start_stats_tracker(crawler)
    # start the email spider that reads from the crawler's URLs queue
    email_spider = EmailSpider(crawler, n_threads=args.num_threads)
    email_spider.run()
    # set the global variable so the tracker stops running
    is_running = False
