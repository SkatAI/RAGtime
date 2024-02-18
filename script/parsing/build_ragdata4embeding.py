'''
Build whole dataset for RAG
v1: recital and regulation
- commission
- council
- coreper
extra cols: proposers, group, amendment,
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
    # load regulation: rgn
    file_regulation = './data/rag/regulation-20240218.json'
    rgn = pd.read_json(file_regulation)
    # load recital
    file_recital = './data/rag/recital-20240218.json'
    rcl = pd.read_json(file_recital)

    # fix columns
    # rgn.columns Index(['text', 'line_type', 'number', 'bread', 'order', 'author'], dtype='object')
    rgn['amendment'] = ''
    rgn['section'] = 'articles'
    # rcl.columns: Index(['text', 'title', 'number', 'author', 'amendment'], dtype='object')
    rcl['line_type'] = 'recital'
    rcl['bread'] = rcl.number.apply( lambda num : json.dumps( {'rec': str(num)  }    )  )
    rcl['order'] = rcl.number.apply( lambda num : str(num).zfill(5)  )
    rcl['section'] = 'recitals'
    rcl.drop(columns = 'title', inplace = True)

    assert sorted(rcl.columns) == sorted(rgn.columns)
    # dumps to rag dataset
    data = pd.concat([rcl, rgn])
    data.sort_values(by = ['author', 'order'], inplace = True)

    # uuid
    # data['uuid'] = [ str(uuid.uuid4()) for i in range(len(data))  ]
    # aggregate at teh paragraph level and at the aricle level
    data['dbrd'] = data.bread.apply(json.loads)
    data['rec']  = data.dbrd.apply(lambda b : f"Recital {str(b.get('rec')).zfill(6)}" if b.get('rec') else '' )
    data['ttl']  = data.dbrd.apply(lambda b : f"TITLE {str(b.get('TTL')).zfill(5)}" if b.get('TTL') else '' )
    data['art']  = data.dbrd.apply(lambda b : f"Article {str(b.get('art')).zfill(4)}" if b.get('art') else '' )
    data['par']  = data.dbrd.apply(lambda b : f"paragraph {str(b.get('par')).zfill(4)}" if b.get('par') else '' )

    # group by articles
    arts = data.groupby(by = ['rec','ttl','art','author','section','amendment'], as_index=False).agg({'text': '\n'.join}  )
    pars = data.groupby(by = ['rec','ttl','art', 'par','author','section','amendment'], as_index=False).agg({'text': '\n'.join}  )

    arts.loc[arts.art == '', 'line_type'] = 'other'
    arts.loc[arts.art != '', 'line_type'] = 'article'

    pars.loc[pars.par == '', 'line_type'] = 'other'
    pars.loc[pars.par != '', 'line_type'] = 'paragraph'

    ragdata = pd.concat([pars, arts])
    ragdata.fillna('', inplace = True)
    ragdata.reset_index(inplace=True, drop = True)
    ragdata['uuid'] = [ str(uuid.uuid4()) for i in range(len(ragdata))  ]

    output_file_json = "./data/rag/ragtime_20240218.json"
    with open(output_file_json, "w", encoding="utf-8") as f:
        ragdata.to_json(f, force_ascii=False, orient="records", indent=4)

