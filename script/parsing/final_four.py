'''
Parse text into json
from final_four columns
# TODO: move to postgres
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
import uuid

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

    # ----------------------------------------------------------------------
    # Merging consecutive text blocks that have been split over page breaks
    # ----------------------------------------------------------------------

    # flag text blocks that have been split into a new table due to page break
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

    # ----------------------------------------------------------------------
    # rm not meaningfull cols and rows
    # ----------------------------------------------------------------------

    # drop table rows
    data = data[data.row_type.isin(['title', 'content'])].copy()

    # drop non meaningfull columns
    data.drop(columns = [2,8,9, 'merge_' ,'merge_idx' ,'len_merge_idx' ,'delete_'], inplace = True)

    data.reset_index(inplace = True, drop = True)

    # ----------------------------------------------------------------------
    # clean up content
    # ----------------------------------------------------------------------

    # rm consecutive spaces from cols 3 to 7
    print('-- rm consecutive spaces')
    rgx = r'\s+'
    for col in range(3,8):
        data[col] = data[col].apply(lambda txt : re.sub(rgx, ' ', txt).strip())

    # rm numbers glued to words
    rgx = r'\b([a-z]+)\d{1,2}\b'
    for col in range(3,8):
        data[col] = data[col].apply(lambda txt : re.sub(rgx, r'\1', txt).strip())

    # ----------------------------------------------------------------------
    # new features: title, numbering, Text Origin
    # ----------------------------------------------------------------------

    # title
    print('-- build title, number')
    # build title column
    data['title'] = ''
    data['section'] = ''
    data['tmp'] = data[3].apply(lambda d : d.split(' ')[0])
    for i,d in data.iterrows():
        if d.tmp in ['Proposal','Article', 'Recital', 'Annex', 'Chapter', 'CHAPTER', 'TITLE', 'Formula', 'Citation', 'Title']:
            data.loc[i, 'title'] = d[3]

    data.drop(columns = ['tmp'], inplace = True)

    # add title to content rows
    current_title = ''
    for i, d in data.iterrows():
        if len(d.title) >0:
            current_title = d.title
        else:
            data.loc[i, 'title'] = current_title

    # create numbering scheme
    data['i'] = data.apply(lambda d : int(d.row_number.split('.')[0]), axis =1 )
    data['j'] = data.apply(lambda d : int(d.row_number.split('.')[1]), axis =1 )
    # keep original numbering order from the pdf
    data['pdf_order'] = data.apply(lambda d : '.'.join([str(d.part), str(d.row_number)]), axis = 1)

    # extract Text Origin from draft agreement
    print('-- extract origin')
    start_token = "Text Origin:"
    data['origin'] = ''
    for i, d in data.iterrows():
        match = re.search(rf"{re.escape(start_token)}(.*)", d[7])
        if match:
            data.loc[i, 'origin'] = match.group(1).replace('\n',' ').strip()  # Everything after the token
            data.loc[i, 7] = re.sub(rf"{re.escape(start_token)}.*", "", d[7]).strip()

    # extract footnotes
    # on hold for the moment
    if False:
        print('-- extract and remove footnotes')

        start_token = "_________"
        for colnum in range(4,8):
            footnote_col = f"footnote_{colnum}"
            data[footnote_col] = ''
            for i, d in data.iterrows():
                match = re.search(rf"{re.escape(start_token)}(.*)", d[colnum])
                if match:

                    data.loc[i, footnote_col] = match.group(1).replace('\n',' ').strip()  # Everything after the token
                    data.loc[i, colnum] = re.sub(rf"{re.escape(start_token)}.*", "", d[colnum]).strip()

    # uuid for each text block
    data['uuid'] = [str(uuid.uuid4()) for n in range(len(data))]


    # ----------------------------------------------------------------------
    # column naming and ordering
    # ----------------------------------------------------------------------

    data.drop(columns = [0, 1, 3], inplace = True)
    col_mapping = {
        4: 'commission',
        5: 'parliament',
        6: 'council',
        7: 'draft',
        # 'footnote_4':'footnote_commission',
        # 'footnote_5':'footnote_parliament',
        # 'footnote_6':'footnote_council',
        # 'footnote_7':'footnote_draft'
    }
    data.rename(columns = col_mapping, inplace = True)

    # ----------------------------------------------------------------------
    # sanity check
    # ----------------------------------------------------------------------

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

    # ----------------------------------------------------------------------
    # new features: add section, parse title
    # ----------------------------------------------------------------------
    # drop title lines
    data = data[data.row_type == 'content'].copy()
    data.reset_index(inplace = True, drop = True)

    # somehow the order counts, otherwise some Citation have Annex in title
    for i,d in data.iterrows():
        rgx_rec = r"Recital"
        rgx_reg = r"Article|Chapter|CHAPTER|TITLE|Title"
        rgx_ann = r"Annex"
        rgx_cit = r"Citation|Formula|Proposal Title|"
        if re.search(rgx_rec, d.title):
            data.loc[i,'section'] = 'recitals'
        elif re.search(rgx_reg, d.title):
            data.loc[i,'section'] = 'regulation'
        elif re.search(rgx_ann, d.title):
            data.loc[i,'section'] = 'annex'
        elif re.search(rgx_cit, d.title):
            data.loc[i,'section'] = 'citation'

    # assign TITLE level to the regulation section
    data['regulation_title'] = ''
    current_reg_title = ''
    for i, d in data.iterrows():
        if (d.section == 'regulation') & ('TITLE' in d.title):
            current_reg_title = d.title
        data.loc[i, 'regulation_title'] = current_reg_title


    # ----------------------------------------------------------------------
    # level 1
    # ----------------------------------------------------------------------


    # article number
    data['level_1'] = '0'
    rgx_source = r'.*?(\d+).*$'
    rgx_target = r'\1'
    for i, d in data.loc[data.section != 'annex'].iterrows():
        data.loc[i, 'level_1'] =  re.sub(rgx_source, rgx_target, d.title)


    # Annex number transform  Roman numbering into ints in Annex
    roman_to_num = {
        'I': 1, 'II': 2, 'III': 3, 'IV': 4,'V': 5, 'VI': 6, 'VII': 7, 'VIII': 8, 'IX': 9
    }
    rgx = r'Annex ((?:I[XV]|V?I{0,3}))[a-zA-Z]*'
    for i, d in data.loc[data.section == 'annex'].iterrows():
        match = re.search(rgx, d.title)
        if match:
            data.loc[i, 'level_1'] =  str(roman_to_num[match.group(1).strip()])

    # remaining titles
    data.loc[data.level_1.isin([ 'Formula','Proposal Title','Title Ia']), 'level_1'] = '1'
    data.loc[data.level_1.str.contains('TITLE') | data.level_1.str.contains('Chapter'), 'level_1'] = '1'

    data['level_1'] = data.level_1.astype(int)

    # ----------------------------------------------------------------------
    # level 2
    # Annex II, point 2
    # Annex III, seventh paragraph
    # Article 4a(1)
    # Article 3, first paragraph, point (1)
    # but not:
    # Article 10(1), second subparagraph new
    # ----------------------------------------------------------------------
    ordinal_to_int = { "first": 1, "second": 2, "third": 3, "fourth": 4, "fifth": 5, "sixth": 6,
                        "seventh": 7, "eighth": 8, "ninth": 9,
                        "tenth": 10, "eleventh": 11, "twelfth": 12, "thirteenth": 13, "fourteenth": 14, "fifteenth": 15, "sixteenth": 16,
                        "seventeenth": 17, "eighteenth": 18, "nineteenth": 19, "twentieth": 20, 'twenty-first': 21
                    }

    data['level_2'] = '0'

    # 1) Article 4a(1) -> 1
    rgx = r'Article .*?\((\d+).*?\).*$'
    test = {"Article 4a(1)" : 1,
            "Article 61(4), second subparagraph": 4,
            "Article 63(7d), second subparagraph": 7}

    for txt, n in test.items():
        match = re.search(rgx, txt)
        assert match.group(1) == str(n)

    for i, d in data.loc[data.section == 'regulation'].iterrows():
        match = re.search(rgx, d.title)
        if match:
            data.loc[i, 'level_2'] =  str(match.group(1).strip())


    # 2) Article 61, second paragraph -> 2
    ordinal_list = '|'.join(ordinal_to_int.keys())

    rgx = rf".*?({ordinal_list}) paragraph.*$"

    test = {
            "Article 61, second paragraph": 'second',
            "Article 10(1), second subparagraph": None,
            "Article 82, third paragraph, amending provision, first subparagraph, second paragraph" : 'third',
            "Article 82, first paragraph, amending provision, first subparagraph, second paragraph" : 'first',
        }

    for txt, output in test.items():
        match = re.search(rgx, txt)
        if match:
            assert match.group(1) == str(output)
        else:
            assert match is None

    for i, d in data.loc[data.section == 'regulation'].iterrows():
        match = re.search(rgx, d.title)
        if match:
            data.loc[i, 'level_2'] =  ordinal_to_int[str(match.group(1).strip())]


    # 3) annex: Annex VII, nineteenth paragraph => 19

    rgx = rf".*?({ordinal_list}) paragraph.*$"

    test = {
            "Annex VII, nineteenth paragraph": 'nineteenth',
            "Annex VII, point 1., first subparagraph": None,
            "Annex VII, first paragraph, point (d)" : 'first',
        }

    for txt, output in test.items():
        match = re.search(rgx, txt)
        if match:
            assert match.group(1) == str(output)
        else:
            assert match is None

    for i, d in data.loc[data.section == 'annex'].iterrows():
        match = re.search(rgx, d.title)
        if match:
            data.loc[i, 'level_2'] =  ordinal_to_int[str(match.group(1).strip())]

    # 4) annex: Annex IX, point 3.(a) => 3

    rgx = r'Annex.*?point (\d+)\..*$'

    test = {
            "Annex IX, point 3.(a)": '3',
            "Annex VII, point 1., first subparagraph": '1',
            "Annex VII, tenth paragraph" : None,
        }

    for txt, output in test.items():
        match = re.search(rgx, txt)
        if match:
            assert match.group(1) == str(output)
        else:
            assert match is None

    for i, d in data.loc[data.section == 'annex'].iterrows():
        match = re.search(rgx, d.title)
        if match:
            data.loc[i, 'level_2'] =  match.group(1).strip()

    data['level_2'] = data.level_2.astype(int)

    # ------------------------------------------------------
    #  level 3
    # ------------------------------------------------------

    current_l1 = 0
    current_l2 = 0
    current_l3 = 0
    data['level_3'] = 0
    for i,d in data.iterrows():
        if d.level_1 != current_l1:
            current_l1 = d.level_1
            current_l3 = 0
        elif d.level_2 != current_l2:
            current_l2 = d.level_2
            current_l3 = 0
        else:
            current_l3  +=1
        data.loc[i, 'level_3']  = current_l3


    # recitals level 2 = level 3 and level 3 = 0
    cond = data.section == 'recitals'
    data.loc[cond, 'level_2'] = data[cond].level_3 + 1
    data.loc[cond, 'level_3'] = 0


    # ------------------------------------------------------
    #  ordering columns and rows
    # ------------------------------------------------------
    cols = ['uuid','section','pdf_order', 'part','i','j', 'title','regulation_title','level_1', 'level_2', 'level_3','commission', 'council', 'parliament',  'draft', 'row_type', 'origin']
    data = data[cols].copy()


    # re Order
    data.sort_values(by = ['part','i', 'j'], inplace = True)
    data.reset_index(inplace = True, drop = True)


    # ------------------------------------------------------
    #  saving
    # ------------------------------------------------------
    print("saving to json")
    output_file_json = "./data/json/final-four-2024-02-06.json"
    with open(output_file_json, "w", encoding="utf-8") as f:
        data.to_json(f, force_ascii=False, orient="records", indent=4)

    # ------------------------------------------------------
    #  mapping
    # ------------------------------------------------------

    cols = ['uuid','pdf_order', 'part','i','j', 'level_1', 'level_2', 'level_3']
    mapp = data[cols].copy()
    mapp['modified_at'] = None
    output_file_json = "./data/json/final_four_mapping-2024-02-06.json"
    with open(output_file_json, "w", encoding="utf-8") as f:
        mapp.to_json(f, force_ascii=False, orient="records", indent=4)

    # ------------------------------------------------------
    #  verticalize
    # ------------------------------------------------------
    print("-- verticalize")
    vdata = []
    keep_cols = ['uuid', 'section', 'pdf_order', 'part', 'i', 'j', 'title', 'regulation_title', 'level_1', 'level_2', 'level_3', 'origin']
    text_cols = ['commission', 'parliament', 'council', 'draft']
    for i,d in tqdm(data.iterrows()):
        for col in text_cols:
            item = dict(d[keep_cols]).copy()
            item.update({
                'text': d[col],
                'author': col,
                'vvid': str(uuid.uuid4()),
            })
            vdata.append(item)

    vdata = pd.DataFrame(vdata)
    cols = ['vvid', 'uuid', 'section', 'title', 'author', 'text','pdf_order', 'part', 'i', 'j', 'regulation_title', 'level_1', 'level_2', 'level_3', 'origin']
    vdata = vdata[cols].copy()
    output_file_json = "./data/json/final_four_author-2024-02-06.json"
    with open(output_file_json, "w", encoding="utf-8") as f:
        vdata.to_json(f, force_ascii=False, orient="records", indent=4)


