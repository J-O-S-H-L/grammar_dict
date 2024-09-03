import json
import requests
from bs4 import BeautifulSoup
import datetime as dt
import time
import random
import logging
import os
from collections import namedtuple
import tqdm
import subprocess


ResponseResult = namedtuple(
    "ResponseResult", ["action", "site", "sleep_time", "scraped"]
)

# Create a logger
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# Create a file handler for errors and warnings
file_handler = logging.FileHandler("scraping_errors.log")
file_handler.setLevel(logging.WARNING)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)  # Log info and above to console

# Create a logging format and add it to the handlers
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Add the handlers to the logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# NordVPN connection
def nord_connect():
    nordvpn_path = r"C:\Program Files\NordVPN\NordVPN.exe"
    command = f'& "{nordvpn_path}" -c'

    try:
        result = subprocess.run(
            ["powershell", "-Command", command],
            capture_output=True,
            text=True,
            check=True  # Raises CalledProcessError if command fails
        )
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"An error occurred: {e.stderr}")


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

    base_url = "https://bunpro.jp/grammar_points/"
    grammar_points = data.get(n_level, [])
    scrape_sites = [base_url + gp for gp in grammar_points]
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
    dir = os.path.pardir(os.path.abspath(__file__))
    if not os.path.exists(os.path.join(dir, "grammar_pages")):
        logging.warning("Directory 'grammar_pages' does not exist. Creating it.")
        os.makedirs(os.path.join(dir, "grammar_pages"))
    filename = os.path.join(dir, "grammar_pages", filename)
    try:
        with open(filename, "w", encoding="utf-8") as file:
            file.write(soup.prettify())
    except IOError as e:
        logging.error(f"Error saving source code for {site}: {e}")

    logging.info(f"Saved source code for {site} to {filename}")



def process_response(response, site, sleep_time):
    try:
        response.raise_for_status()
        if response.status_code == 429:
            logging.error(f"Rate limit exceeded for {site}. Exiting.")
            return ResponseResult("break", site, sleep_time, False)
        soup = BeautifulSoup(response.text, "html.parser")
        save_source_code(soup, site)
        logging.info(f"Scraped {site}")
        return ResponseResult("scrape", site, sleep_time, True)

    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred while scraping {site}: {http_err}")
        return ResponseResult("error", site, sleep_time, False)
    except requests.exceptions.RequestException as e:
        logging.error(f"Error scraping {site}: {e}")
        return ResponseResult("error", site, sleep_time, False)


def scrape_sites(sites, times, min_session_interval):
    connect_to_nord = random.randint(0, 19)
    sites_times = zip(sites, times)
    session = None
    for site, sleep_time in tqdm.tqdm(sites_times, total=len(sites), leave=True):
        time.sleep(sleep_time)
        dice_roll = random.randint(0,19)
        if connect_to_nord == dice_roll:
            nord_connect()
    #     try:
    #         if sleep_time < min_session_interval:
    #             # Use a session for requests with short sleep times
    #             if session is None:
    #                 session = requests.Session()
    #             response = session.get(site, timeout=10)
    #         else:
    #             # Use a direct request for longer sleep times
    #             if session is not None:
    #                 session.close()
    #                 session = None
    #             response = requests.get(site, timeout=10)

    #         result = process_response(response, site, sleep_time)
    #         if result.action == "break":
    #             break
    #         yield result

    #     except requests.exceptions.Timeout:
    #         logging.error(f"Timeout occurred while trying to access {site}")
    #         yield ResponseResult("error", site, sleep_time, False)
    #     except requests.exceptions.RequestException as e:
    #         logging.error(f"Error scraping {site}: {e}")
    #         yield ResponseResult("error", site, sleep_time, False)
    #     finally:
    #         if session is not None and sleep_time >= min_session_interval:
    #             session.close()
    #             session = None

    #     # Sleep for the designated time
    #     time.sleep(sleep_time)

    # Ensure the session is closed if it was opened
    if session is not None:
        print("closing session")
        session.close()

if __name__ == '__main__':

    json_path = "grammar_points.json"
    n_level = "N5"
    sites_to_scrape_list = get_scrape_urls(json_path, n_level)
    min_sleep = 2 # seconds
    duration =  calc_duration()
    n_requests = len(sites_to_scrape_list)
    sleep_times = gen_random_sleeps(min_sleep, duration, n_requests)
    minimum_session_interval = 5*60

    scrape_sites(sites_to_scrape_list, sleep_times, minimum_session_interval)
