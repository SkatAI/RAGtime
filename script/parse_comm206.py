'''
Parsing the sections of the COM(2021)-206 document into a json structured file

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
The file is already quite clean. exception, title numbering is glued to title text: 1.2.3.This is the title
- add markup for titles with the regex (\d+\.)([A-Z]) => # $1 $2 ... (\d+\.\d+\.\d+\.)([A-Z]) => ### $1 $2
-

'''

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
    text = re.sub(r'(\d+\.\d+\.\d+\.)([A-Z])', r'\1 \2', text)
    text = re.sub(r'(\d+\.\d+\.)([A-Z])', r'\1 \2', text)
    text = re.sub(r'(\d+\.)([A-Z])', r'\1 \2', text)
    return text

def is_bullet(text):
    rgx = r'^- .*'
    return re.match(rgx, text) is not None

def is_title(text):
    rgx = r'(\d+\.) ([A-Z])|(\d+\.\d+\.) ([A-Z])|(\d+\.\d+\.\d+\.) ([A-Z])'
    return re.match(rgx, text) is not None

def title_h1(text):
    rgx = r'(\d+\.) ([A-Z])'
    return re.match(rgx, text) is not None

def title_level(text):
    rgxs = [r'^(\d+\.) ([A-Z])',r'^(\d+\.\d+\.) ([A-Z])',r'^(\d+\.\d+\.\d+\.) ([A-Z])']
    for rgx in rgxs:
        if re.match(rgx, text) is not None:
            return rgxs.index(rgx)


if __name__ == "__main__":

    if True:
        filename = "./data/txt/52021-PC0206/52021PC0206-COM(2021)-206-final-01-01-explanatory-memorandum.txt"
        output_file_json = "./data/json/52021PC0206-explanatory-memorandum.json"
        base_ = {
            "document_uuid": "3ee2bbd9-defb-47d0-b065-a8a40f1e5369",
            "document_section": "explanatory memorandum",
            "document_section_number": 1,
            "type": "context",
        }
        counter_ = 1
        current_title = []
    else:
        filename = "./data/txt/52021-PC0206/52021PC0206-COM(2021)-206-final-01-02-recitals.txt"
        output_file_json = "./data/json/52021PC0206-recitals.json"
        base_ = {
            "document_uuid": "3ee2bbd9-defb-47d0-b065-a8a40f1e5369",
            "document_section": "recitals",
            "document_section_number": 2,
            "type": "recitals",
        }
        counter_ = 0
        current_title = ['']

    with open(filename, "r") as file:
        texts = file.readlines()

    texts = [title_space(txt.strip()) for txt in texts  if len(txt.strip()) > 0]


    ''' Rules
    - append + : current title to text with / without numbering
    - add paragraph numbering
    - [not implemented] items that starts with - (bullet points) are concatenated with previous item
    '''

    path_sep = ' >> '
    document = []
    for text in texts:
        candidate = base_.copy()
        if is_title(text):
            level = title_level(text)
            print("=====", level, text)
            if title_h1(text):
                current_title = [text]
                level = 0
            else:
                current_title = current_title[:level]
                current_title.append(text)
            print(level, current_title)
        else:
            counter_ += 1

        candidate.update({
            "id": str(counter_),
            "uuid": str(uuid.uuid4()),
            "path": path_sep.join(current_title),
            "header": is_title(text),
            "text": text,
        })
        document.append(candidate)

    document = pd.DataFrame(document)


    print("saving to json")
    with open(output_file_json, "w", encoding="utf-8") as f:
        document.to_json(f, force_ascii=False, orient="records", indent=4)




