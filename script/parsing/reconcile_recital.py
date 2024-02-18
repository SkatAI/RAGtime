'''
Recital for
- commission
- council
- final four
- ep adopted
- coreper
'''

# usual libs
import os, re, json, glob
import time, datetime
from datetime import timedelta
import pandas as pd
import argparse
from tqdm import tqdm
pd.options.display.max_columns = 30
pd.options.display.max_rows = 60
pd.options.display.max_colwidth = 80
pd.options.display.precision = 4
pd.options.display.width = 0
pd.set_option("display.float_format", "{:.2f}".format)
import numpy as np
import typing as t
from regex_utils import Rgx
from lines import Line, RecitalLine, RegulationLine

# build path

def format_recital(author: str,lines: t.List[Line]) -> pd.DataFrame :
    if author in ['commission', 'council', 'coreper']:
        # extract the recital number from the text
        df = pd.DataFrame()
        df['text'] = [line.text for line in lines]
        df['title'] = [f"Recital {line.number_in_parenthesis}" for line in lines]
        df['number'] =  [Rgx.format_number(line.number_in_parenthesis) for line in lines]
        df['author'] = author
        df['amendment'] = ''

    elif author == 'final_four':
        data = []
        item = {}
        for line in lines:
            if line.starts_with("Recital"):
                item.update({
                    'title': line.text,
                    'number': Rgx.format_number(line.first_number_from_title)
                })
            elif (line.starts_with('parliament')):
                item.update({
                    'text': re.sub( r"^parliament:", '', line.text).strip()
                })
                data.append(item)
                item = {}
        df = pd.DataFrame(data)
        df['author'] = 'ff_parliament'
        df['amendment'] = ''
        df = df[df.text != ''].copy()
        df.reset_index(inplace = True, drop = True)
    elif author == 'ep_adopted':
        data = []
        item = {}
        for line in lines:
            if line.starts_with("Amendment"):
                item.update({
                    'amendment': line.text,
                })
            elif line.starts_with("Recital"):
                item.update({
                    'title': line.text,
                    'number': Rgx.format_number(line.extract_first_number_from_title())
                })
            elif line.has_text():
                item.update({
                    'text': line.text
                })
                data.append(item)
                item = {}
        df = pd.DataFrame(data)
        df['author'] = author

    return df

class Document(object):
    recital_files = {
        'commission':'./data/txt/52021-PC0206-commission/52021PC0206-recitals.txt',
        'council':'./data/txt/ST-15698-2022-council/ST-15698-recital.txt',
        'final_four':'./data/txt/final_four/AIAct-final-four-simple-recitals.txt',
        'ep_adopted':'./data/txt/adopted-amendments/EP-amendments-parliament-recital.txt',
        'coreper':'./data/txt/coreper-feb2/AIA-Trilogue-Coreper20240202-recitals.txt',
    }


    def __init__(self, author, filename) -> None:
        self.author = author
        self.filename = filename

    def load_texts(self) -> None:
        with open(self.filename, 'r') as f:
            self.texts = [txt for txt in f.read().split('\n') if len(txt) >0]

    def format(self) -> None:
        pass



if __name__ == "__main__":


    # recitals
    data = pd.DataFrame()
    for author in ['commission','council','final_four','ep_adopted','coreper']:
        file = Document.recital_files[author]
        with open(file, 'r') as f:
            texts = [txt for txt in f.read().split('\n')]

        lines = [RecitalLine(txt) for txt in texts  if len(txt) >0]

        data = pd.concat([data, format_recital(author,lines)])

    author_order_list = ['commission','council','ep_adopted','final_four','coreper']
    data["author"] = data["author"].astype("category")
    data["author"] = data["author"].cat.set_categories(author_order_list, ordered=True)



    data.sort_values(by = ['number','author'], inplace = True)
    data.reset_index(inplace = True, drop = True)

    print("Recitals",data.shape)

    # export to rag data
    data = data[data.author.isin(['commission', 'council', 'coreper'])].copy()
    data.reset_index(inplace=True, drop = True)

    output_file_json = "./data/rag/recital-20240218.json"
    with open(output_file_json, "w", encoding="utf-8") as f:
        data.to_json(f, force_ascii=False, orient="records", indent=4)
