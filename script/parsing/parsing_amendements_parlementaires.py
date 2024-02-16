import os, re, json, glob
import time, datetime
from datetime import timedelta
import pandas as pd
import argparse
from tqdm import tqdm
pd.options.display.max_columns = 120
pd.options.display.max_rows = 60
pd.options.display.precision = 10
pd.options.display.max_colwidth = 100
pd.options.display.width = 200
pd.set_option("display.float_format", "{:.2f}".format)
import numpy as np
import typing as t

from regex_utils import Rgx
from lines import Line, RecitalLine, RegulationLine

if __name__ == "__main__":
    political_groups = {
        "European Conservatives and Reformists Group": "ECR",
        "Group of the European Peoples Party (Christian Democrats)": "EPP",
        "Group of the Greens/European Free Alliance": "Greens/EFA",
        "The Left group in the European Parliament - GUE/NGL": "GUE/NGL",
        "Identity and Democracy Group": "ID",
        "Renew Europe Group": "Renew",
        "Group of the Progressive Alliance of Socialists and Democrats in the European Parliament": "S&D",
    }

    am = pd.read_csv("./data/amendements_parlementaires.csv")
    am.fillna('', inplace = True)

    # flatten am
    lines = []
    # TODO: when writing txt file, modify d.amendment to match line identification
    for i, d in am.iterrows():
        lines.append(f"Amendment {d.number}")
        lines.append(f"{political_groups[d.group]} - {d.group}")
        lines.append(d.proposers)
        lines.append(d.title)
        lines.append(d.amendment)
        lines.append('')

    lines = [text.replace('–','-') for text in lines]
    lines = [text + "\n" for text in lines]

    output_file = './data/txt/amendments/amendments_3k.txt'
    with open(output_file, 'w') as f:
        for line in lines:
            f.write(line)

    '''
    - from data, match all the loc with at least one src title
    '''


    # # find titles that are in ep_amendement loc
    # titles = []
    # # am[am.title.str.contains("Article 1 – paragraph")]
    # for i, d in am.iterrows():
    #     sub = data[data['loc'] == d.title.strip()]
    #     if sub.shape[0] > 1:
    #         print(f"-- {len(sub)}: {d.title}")
    #         titles.append(d.title)

    # root = "Article 1 "
    # src = am[am.title.str.contains(root)].copy()
    # src_titles = src.title.unique()

    # tgt = data[data['loc'].str.contains(root)].copy()
    # tgt_titles = tgt['loc'].unique()
