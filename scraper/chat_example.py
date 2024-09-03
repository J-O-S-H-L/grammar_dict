import requests
from bs4 import BeautifulSoup

# Initialize a session and user agent
session = requests.Session()

# The URL to scrape
url = "https://bunpro.jp/grammar_points/だ"

try:
    response = session.get(url)
    response.raise_for_status()  # Check for HTTP errors

    # Parse the HTML content with BeautifulSoup
    soup = BeautifulSoup(response.text, "html.parser")

    # Save the HTML content to a file
    with open("scraped_da.html", "w", encoding="utf-8") as file:
        file.write(soup.prettify())  # Save the formatted HTML

    print(f"Successfully scraped and saved content from {url}")


except requests.exceptions.RequestException as e:
    print(f"Error scraping {url}: {e}")
