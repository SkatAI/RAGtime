'''
Parse text into json
from final_four columns
'''


# usual suspects
import os, re, json, glob
import time, datetime
from datetime import timedelta
import pandas as pd
import argparse
from tqdm import tqdm
pd.options.display.max_columns = 100
pd.options.display.max_rows = 60
pd.options.display.max_colwidth = 60
pd.options.display.precision = 10
pd.options.display.width = 180
pd.set_option("display.float_format", "{:.2f}".format)
import numpy as np

if __name__ == "__main__":
    files = glob.glob(os.path.join('data/txt/final_four/', '*.txt'))
    files.sort()

    data = pd.DataFrame()
    for file in files:
        row_list = []
        with open(file, 'r') as f:
            text = f.read()

        # split across tables
        tables = text.split("--\n\n\nTTTXX")
        rows = []
        for table in tables:
            rows += table.split("== ROW")

        for row in rows:
            row_list.append(
                [r.strip() for r in row.split('-- COL')]
            )

        df = pd.DataFrame(row_list)

        # rm -- and strip
        tri_number_rgx = r"^(\d+).(\d+).(\d+)"
        df.fillna('', inplace = True)
        for i, d in df.iterrows():
            for j in range(len(d)):
                df.loc[i,j] = d[j].replace('--','').strip().replace('\n',' ')
                # rm 2.0.3 at beginning of line
                df.loc[i,j] = re.sub(tri_number_rgx, '', d[j]).strip()


        df['row_type'] = ''
        df['row_number'] = ''

        table_rgx = r"TABLE: (\d+) XXTTT"
        header_rgx = r"Commission Proposal"
        row_number_rgx = r"(\d+).(\d+) =="
        for i, d in df.iterrows():
            # col 0: TTTXX TABLE: 12 XXTTT
            if re.search(table_rgx, d[0]):
                # get table rows
                df.loc[i, 'row_type'] = 'table'
                df.loc[i, 'row_number'] = re.search(table_rgx, d[0]).group(1)

            # col 4: Commission Proposal
            elif re.search(header_rgx, d[4]):
                # get table rows
                df.loc[i, 'row_type'] = 'header'
                df.loc[i, 'row_number'] = '.'.join(re.search(row_number_rgx, d[0]).groups())
            else:
                df.loc[i, 'row_type'] = 'content'
                df.loc[i, 'row_number'] = '.'.join(re.search(row_number_rgx, d[0]).groups())
        data = pd.concat([data,df])
        print(data.shape)





    # rm all \n
