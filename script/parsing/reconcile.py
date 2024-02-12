'''
Create unique dataframe that includes all text versions from
- commission
- council
- final four
- ep adopted
- coreper
start with recital
'''

# usual libs
import os, re, json, glob
import time, datetime
from datetime import timedelta
import pandas as pd
import argparse
from tqdm import tqdm
pd.options.display.max_columns = 120
pd.options.display.max_rows = 60
pd.options.display.max_colwidth = 120
pd.options.display.precision = 10
pd.options.display.width = 240
pd.set_option("display.float_format", "{:.2f}".format)
import numpy as np
import typing as t


recital_files = {
    'commission':'./data/txt/52021-PC0206-commission/52021PC0206-recitals.txt',
    'council':'./data/txt/ST-15698-2022-council/ST-15698-recital.txt',
    'final_four':'./data/txt/final_four/AIAct-final-four-simple.txt',
    'ep-adopted':'./data/txt/adopted-amendments/EP-amendments-parliament-recital.txt',
    'coreper':'./data/txt/coreper-feb2/AIA-Trilogue-Coreper20240202-recitals.txt',
}

def extract_number(txt: str) -> str:
    # given "(2) hello" return "2"
    rgx = r"\(([-]*\s*\d+\s*[a-z]*)\).*$"
    match = re.match(rgx, txt)
    if match:
        return match.group(1).strip()
    else:
        return None

assert extract_number("(1) hello")  == "1"
assert extract_number("(1a) hello")  == "1a"
assert extract_number("(1 ) hello")  == "1"
assert extract_number("(12) hello")  == "12"
assert extract_number(" hello")  is None


def format_simple(author: str,txt: t.List) -> pd.DataFrame :
    # extract the recital number from the text
    df = pd.DataFrame()
    df['text'] = txt
    df['author'] = author
    df['title'] = df.text.apply(lambda txt : f"Recital {extract_number(txt)}")
    df['order'] = df.text.apply(lambda txt : extract_number(txt))
    return df

if __name__ == "__main__":

    # for author, file in recital_files.items():
    #     with open(file, 'r') as f:
    #         texts = [txt for txt in f.read().split('\n') if len(txt) >0]
    #     print()
    #     print(author)
    #     print(text[s0])

    df = pd.DataFrame()
    for author in ['commission','council']:
        file = recital_files[author]
        with open(file, 'r') as f:
            texts = [txt for txt in f.read().split('\n') if len(txt) >0]

        df = pd.concat([df, format_simple(author,texts)])
    df.sort_values(by = ['order','author'], inplace = True)

    print(df.head(40).tail(10))

    print(df[df.order.isna()].shape)