'''
Id sources titles for each tgt title
'''
import os, re, json, glob
import pandas as pd
import numpy as np
import typing as t
from regex_utils import Rgx
from lines import Line, RecitalLine, RegulationLine

def fix_space_point(text):
    # point c a => point ca | point 1 a => point 1a
    rgx = r"^(.*)point (\d+|[a-z]{1,2}) ([a-z]{1,2})(.*)$"
    m = re.match(rgx, text)
    if m:
        text = f"{m.group(1)}point {m.group(2)}{m.group(3)}{m.group(4)}"
    return text

def fix_space_article(text):
    # Article 2 a => Article 2a
    rgx = r"^Article (\d+) ([a-z]{1,2})(.*)$"
    m = re.match(rgx, text)
    if m:
        text = f"Article {m.group(1)}{m.group(2)}{m.group(3)}"
    return text

def fix_space_paragraph(text):
    # paragraph 1 a => paragraph 1a'
    rgx = r"^(.*)paragraph (\d+) ([a-z]{1,3})(.*)$"
    m = re.match(rgx, text)
    if m:
        text = f"{m.group(1)}paragraph {m.group(2)}{m.group(3)}{m.group(4)}"
    return text

def view_titles(df, start = 0, step = 10):
    cond = df.title.str.contains('Article ')
    titles = df[cond].title.unique()
    for tit in titles[start:start + step]:
        print(tit)

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

    # save csv file as json with some cleaning already done
    if True:
        am = pd.read_csv("./data/amendements_parlementaires.csv")
        am.fillna('', inplace = True)
        am['gpe'] = am.group.apply(lambda txt : political_groups[txt])
        am.rename(columns = {'amendment': 'text'}, inplace = True)
        am['amendment'] = am.number.apply(lambda n : f"Amendment {n}")
        am['title'] = am.title.apply(lambda txt: txt.replace('–','-'))
        am['title'] = am.title.apply(lambda txt: txt.replace('premier','1'))
        am['title'] = am.title.apply(lambda txt: fix_space_point(txt))
        am['title'] = am.title.apply(lambda txt: fix_space_paragraph(txt))
        am['title'] = am.title.apply(lambda txt: fix_space_article(txt))

        output_file_json = "./data/json/3k_regulation.json"
        with open(output_file_json, "w", encoding="utf-8") as f:
            am.to_json(f, force_ascii=False, orient="records", indent=4)

    am_file = "./data/json/3k_regulation.json"
    am = pd.read_json(am_file)
    am = am[am.title.str.contains("Article")].copy()
    am.reset_index(inplace = True, drop = True)

    src_titles = am.title.unique().copy()

    data_file = "./data/json/regulation_full.json"
    data = pd.read_json(data_file)
    data = data[data.amendment != ''].copy()
    data.reset_index(inplace = True, drop = True)


    print(f"{len(data.title.unique())} target titles")
    tgt_titles = data.title.unique().copy()


    mismatch = [  title  for title in tgt_titles if title not in src_titles   ]
    print(f" {len(mismatch)} mismatch: {mismatch[:10]}")



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

    if False:

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

