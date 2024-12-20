import json
import pandas as pd
import numpy as np


def compose_entry(
    subject, reading, term_long_name, part_of_speech, definition, explanation, link, matchup=10, JLPT="N5"
) -> str:
    if part_of_speech is np.nan:
        part_of_speech = ""
    data = [
        subject,  # Kanji
        reading,  # Kana
        term_long_name,  # Part of speech 1
        part_of_speech,  # Part of speech 2
        matchup,
        [
            {
                "type": "structured-content",
                "content": [
                    "【 Meaning 】",
                    {"tag": "div", "style": {"marginLeft": 1}, "content": definition},
                    "【 Explination 】",
                    {"tag": "div", "style": {"marginLeft": 1}, "content": explanation},
                    "【 Example sentences 】",
                    {
                        "tag": "ol",
                        "content": [
                            {
                                "tag": "li",
                                "style": {"listStyleType": "'①'"},
                                "content": "例文 1\nSentence 1",
                            },
                            {
                                "tag": "li",
                                "style": {"listStyleType": "'②'"},
                                "content": "Sentence 2",
                            },
                        ],
                    },
                ],
            },
            {
                "type": "structured-content",
                "content": [
                    {
                        "tag": "a",
                        "href": link,
                        "content": "Link to Bunpro",
                    }
                ]
            }
        ],
        1,  # Some boolean flag
        JLPT,  # JLPT Level
    ]
    return data


def main():
    df = pd.read_csv(r"dictionary_construction\bunpro_entries.csv")
    result = df.apply(
        lambda row: compose_entry(**row), axis=1
    ).tolist()  # Convert to a list
    # break the list up into 4 files
    for i in range(4):
        with open(fr"dictionary_files\term_bank_{i+1}.json", "w", encoding="utf-8") as f:
            json.dump(result[i::4], f, indent=4, ensure_ascii=False)


if __name__ == "__main__":
    main()
