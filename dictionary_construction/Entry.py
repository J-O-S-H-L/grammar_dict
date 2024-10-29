import json
import pandas as pd
import numpy as np
import re
from bs4 import BeautifulSoup
from dictionary_construction.const import FIX_POS

class Dictionary_Entry:
    def __init__(self, BS4_soup: BeautifulSoup):
        self.soup = BS4_soup
        self.subject = self.extract_subject()
        self.reading = ''
        self.term_long_name = self.soup.find("title").get_text(strip=True).split(" ")[0]
        self.part_of_speech = self.extract_pos()
        self.definition = self.soup.select_one("p.line-clamp-1").get_text(strip=True)
        self.explanation = self.extract_explanation()
        self.jp_example_sentance = self.extract_jp_example()
        self.link = self.soup.select_one('head > link[rel="canonical"]')['href']
        self.matchup = 10
        self.JLPT = self.extract_jlpt_level()

    def extract_subject(self):
        result = self.soup.find("h1").get_text(strip=True).split(" ")[0]
        return re.sub(r"[a-zA-Z,]", "", result)

    def extract_pos(self):
        title = self.soup.select("ul h4")
        labels = self.soup.select("ul > li > p")
        for t, l in zip(title, labels):
            if t.get_text(strip=True) == "Part of Speech":
                result = l.get_text(strip=True)
                result = FIX_POS.get(result)
                if result:
                    return result
                else:
                    raise ValueError(f"Unknown POS: {result}")
        return ""

    def extract_explanation(self) -> str:
        main_div = self.soup.find("div", class_="bp-ddw bp-writeup-body prose")

        try:
            for example_section in main_div.find_all(
                class_=["writeup-example--japanese", "writeup-example--english"]
            ):
                example_section.decompose()
            explination = main_div.get_text(separator=" ", strip=True)
            return explination
        except AttributeError:
            print(
                f"Could not find example sections in {self.soup.find('title').get_text(strip=True)}"
            )
            return "Error: Could not extract explanation"
        
    def extract_jp_example(self) -> list:
        examples = self.soup.select

    def extract_jlpt_level(self) -> str:
        title = self.soup.find("title").get_text(strip=True)
        # Extract the JLPT level from the title
        jlpt = title.split("JLPT")[1].strip(") | Bunpro")
        if jlpt not in ["N5", "N4", "N3", "N2", "N1", "N0"]:
            raise ValueError(f"Unknown JLPT level: {jlpt}")
        return jlpt
    
