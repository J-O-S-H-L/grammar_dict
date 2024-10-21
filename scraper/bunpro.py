import json
import requests
from bs4 import BeautifulSoup
import datetime as dt
import time
import random
import logging
import os
import os
from collections import namedtuple
import tqdm
import subprocess
from urllib.parse import quote


ResponseResult = namedtuple(
    "ResponseResult", ["action", "site", "sleep_time", "scraped"]
)


# Create a logger
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# Create a file handler for errors and warnings with UTF-8 encoding
file_handler = logging.FileHandler("scraping_errors.log", encoding="utf-8")
file_handler.setLevel(logging.WARNING)

# Create a console handler to output to the console
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)  # Log info and above to console

# Create a logging format and add it to the handlers
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Add the handlers to the logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)


def get_scrape_urls(json_path: str, n_level: str) -> list:
    """Generate a list of URLs to scrape based on grammar points."""
    try:
        with open(json_path, "r", encoding="utf-8") as file:
            data = json.load(file)
    except FileNotFoundError:
        logging.error(f"JSON file {json_path} not found.")
        return []
    except json.JSONDecodeError:
        logging.error(f"Error decoding JSON from {json_path}.")
        return []

    base_url = "https://bunpro.jp"
    grammar_points = data.get(n_level, [])
    
    scrape_sites = []
    for grammar_point in grammar_points:
        for url in grammar_point.values():
            scrape_sites.append(base_url + url)
    
    return scrape_sites


def gen_random_sleeps(min_sleep, max_total_time, n_requests):
    """Generate random sleep intervals for web scraping."""
    if n_requests * min_sleep > max_total_time:
        error_msg = (
            "Minimum sleep times number of requests exceed the maximum total time."
        )
        logging.error(error_msg)
        raise ValueError(error_msg)

    remaining_time = max_total_time - (n_requests * min_sleep)
    sleep_intervals = [min_sleep] * n_requests

    for i in range(n_requests):
        if remaining_time <= 0:
            break
        max_additional_sleep = remaining_time / (n_requests - i)
        additional_sleep = random.uniform(0, max_additional_sleep)
        sleep_intervals[i] += additional_sleep
        remaining_time -= additional_sleep

    if len(sleep_intervals) != n_requests:
        error_msg = (
            f"Error generating sleep intervals: {len(sleep_intervals)} != {n_requests}"
        )
        logging.error(error_msg)
        raise ValueError(error_msg)

    random.shuffle(sleep_intervals)
    return sleep_intervals


def calc_duration(start=None, end=None):
    """Calculate the duration between two datetime objects."""
    if start is None:
        start = dt.datetime.now()
    if end is None:
        end = start.replace(hour=23, minute=59, second=59)
    if start > end:
        error_msg = "End time must come after start time."
        logging.error(error_msg)
        raise ValueError(error_msg)
    duration = end - start
    return duration.total_seconds()


# save source code to a file
def save_source_code(soup, site):
    """Save the source code of a webpage to a file."""
    filename = site.split("/")[-1] + ".html"
    dir = os.path.dirname(os.path.abspath(__file__))  # Get the directory of the current file
    parent_dir = os.path.join(dir, os.pardir)  # Navigate to the parent directory
    grammar_pages_dir = os.path.join(parent_dir, "grammar_pages")

    # Check if 'grammar_pages' directory exists, if not, create it
    if not os.path.exists(grammar_pages_dir):
        logging.warning("Directory 'grammar_pages' does not exist. Creating it.")
        os.makedirs(grammar_pages_dir)

    # Construct the full path for the file
    filename = os.path.join(grammar_pages_dir, filename)

    # check if the file already exists
    if os.path.exists(filename):
        # if it does, add a timestamp to the filename
        timestamp = dt.datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"{filename}_{timestamp}.html"
        
    try:
        with open(filename, "w", encoding="utf-8") as file:
            file.write(soup.prettify())
    except IOError as e:
        logging.error(f"Error saving source code for {site}: {e}")





def process_response(response, site, sleep_time):
    try:
        response.raise_for_status()
        if response.status_code == 429:
            logging.error(f"Rate limit exceeded for {site}. Exiting.")
            return ResponseResult("break", site, sleep_time, False)
        
        time.sleep(sleep_time)
        soup = BeautifulSoup(response.text, "html.parser")
        save_source_code(soup, site)

        return ResponseResult("scrape", site, sleep_time, True)

    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred while scraping {site}: {http_err}")
        return ResponseResult("error", site, sleep_time, False)
    except requests.exceptions.RequestException as e:
        logging.error(f"Error scraping {site}: {e}")
        return ResponseResult("error", site, sleep_time, False)


def scrape_sites(sites, times, min_session_interval):
    sites_times = zip(sites, times)
    session = None
    skip_sites = os.listdir("../grammar_pages")
    skip_sites = [site.split(".")[0] for site in skip_sites]

    try:
        for site, sleep_time in tqdm.tqdm(sites_times, total=len(sites), desc="Scraping sites", bar_format='{l_bar}{bar} | {n_fmt}/{total_fmt} sites', leave=True):

            if site.split('/')[-1] in skip_sites:
                logging.info(f"Skipping {site} as it has already been scraped.")
                continue

            # Encode the URL properly
            encoded_site = quote(site, safe=':/?=&')

            try:
                if sleep_time < min_session_interval:
                    # Use a session for requests with short sleep times
                    if session is None:
                        session = requests.Session()
                    response = session.get(encoded_site, timeout=10)
                else:
                    # Use a direct request for longer sleep times
                    if session is not None:
                        session.close()
                        session = None
                    response = requests.get(encoded_site, timeout=10)

                result = process_response(response, site, sleep_time)
                logging.debug(f"Processed response from {site}")
                if result.action == "break":
                    break
                yield result

            except requests.exceptions.Timeout:
                logging.error(f"Timeout occurred while trying to access {site}")
                yield ResponseResult("error", site, sleep_time, False)
            except requests.exceptions.RequestException as e:
                logging.error(f"Error scraping {site}: {e}")
                yield ResponseResult("error", site, sleep_time, False)
            finally:
                if session is not None and sleep_time >= min_session_interval:
                    session.close()
                    session = None
                    logging.debug("Session closed")

    
    except KeyboardInterrupt:
        logging.info("Scraping interrupted by user.")
        if session is not None:
            session.close()
            logging.info("Session closed after interruption.")
        raise  # Re-raise the exception if needed

    # Ensure the session is closed if it was opened
    if session is not None:
        session.close()


if __name__ == '__main__':
    json_path = "grammar_points.json"
    n_level = "N1"
    sites_to_scrape_list = get_scrape_urls(json_path, n_level)
    min_sleep = 2  # seconds
    duration = calc_duration()
    n_requests = len(sites_to_scrape_list)
    sleep_times = [random.randint(min_sleep, 10) for _ in range(n_requests)]
    minimum_session_interval = 30  # seconds

    # Collect results from the generator
    results = list(scrape_sites(sites_to_scrape_list, sleep_times, minimum_session_interval))

    # Save the results list to a file
    with open('scrape_results.json', 'w', encoding='utf-8') as f:
        json.dump([result._asdict() for result in results], f, ensure_ascii=False, indent=4)
