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

def empty_cells(row: pd.core.series.Series, fromto : range) -> bool:
    return len(row[fromto].sum()) == 0



if __name__ == "__main__":

    folder_ = "/Users/alexis/Google Drive/My Drive/SkatAI/SkatAI projects/RAG-AI-act/data/AIACT-finalfour/extract/*.txt"
    files = glob.glob(folder_)
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
        df['part'] = int(file.split('/')[-1].split('.')[0].split('-')[-1][-3:])

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
            elif empty_cells(d, range(4,10)) & (not empty_cells(d, range(3,4))):
                df.loc[i, 'row_type'] = 'title'
                df.loc[i, 'row_number'] = '.'.join(re.search(row_number_rgx, d[0]).groups())
            elif empty_cells(d, range(4,10)) :
                # TODO - verify blank

                df.loc[i, 'row_type'] = 'blank'
                df.loc[i, 'row_number'] = '.'.join(re.search(row_number_rgx, d[0]).groups())
            else:
                df.loc[i, 'row_type'] = 'content'
                df.loc[i, 'row_number'] = '.'.join(re.search(row_number_rgx, d[0]).groups())
        data = pd.concat([data,df])
        print(data.shape, file)

    print("===processing")

    # flag paragraph that have been split into a new table due to page break


    data = data[data.row_type.isin(['title', 'content'])].copy()
    data.reset_index(inplace = True, drop = True)
    data.drop(columns = [2,8,9], inplace = True)
    # TODO - merge with previous when page break

    data['merge'] = False
    for i,d in data.iterrows():
        if i < 3:
            pass
        elif (data.loc[i-1].row_type == 'header') & (data.loc[i-3].row_type == 'content')  :
            data.loc[i, 'merge'] = True

    assert 1 == 2


    # rm consecutive spaces from cols 3 to 7
    print('-- rm consecutive spaces')
    rgx = r'\s+'
    for col in range(3,8):
        data[col] = data[col].apply(lambda txt : re.sub(rgx, ' ', txt).strip())

    print('-- build title, number')
    # build title column
    data['title'] = ''
    data['tmp'] = data[3].apply(lambda d : d.split(' ')[0])
    for i,d in data.iterrows():
        if d.tmp in ['Proposal','Article', 'Recital', 'Annex', 'Chapter', 'CHAPTER', 'TITLE', 'Formula', 'Citation', 'Title']:
            data.loc[i, 'title'] = d[3]
    data.drop(columns = ['tmp'], inplace = True)

    current_title = ''
    for i, d in data.iterrows():
        if len(d.title) >0:
            current_title = d.title
        else:
            data.loc[i, 'title'] = current_title

    data['number'] = data.apply(lambda d : '.'.join([str(d.part), str(d.row_number)]), axis = 1)

    # extract Text Origin from draft agreement
    print('-- extract origin')
    start_token = "Text Origin:"
    data['origin'] = ''
    for i, d in data.iterrows():
        match = re.search(rf"{re.escape(start_token)}(.*)", d[7])
        if match:
            data.loc[i, 'origin'] = match.group(1).replace('\n',' ').strip()  # Everything after the token








    # rm all \n
