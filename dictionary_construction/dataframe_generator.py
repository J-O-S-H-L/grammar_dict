import logging
import os
import re
import importlib.resources
from bs4 import BeautifulSoup
import pandas as pd
from dictionary_construction.const import fix_pos



# Create a logger
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# Create a file handler for errors and warnings with UTF-8 encoding
file_handler = logging.FileHandler("dataframe_errors.log", encoding="utf-8")
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

path_to_html_files = r"grammar_pages"
page_list = os.listdir(path_to_html_files)


def extract_explination(soup: BeautifulSoup) -> str:
    main_div = soup.find("div", class_="bp-ddw bp-writeup-body prose")

    try:
        for example_section in main_div.find_all(
            class_=["writeup-example--japanese", "writeup-example--english"]
        ):
            example_section.decompose()
        explination = main_div.get_text(separator=" ", strip=True)
        return explination
    except AttributeError:
        logger.warning(
            f"Could not find example sections in {soup.find('title').get_text(strip=True)}"
        )
        return "Error: Could not extract explanation"

    # Extract the remaining text


def determine_pos(soup: BeautifulSoup) -> str:
    title = soup.select("ul h4")
    labels = soup.select("ul > li > p")
    for t, l in zip(title, labels):
        if t.get_text(strip=True) == "Part of Speech":
            result = l.get_text(strip=True)
            result = fix_pos.get(result)
            if result:
                return result
            else:
                raise ValueError(f"Unknown POS: {result}")
    return ""


def remove_latin_chars(text):
    # Regular expression to match Latin characters (a-z, A-Z)
    return re.sub(r"[a-zA-Z,]", "", text)


def JLPT_level(soup: BeautifulSoup) -> str:
    title = soup.find("title").get_text(strip=True)
    # Extract the JLPT level from the title
    jlpt = title.split("JLPT")[1].strip(") | Bunpro")
    if jlpt not in ["N5", "N4", "N3", "N2", "N1", "N0"]:
        raise ValueError(f"Unknown JLPT level: {jlpt}")
    return jlpt


def split_and_duplicate_rows(row):
    # Split the 'subject' column by the '・' character
    splits = row["subject"].split("・")
    # Duplicate the row for each split
    return pd.DataFrame(
        {
            "subject": splits,
            "reading": [row["reading"]] * len(splits),
            "part_of_speech": [row["part_of_speech"]] * len(splits),
            "definition": [row["definition"]] * len(splits),
            "explanation": [row["explanation"]] * len(splits),
            "link": [row["link"]] * len(splits),
            "JLPT": [row["JLPT"]] * len(splits),
        }
    )


def main():
    df = pd.DataFrame(
        columns=[
            "subject",
            "reading",
            "part_of_speech",
            "definition",
            "explanation",
            "link"
            "JLPT",
        ]
    )
    for page in page_list:
        with open(os.path.join(path_to_html_files, page), "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f, "html.parser", from_encoding="utf-8")

        entry_contents = {
            "subject": remove_latin_chars(
                soup.find("h1").get_text(strip=True).split(" ")[0]
            ),
            "reading": soup.find("title").get_text(strip=True).split(" ")[0],
            "part_of_speech": determine_pos(soup),
            "definition": soup.select_one("p.line-clamp-1").get_text(strip=True),
            "explanation": extract_explination(soup),
            "link": soup.select_one('head > link[rel="canonical"]')['href'],
            "JLPT": JLPT_level(soup),
        }
        if entry_contents["subject"] == "" or entry_contents["definition"] == "()":
            logger.warning(
                f"Skipping {page} with grammar point {soup.find("title").get_text(strip=True).split(' ')[0]} as it has no subject or definition."
            )
            continue
        df = pd.concat([df, pd.DataFrame(entry_contents, index=[0])], ignore_index=True)

    expanded_df = pd.concat(
        df.apply(split_and_duplicate_rows, axis=1).tolist(), ignore_index=True
    )
    expanded_df.to_csv("bunpro_entries.csv", index=False)


if __name__ == "__main__":
    main()
