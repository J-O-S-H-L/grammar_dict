from bs4 import BeautifulSoup
import os

path_to_json = r"grammar_pages"
pages_list = os.listdir(path_to_json)


def bunpro_adj_options(page_list: list) -> set:
    adj_options = set()
    for page in page_list:
        soup = BeautifulSoup(
            open(os.path.join(path_to_json, page), "r", encoding="utf-8"), "html.parser"
        )
        title = soup.select("ul h4")
        labels = soup.select("ul > li > p")
        for t, l in zip(title, labels):
            if t.get_text(strip=True) == "Part of Speech":
                adj_options.add(l.get_text(strip=True))
    return sorted(adj_options)


bun_opt = bunpro_adj_options(pages_list)

yomi_pos = [
    "adj-na",
    "adj-na",
    "adv",
    "aux-v",
    "prt",
    "exp",
    "adj-na",
    "n",
    "prt",
    "pn",
    "v-unspec",
]
assert len(bun_opt) == len(
    yomi_pos
), "Lengths of bunpro and yomichan POS lists are not equal"
# fix_pos = {key: value for key, value in zip(bun_opt, yomi_pos)}

fix_pos = {
    "Adjective": "adj-na",
    "Adjective + Conjunctions": "adj-na",
    "Adverb": "adv",
    "Auxiliary Verb": "aux-v",
    "Conjunctive Particle": "prt",
    "Expression": "exp",
    "Fixed Adjective": "adj-na",
    "Noun": "n",
    "Particle": "prt",
    "Pronoun": "pn",
    "Verb": "v-unspec",
}
