'''
Ingest Q&A into groundtruth
from augmented data : ./data/augment/*.json
from live Q&A: google bucket
'''

import os, re, json
import time, datetime
from datetime import timedelta
import pandas as pd
import argparse
pd.options.display.max_columns = 100
pd.options.display.max_rows = 60
pd.options.display.max_colwidth = 100
pd.options.display.precision = 10
pd.options.display.width = 160
pd.set_option("display.float_format", "{:.2f}".format)
import numpy as np
import glob

import psycopg2
from sqlalchemy import create_engine
import sys
sys.path.append('./script')
from db_utils import Database

if __name__ == "__main__":

    # read augmented Q&A into df
    qa_files = glob.glob("./data/augment/*.json")
    data = pd.DataFrame()
    for file in qa_files:
        tmp = pd.read_json(file)
        print(tmp.shape)
        data = pd.concat([data, tmp])
    data.reset_index(drop = True, inplace = True)

    # split short and expert asnwers
    data['short'] = data.answer.apply(lambda d : d['short'])
    data['expert'] = data.answer.apply(lambda d : d['expert'])


    gtr = []
    for i,d in data.iterrows():
        gtr.append({
            'question': d.question,
            'answer': d.answer['short'],
            'answer_type': 'short',
        })
        gtr.append({
            'question': d.question,
            'answer': d.answer['expert'],
            'answer_type': 'expert',
        })

    gtr = pd.DataFrame(gtr)
    gtr['source'] = 'gpt4-qa'

    if True:
        db = Database()
        gtr.to_sql(name="groundtruth", con=db.engine, if_exists="append", index=False)