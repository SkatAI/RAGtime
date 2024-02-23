'''
Build whole dataset for RAG
v1: recital and regulation
- commission
- council
- coreper

# TODO: anxs has title for commission with council title: ANNEX I: [deleted]
# TODO: anxs in section title: paragraph number appears
# TODO: article 3 has too many tokens
# TODO break down articles that have too many tokens (> threshold)
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
import uuid
from regex_utils import Rgx
from lines import Line, RecitalLine, RegulationLine

if __name__ == "__main__":
    file_regulation = './data/rag/regulation-20240218.json'
    file_recital = './data/rag/recital-20240218.json'
    file_annex = './data/rag/annex-20240219.json'

    # ------------------------------------------------------------------------------------
    # regulation: only recital content, one liner
    # ------------------------------------------------------------------------------------
    # load regulation: rgn
    rgn = pd.read_json(file_regulation)
    rgn['section'] = 'articles'

    # regulation
    data = rgn.copy()
    data['dbrd'] = data.bread.apply(json.loads)
    data['ttl']  = data.dbrd.apply(lambda b : f"TITLE {str(b.get('TTL'))}" if b.get('TTL') else '' )
    data['cha']  = data.dbrd.apply(lambda b : f"Chapter {str(b.get('cha'))}" if b.get('cha') else '' )
    data['art']  = data.dbrd.apply(lambda b : f"Article {str(b.get('art'))}" if b.get('art') else '' )
    data['par']  = data.dbrd.apply(lambda b : f"paragraph {str(b.get('par'))}" if b.get('par') else '' )



    def rm_blank(lst : t.List) -> t.List:
        return [a for a in lst if a != '']

    ct = ['','', '', '']
    for author in data.author.unique():
        cond = data.author == author
        for i, d in data[cond].iterrows():
            if d.line_type == 'section_title':
                ct = [d.text, '', '', '']
                data.loc[i, 'title'] = ct[0]
            elif d.line_type == 'chapter_title':
                ct[1] = d.text
                data.loc[i, 'title'] = ' - '.join(rm_blank(ct[:2]))
            elif d.line_type == 'article_title':
                ct[2] = d.text
                data.loc[i, 'title'] = ' - '.join(rm_blank(ct[:3]))
            else:
                # ct[3] = d.text
                data.loc[i, 'title'] = ' - '.join(rm_blank(ct))

    # article 3
    cond =  (data.art == 'Article 3')
    rgx = r"^(\d+[a-z]{0,3}\d*)\.\s[‘’'](.*)[‘’'].*$"
    current_title = 'Article 3: Definitions'
    current_art = ''
    for i, d in data[cond].iterrows():
        m = re.search(rgx, d.text)
        if m is not None:
            title = d.title + ': ' + m.group(2)
            art = f"Article 3.{m.group(1)}"
            current_title = title
            current_art = art
            data.loc[i, 'title'] = current_title
            data.loc[i, 'art'] = current_art
        else:
            data.loc[i, 'title'] = current_title
            data.loc[i, 'art'] = current_art

    # article 5 for coreper
    cond =  (data.author == 'coreper') & (data.art == 'Article 5')
    for i, d in data[cond].iterrows():
        data.loc[i, 'art'] = f"{d.art} - {d.par}"

    # article 53 for coreper
    cond =  (data.author == 'coreper') & (data.art == 'Article 53')
    for i, d in data[cond].iterrows():
        data.loc[i, 'art'] = f"{d.art} - {d.par}"


    # group by articles
    arts = data.groupby(by = ['ttl','cha','art','title','author','section'], as_index=False).agg({'text': '\n'.join}  )

    arts.loc[(arts.art == ''), 'content_type'] = 'header'
    arts.loc[(arts.art != ''),  'content_type'] = 'article'

    arts = arts[['author', 'section', 'content_type', 'title', 'text']]

    # group by paragraphs
    pars = data.groupby(by = ['ttl','cha','art', 'par', 'title','author','section'], as_index=False).agg({'text': '\n'.join}  )
    # add paragraph number to title
    for i, d in pars.iterrows():
        if d.par != '':
            pars.loc[i, 'title'] = f"{d.title} - {d.par}"

    pars.loc[(pars.par == ''), 'content_type'] = 'header'
    pars.loc[(pars.par != ''),  'content_type'] = 'paragraph'

    pars = pars[['author', 'section', 'content_type', 'title', 'text']]

    # ------------------------------------------------------------------------------------
    # recitals: only recital content, one liner
    # ------------------------------------------------------------------------------------

    rcl = pd.read_json(file_recital)
    rcl['section'] = 'recitals'
    rcl['content_type'] = 'recital'

    rcl = rcl[['author', 'section', 'content_type', 'title', 'text']]


    # ------------------------------------------------------------------------------------
    # annex:
    # ------------------------------------------------------------------------------------

    anx = pd.read_json(file_annex)
    anx['section'] = 'annex'

    data = anx.copy()
    data['dbrd'] = data.bread.apply(json.loads)
    data['anx']  = data.dbrd.apply(lambda b : f"Annex {str(b.get('anx'))}" if b.get('anx') else '' )
    data['sct']  = data.dbrd.apply(lambda b : f"Section {str(b.get('sct'))}" if b.get('sct') else '' )
    data['sct']  = data.dbrd.apply(lambda b : f"Part {str(b.get('prt'))}" if b.get('prt') else '' )
    data['par']  = data.dbrd.apply(lambda b : f"Paragraph {str(b.get('par'))}" if b.get('par') else '' )

    ct = ['','', '', '']
    for author in data.author.unique():
        cond = data.author == author

        for i, d in data[cond].iterrows():
            if d.line_type == 'annex_title':
                ct = [d.text, '', '', '']
                data.loc[i, 'title'] = ct[0]
            elif d.line_type in ['annex_section', 'annex_part']:
                ct[1] = d.text
                data.loc[i, 'title'] = ' - '.join(rm_blank(ct[:2]))
            elif d.line_type == 'paragraph':
                ct[2] = d.par
                data.loc[i, 'title'] = ' - '.join(rm_blank(ct[:3]))
            else:
                data.loc[i, 'title'] = ' - '.join(rm_blank(ct))

    anxs = data.groupby(by = ['anx', 'sct', 'par', 'title', 'author','section'], as_index=False).agg({'text': '\n'.join}  )
    anxs.loc[(anxs.par == '') , 'content_type'] = 'header'
    anxs.loc[(anxs.par != '') , 'content_type'] = 'annex_paragraph'

    anxs = anxs[['author', 'section', 'content_type', 'title', 'text']]

    ragdata = pd.concat([rcl, pars, arts, anxs])
    ragdata.fillna('', inplace = True)
    ragdata.reset_index(inplace=True, drop = True)
    ragdata['uuid'] = [ str(uuid.uuid4()) for i in range(len(ragdata))  ]

    # all other lines are also

    output_file_json = "./data/rag/ragtime_20240220.json"
    with open(output_file_json, "w", encoding="utf-8") as f:
        ragdata.to_json(f, force_ascii=False, orient="records", indent=4)

