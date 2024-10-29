import json
import os
from bs4 import BeautifulSoup
import zipfile
from dictionary_construction.Entry import Dictionary_Entry

def generate_entry(entry: Dictionary_Entry, example_sentences = []) -> list:
    """
    Generates a dictionary structure for the desired JSON schema with dynamic example sentences.
    """
    # Create the list of example sentence structures dynamically
    example_sentence_list = [
        {
            "tag": "li",
            "style": {"listStyleType": f"'{chr(9311 + idx)}'"},
            "content": sentence
        }
        for idx, sentence in enumerate(example_sentences, start=1)
    ]
    
    # JSON structure based on provided schema
    data = [
        entry.subject,
        entry.reading,
        entry.term_long_name,
        entry.part_of_speech,
        0,
        [
            {
                "type": "structured-content",
                "content": [
                    "【 Meaning 】",
                    {"tag": "div", "style": {"marginLeft": 1}, "content": entry.definition},
                    "【 Explanation 】",
                    {"tag": "div", "style": {"marginLeft": 1}, "content": entry.explanation},
                    "【 Example sentences 】",
                    {
                        "tag": "ol",
                        "content": example_sentence_list,
                    },
                ],
            },
            {
                "type": "structured-content",
                "content": [
                    {
                        "tag": "a",
                        "href": entry.link,
                        "content": "Link to Bunpro",
                    }
                ]
            }
        ],
        1,
        entry.JLPT,
    ]
    return data


def zip_directory(directory_path, zip_name):
    # Create a ZipFile object
    with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Walk through all files and folders within the directory
        for root, _, files in os.walk(directory_path):
            for file in files:
                # Create the full path of the file
                full_path = os.path.join(root, file)
                # Write the file into the zip archive with a relative path
                zipf.write(full_path, os.path.relpath(full_path, directory_path))

def main():
    path_to_html_files = r"grammar_pages"
    page_list = os.listdir(path_to_html_files)
    grammar_points = []

    for page in page_list:
        with open(os.path.join(path_to_html_files, page), "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f, "html.parser", from_encoding="utf-8")

        entry = Dictionary_Entry(soup)
        entry = generate_entry(entry)
        grammar_points.append(entry)

    for i in range(4):
        with open(fr"dictionary_files\term_bank_{i+1}.json", "w", encoding="utf-8") as f:
            json.dump(grammar_points[i::4], f, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    # main()

    # Zip the dictionary files
    zip_directory("dictionary_files", "bunpro_dict.zip")