import json
from bs4 import BeautifulSoup
import os
import re
import pandas as pd
from const import fix_pos

path_to_html_files = r"grammar_pages"
page_list = os.listdir(path_to_html_files)

def extract_explination(soup: BeautifulSoup) -> str:
    main_div = soup.find('div', class_='bp-ddw bp-writeup-body prose')

    # Remove example sentence sections by specifying the classes you want to skip
    for example_section in main_div.find_all(class_=['writeup-example--japanese', 'writeup-example--english']):
        example_section.decompose()  # This removes the element from the tree

    # Extract the remaining text
    explination = main_div.get_text(separator=' ', strip=True)
    return explination

def determine_pos(soup: BeautifulSoup) -> str:
    title = soup.select('ul h4')
    labels = soup.select('ul > li > p')
    for t, l in zip(title, labels):
        if t.get_text(strip=True) == "Part of Speech":
            result = l.get_text(strip=True)
            result = fix_pos.get(result)
            if result:
                return result
            else:
                raise ValueError(f"Unknown POS: {result}")
    return "Unknown"

def remove_latin_chars(text):
    # Regular expression to match Latin characters (a-z, A-Z)
    return re.sub(r'[a-zA-Z,]', '', text)

def JLPT_level(soup: BeautifulSoup) -> str:
    title = soup.find('title').get_text(strip=True)
    # Extract the JLPT level from the title
    jlpt = title.split('JLPT')[1].strip(') | Bunpro')
    if jlpt not in ['N5', 'N4', 'N3', 'N2', 'N1', 'N0']:
        raise ValueError(f"Unknown JLPT level: {jlpt}")
    return jlpt

def split_and_duplicate_rows(row):
    # Split the 'subject' column by the '・' character
    splits = row['subject'].split('・')
    # Duplicate the row for each split
    return pd.DataFrame({
        'subject': splits,
        'part_of_speech': [row['part_of_speech']] * len(splits),
        'definition': [row['definition']] * len(splits),
        'explanation': [row['explanation']] * len(splits),
        'JLPT': [row['JLPT']] * len(splits),
    })

def main():
    df = pd.DataFrame(columns=["subject", "part_of_speech", "definition", "explanation", "JLPT"])
    for page in page_list:
        soup = BeautifulSoup(open(os.path.join(path_to_html_files, page), 'r', encoding='utf-8'), 'html.parser')
        entry_contents = {
            "subject": remove_latin_chars(soup.find('h1').get_text(strip=True).split(' ')[0]),
            "part_of_speech": determine_pos(soup),
            "definition": soup.select_one('p.line-clamp-1').get_text(strip=True),
            "explanation": extract_explination(soup),
            "JLPT": JLPT_level(soup)
            
        }
        df = pd.concat([df, pd.DataFrame(entry_contents, index=[0])], ignore_index=True)

    expanded_df = pd.concat(df.apply(split_and_duplicate_rows, axis=1).tolist(), ignore_index=True)
    expanded_df.to_csv("bunpro_entries.csv", index=False)

if __name__ == "__main__":
    main()