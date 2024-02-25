"""
Parsing the regulation section of the COM(2021)-206 document into a json structured file

item:
  - id:
  - uuid:
  - document_uuid:
  - prec_loc: navigation scheme for ordering
  # the document from which it is extracted
  - document_section: parent document section
  - type: # context, recital, article, amendment, ...
  # breadcrumbs
  - path: # location: article 2, section 1, paragraph a ... title IV paragraph 2, ...
  - numbering: 1.2. (a), III, ...
  # text
  - text: the content

# prep work
we have the following hierarchy
TITLE XX
<Title ALL CAPS>
Chapter XX
<Title of chapter ALL CAPS>
Article XX
<Title of article>
<number.> <text>
with <text> including

(a) <more text>
and
(i) <more text>

"""

import os, re, json, glob, csv
import time, datetime
from datetime import timedelta
import pandas as pd
import argparse
from tqdm import tqdm

pd.options.display.max_columns = 100
pd.options.display.max_rows = 60
pd.options.display.max_colwidth = 160
pd.options.display.precision = 10
pd.options.display.width = 160
pd.set_option("display.float_format", "{:.4f}".format)
import numpy as np
import uuid


def title_space(text):
    text = re.sub(r"(\d+\.\d+\.\d+\.)([A-Z])", r"\1 \2", text)
    text = re.sub(r"(\d+\.\d+\.)([A-Z])", r"\1 \2", text)
    text = re.sub(r"(\d+\.)([A-Z])", r"\1 \2", text)
    return text


def is_bullet(text):
    rgx = r"^- .*"
    # rgx = r'^\* '
    return re.match(rgx, text) is not None


def is_title(text):
    rgx = r"^TITLE|^Chapter|^Article|^Section"
    # rgx = r'^TITLE|^Article|^Section'
    return re.match(rgx, text) is not None


def title_h1(text):
    rgx = r"^TITLE"
    return re.match(rgx, text) is not None


def is_valid(txt):
    # remove non essential lines
    flag = True
    flag = flag & (len(txt.strip()) > 0)
    # flag = flag & (txt != '__________')
    flag = flag & (re.match(r"^__________", txt) is None)
    flag = flag & (re.match(r"^\* ", txt) is None)

    return flag


def aggregate_title(rgx, texts):
    """merges the title line with the following line
    ex:
    Article 1
    Scope
    becomes
    Article 1: Scope
    """
    outtext = []
    skip = False
    for i in range(len(texts)):
        if skip:
            skip = False
        else:
            if re.match(rgx, texts[i]) is not None:
                outtext.append(f"{texts[i]}: {texts[i+1]}")
                skip = True
            else:
                outtext.append(texts[i])

    return outtext


def aggregate_bullets(rgx, texts):
    """
    lines starting with - belong to the preceeding line
    """
    outtext = []
    skip = False
    for i in range(len(texts)):
        if skip:
            skip = False
        elif i < len(texts) - 1:
            if (re.match(rgx, texts[i]) is not None) & (re.match(rgx, texts[i + 1]) is not None):
                outtext.append(f"{texts[i]} {texts[i+1]}")
                skip = True
            else:
                outtext.append(texts[i])
        else:
            outtext.append(texts[i])

    return outtext


def consecutive(rgx, texts):
    # detect if there are 2 consecutive lines matching regex
    for i in range(len(texts) - 1):
        if (re.match(rgx, texts[i]) is not None) & (re.match(rgx, texts[i + 1]) is not None):
            return True
    return False


def aggregate_text_bullet(rgx, texts):
    """
    (line, bullet line) => "{line} {bullet line}"
    """
    outtext = []
    skip = False
    for i in range(len(texts)):
        if skip:
            skip = False
        elif i < len(texts) - 1:
            if (re.match(rgx, texts[i]) is None) & (re.match(rgx, texts[i + 1]) is not None):
                outtext.append(f"{texts[i]} {texts[i+1]}")
                skip = True
            else:
                outtext.append(texts[i])
        else:
            outtext.append(texts[i])

    return outtext


def add_sections(rgx=r"^\d+\. ", texts=[]):
    # splits '2. some text' into 2 lines 'Section 2.', 'some text'
    outtext = []
    for i in range(len(texts)):
        if re.match(rgx, texts[i]) is not None:
            numbering = texts[i].split(" ")[0].strip()
            # remove last '.'
            if numbering[-1] == ".":
                numbering = numbering[:-1]
            outtext.append(f"Section {numbering}")
            text = re.sub(rgx, "", texts[i])
            outtext.append(text)
        else:
            outtext.append(texts[i])
    return outtext


if __name__ == "__main__":
    # Edited from 52021PC0206-COM(2021)-206-final-01-03-regulation.txt to simplify parsing
    filename = "./data/txt/52021-PC0206/52021PC0206-COM(2021)-206-final-01-03-regulation-01.txt"
    output_file_json = "./data/json/52021-PC0206-regulation.json"

    counter_ = 1
    with open(filename, "r") as file:
        texts = file.readlines()

    texts = [title_space(txt.strip()) for txt in texts if is_valid(txt)]

    # for regulations, the article title is split over two lines => merge

    rgx = r"^TITLE "
    texts = aggregate_title(rgx, texts)

    rgx = r"^Chapter \d+"
    texts = aggregate_title(rgx, texts)

    rgx = r"^Article \d+"
    texts = aggregate_title(rgx, texts)

    rgx = r"^\([a-zA-Z]+\) .*"
    while consecutive(rgx, texts):
        print(len(texts))
        texts = aggregate_bullets(rgx, texts)

    texts = aggregate_text_bullet(rgx, texts)

    rgx = r"^\d+\. "
    texts = add_sections(rgx, texts)

    # assert 1 == 2

    """ Rules
    - append + : current title to text with / without numbering
    - add paragraph numbering
    - items that starts with - (bullet points) are concatenated with previous item
    """
    base_ = {
        "document_uuid": "3ee2bbd9-defb-47d0-b065-a8a40f1e5369",
        "document_section": "Regulation",
        "document_section_number": 3,
        "type": "articles",
    }

    def title_level(text):
        rgxs = [r"^TITLE", r"^Chapter", r"^Article", r"^Section"]
        # rgxs = [r'^TITLE',r'^Article',r'^Section']
        for rgx in rgxs:
            if re.match(rgx, text) is not None:
                return rgxs.index(rgx)

    path_sep = " >> "
    current_title = []
    document = []
    level = 1
    k = 0
    for text in texts:
        candidate = base_.copy()
        if is_title(text):
            if title_h1(text):
                current_title = [text]
                level = 0
                # print('h1', text)
            else:
                # print("\n======", k, text)
                new_level = title_level(text)
                keep = new_level
                # if article but not preceeded by chapter => new_level = 1
                # print(f"\t {len(current_title)> 1} \t l:{level} \t nl:{new_level} \t p:{path_sep.join(current_title)}")
                if (new_level == 2) & (len(current_title) > 1):
                    # print('-', title_level(current_title[1]), current_title[1], title_level(current_title[1]) == 2 )
                    if title_level(current_title[1]) == 2:
                        level = 2
                        keep = 1
                        # print('\tmodified keep',keep, 'level', level)
                if (new_level == 3) & (len(current_title) > 2):
                    # print('-', title_level(current_title[1]), current_title[1], title_level(current_title[1]) == 2 )
                    if title_level(current_title[2]) == 3:
                        level = 3
                        keep = 2
                        # print('\tmodified keep',keep, 'level', level)
                # print('keep',keep)

                if new_level <= level:
                    current_title = current_title[:keep]
                    level = new_level
                else:
                    level += 1
                current_title.append(text)
                # print(f" l:{level} \t nl:{new_level} \t p:{path_sep.join(current_title)}")
        else:
            counter_ += 1
        candidate.update(
            {
                "id": str(counter_),
                "uuid": str(uuid.uuid4()),
                "path": path_sep.join(current_title),
                "header": is_title(text),
                "text": text,
            }
        )
        k += 1
        document.append(candidate)

    document = pd.DataFrame(document)
    print("saving to json")
    with open(output_file_json, "w", encoding="utf-8") as f:
        document.to_json(f, force_ascii=False, orient="records", indent=4)
