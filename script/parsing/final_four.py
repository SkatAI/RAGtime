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
pd.options.display.max_colwidth = 30
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
            elif empty_cells(d, range(4,8)) :
                # TODO - verify blank

                df.loc[i, 'row_type'] = 'blank'
                df.loc[i, 'row_number'] = '.'.join(re.search(row_number_rgx, d[0]).groups())
            else:
                df.loc[i, 'row_type'] = 'content'
                df.loc[i, 'row_number'] = '.'.join(re.search(row_number_rgx, d[0]).groups())
        data = pd.concat([data,df])
        print(data.shape, file)

    print("===processing")
    data = data[~data.row_type.isin(['blank'])].copy()
    data.reset_index(inplace = True, drop = True)

    # flag paragraph that have been split into a new table due to page break
    data['merge_'] = False
    data['merge_idx'] = ''
    for i,d in data.iterrows():
        if i + 3 > data.shape[0]:
            print('-- done tagging merge rows')
            pass
        elif (data.loc[i].row_type == 'content') & (data.loc[i+1].row_type == 'table') & (data.loc[i+2].row_type == 'header') :
            data.loc[i, 'merge_'] = True
            data.loc[i, 'merge_idx'] += f"{str(i)}"
            ante = 3
            while (data.loc[i+ante].row_type == 'content') & (data.loc[i+ante-1].row_type == 'header') & (data.loc[i+ante-2].row_type == 'table') :
                data.loc[i, 'merge_idx'] += f", {str(i+ante)}"
                if i + ante + 3 > data.shape[0]:
                    break
                ante += 3
            # print(data.loc[i, 'merge_idx'])

    # cast merge indexes as int
    def try_int(s):
        if len(s) == 0:
            return []
        else:
            return [int(idx) for idx in s.split(', ')]

    data['merge_idx'] = data.merge_idx.apply(lambda d : try_int(d))


    # make sure merge_ flag only concerns multiple merge idx
    data['len_merge_idx'] = data.merge_idx.apply(lambda d : len(d))
    data.loc[data.merge_ & (data.len_merge_idx ==1), 'merge_'] = False

    # merge and flag merged flags for deletion
    cond = data.merge_ & (data.len_merge_idx > 1)
    processed_idx = []
    data['delete_'] = False
    for i, d in data[cond].iterrows():
        if i not in processed_idx:
            for col in range(4,8):
                data.loc[i, col] = ' '.join( [ data.loc[int(idx)][col]  for idx in d.merge_idx   ]   )

        for idx in d.merge_idx:
            processed_idx.append(idx)
            if idx != i:
                data.loc[idx,'delete_'] = True


    # delete the merged rows and only keep title and content
    data = data[~data.delete_].copy()
    data = data[data.row_type.isin(['title', 'content'])].copy()

    # drop non meaningfull columns
    data.drop(columns = [2,8,9, 'merge_' ,'merge_idx' ,'len_merge_idx' ,'delete_'], inplace = True)

    data.reset_index(inplace = True, drop = True)

    # rm consecutive spaces from cols 3 to 7
    print('-- rm consecutive spaces')
    rgx = r'\s+'
    for col in range(3,8):
        data[col] = data[col].apply(lambda txt : re.sub(rgx, ' ', txt).strip())

    print('-- build title, number')
    # build title column
    data['title'] = ''
    data['section'] = ''
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

    # numbering scheme
    data['i'] = data.apply(lambda d : int(d.row_number.split('.')[0]), axis =1 )
    data['j'] = data.apply(lambda d : int(d.row_number.split('.')[1]), axis =1 )

    # assert 1 == 2

    data['number'] = data.apply(lambda d : '.'.join([str(d.part), str(d.row_number)]), axis = 1)

    # extract Text Origin from draft agreement
    print('-- extract origin')
    start_token = "Text Origin:"
    data['origin'] = ''
    for i, d in data.iterrows():
        match = re.search(rf"{re.escape(start_token)}(.*)", d[7])
        if match:
            data.loc[i, 'origin'] = match.group(1).replace('\n',' ').strip()  # Everything after the token
            data.loc[i, 7] = re.sub(rf"{re.escape(start_token)}.*", "", d[7]).strip()

    data.drop(columns = [0, 1, 3], inplace = True)
    col_mapping = {
        4: 'commission',
        5: 'parliament',
        6: 'council',
        7: 'draft',
    }
    data.rename(columns = col_mapping, inplace = True)

    print('-- remove footnotes')
    start_token = "_________"
    for colnum in range(4,8):
        footnote_col = f"footnote_{col_mapping[colnum]}"
        data[footnote_col] = ''
        for i, d in data.iterrows():
            match = re.search(rf"{re.escape(start_token)}(.*)", col_mapping[colnum])
            if match:
                data.loc[i, footnote_col] = match.group(1).replace('\n',' ').strip()  # Everything after the token
                data.loc[i, col_mapping[colnum]] = re.sub(rf"{re.escape(start_token)}.*", "", col_mapping[colnum]).strip()

    cols = ['section','number', 'part','i','j', 'title', 'commission', 'council', 'parliament',  'draft', 'row_type', 'origin',
            'footnote_commission', 'footnote_parliament', 'footnote_council', 'footnote_draft']
    data = data[cols].copy()

    # find title not preceded by content
    prev = ''
    anomalies = []
    for i, d in data.iterrows():
        if i > 1:
            if (d.row_type == 'title' ) & (prev != 'content'):
                anomalies.append(i)
            elif (d.row_type == 'content' ) & (prev != 'title'):
                anomalies.append(i)
            prev = d.row_type
        else:
            prev = d.row_type
    # 20 rows have no content so title is directly followed by title
    assert len(anomalies) == 20

    # drop title lines
    data = data[data.row_type == 'content'].copy()
    data.reset_index(inplace = True, drop = True)

    for i,d in data.iterrows():
        rgx_rec = r"Recital"
        rgx_reg = r"Article|Chapter|CHAPTER|TITLE|Title"
        rgx_ann = r"Annex"
        if re.search(rgx_rec, d.title):
            data.loc[i,'section'] = 'recitals'
        elif re.search(rgx_reg, d.title):
            data.loc[i,'section'] = 'regulation'
        elif re.search(rgx_ann, d.title):
            data.loc[i,'section'] = 'annex'

    # split regulation into TITLES

    data['regulation_title'] = ''
    current_reg_title = ''
    for i, d in data.iterrows():
        if (d.section == 'regulation') & ('TITLE' in d.title):
            current_reg_title = d.title
        data.loc[i, 'regulation_title'] = current_reg_title


    # Order
    data.sort_values(by = ['part','i', 'j'], inplace = True)
    data.reset_index(inplace = True, drop = True)



    print("saving to json")
    output_file_json = "./data/json/final-four-2024-02-05.json"
    with open(output_file_json, "w", encoding="utf-8") as f:
        data.to_json(f, force_ascii=False, orient="records", indent=4)


    # ['section', 'number', 'title', 'origin']
    # vdf = pd.DataFrame()
    # for source in ['commission', 'council', 'parliament', 'draft']:
    #     cols = ['section', 'number', 'title', 'origin'] + [source, f"footnote_{source}"]
    #     tmp = data[cols].copy()
    #     tmp.rename(columns = {source: 'text', f"footnote_{source}": 'footnote'}, inplace = True)
    #     tmp['source'] = source

    #     vdf = pd.concat([vdf, tmp])
    # vdf.sort_values(by = ['part','i', 'j'], inplace = True)
    # vdf.reset_index(inplace = True, drop = True)

    # output_file_json = "./data/json/final-four-vertical-2024-02-05.json"
    # with open(output_file_json, "w", encoding="utf-8") as f:
    #     vdf.to_json(f, force_ascii=False, orient="records", indent=4)
