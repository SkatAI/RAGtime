'''
Create unique dataframe that includes all text versions from
- commission
- council
- final four
- ep adopted
- coreper
start with recital
TODO; subparagraph 1,2: replace with subparagraph a,b ?
TODO: continue on parse_loc
TODO: ingest data/txt/adopted-amendments/EP-amendments-parliament-regulation.txt
TODO: add markup to final four regulation
TODO: passer les textes et non les Lines aux fonction forrmat_reg et format_rec;  decider dans la fonction du type de lignes a creer
TODO: add political groups amendments
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
pd.options.display.max_colwidth = 60
pd.options.display.precision = 10
pd.options.display.width = 240
pd.set_option("display.float_format", "{:.2f}".format)
import numpy as np
import typing as t
from regex_utils import Rgx

recital_files = {
    'commission':'./data/txt/52021-PC0206-commission/52021PC0206-recitals.txt',
    'council':'./data/txt/ST-15698-2022-council/ST-15698-recital.txt',
    'final_four':'./data/txt/final_four/AIAct-final-four-simple-recitals.txt',
    'ep_adopted':'./data/txt/adopted-amendments/EP-amendments-parliament-recital.txt',
    'coreper':'./data/txt/coreper-feb2/AIA-Trilogue-Coreper20240202-recitals.txt',
}
regulation_files = {
    # 'commission':'./data/txt/52021-PC0206-commission/52021PC0206-regulation.txt',
    # 'council':'./data/txt/ST-15698-2022-council/ST-15698-regulation.txt',
    # 'final_four':'./data/txt/final_four/AIAct-final-four-simple-recitals.txt',
    'ep_adopted':'./data/txt/adopted-amendments/EP-amendments-parliament-regulation.txt',
    # 'coreper':'data/txt/coreper-feb2/AIA-Trilogue-Coreper20240202-regulation.txt',
}

roman_to_num = {
    'I': 1, 'IA': '001~a', 'II': 2, 'III': 3, 'IV': 4,'V': 5, 'VI': 6, 'VII': 7, 'VIII': 8,
    'VIIIA': '008~a','IX': 9, 'X': 10, 'XI': 11, 'XII': 12
}

# check that order works
def assert_order(df: pd.DataFrame) ->t.List:
    missorder = []
    for i,j in zip(df.index, df.sort_values(by = 'order').index):
        if i != j:
            missorder.append((i,j))
    if len(missorder) > 0:
        print("{len(missorder)} in missorder\n{missorder[:10]}")
    return missorder

# build path
def build_bread_and_order(df: pd.DataFrame) -> pd.DataFrame:
    # NOTE could take a list of dict insetad of a dataframe
    bread = {}
    current_par_line = 0
    for i, d in df.iterrows():
        if d.line_type == 'section_title':
            bread = {'TTL': d.number}
        elif d.line_type == 'chapter_title':
            bread.update({'cha': d.number})
            bread.pop('art', None)
            bread.pop('par', None)
            bread.pop('sub', None)
            bread.pop('pln', None)
            bread.pop('bpt', None)
        elif d.line_type == 'article_title':
            bread.update({'art': d.number})
            bread.pop('par', None)
            bread.pop('sub', None)
            bread.pop('pln', None)
            bread.pop('bpt', None)
        elif d.line_type == 'paragraph':
            current_par_line = 0
            bread.update({'par': d.number})
            bread.update({'pln':str(current_par_line)})
            bread.pop('sub', None)
            bread.pop('bpt', None)
        elif d.line_type == 'subparagraph':
            bread.update({'pln':str(current_par_line)})
            bread.update({'sub': d.number})
            bread.pop('bpt', None)
        elif d.line_type == 'bulletpoint':
            bread.update({'bpt': d.number})
            bread.update({'pln':str(current_par_line)})
            bread.pop('inp', None)
        elif d.line_type == 'in_paragraph':
            current_par_line +=1
            bread.update({'pln':str(current_par_line)})
            bread.pop('sub', None)

        df.loc[i, 'bread'] = json.dumps(bread)
        df.loc[i, 'order'] = build_order_from_bread(bread)
    return df


def build_order_from_bread(bread: t.Dict ) -> str:

    def zfillnum(txt: str) -> t.Optional[str]:
        rgx = r"([-]{0,1})(\d+)([a-z]{0,2})"
        match = re.search(rgx, txt)
        if match:
            sign = match.group(1)
            num = match.group(2).zfill(3)
            let = match.group(3)
            return f"{sign}{num}{let}"

    order = [str(roman_to_num[bread['TTL']]).zfill(3)]

    if bread.get('cha'):
        order.append(zfillnum(str(bread.get('cha'))))
    else:
        order.append('000')
    if bread.get('art'):
        order.append(zfillnum(str(bread.get('art'))))
    if bread.get('par'):
        order.append(zfillnum(str(bread.get('par'))))
        order.append(str(bread.get('pln').zfill(2)))
    if bread.get('sub'):
        order.append(str(bread.get('sub')))
    if bread.get('bpt'):
        order.append(str(bread.get('bpt')))
    if bread.get('inp'):
        order.append('~'+str(bread.get('inp')))
    return '.'.join(order)


class Line(object):
    def __init__(self, line):
        self.text = line

    def starts_with(self, start_str: str) -> re.Match:
        return Rgx.starts_with(start_str, self.text)

    def has_text(self) -> bool:
        return len(self.text) > 0

    def extract_first_number_from_title(self) -> t.Optional[str]:
        match  = Rgx.extract_first_number_from_title(self.text)
        return match.group(0).strip() if match else None

    def extract_number_in_parenthesis(self) -> t.Optional[str]:
        match = Rgx.extract_number_in_parenthesis(self.text)
        return match.group(1).strip() if match else None

    def is_subparagraph(self) -> t.Optional[str]:
        match = Rgx.is_subparagraph(self.text)
        return match.group(0).strip() if match else None

    def is_bulletpoint(self) -> t.Optional[str]:
        match = Rgx.is_bulletpoint(self.text)
        return match.group(0).strip() if match else None

    def get_line_type(self) -> None:
        if self.is_section_title():
            self.line_type = 'section_title'
            self.text = self.text.replace('##','').strip()
            self.number = self.extract_section_title_number()
        elif self.is_article_title():
            self.line_type = 'article_title'
            self.text = self.text.replace('==','').strip()
            self.number = self.extract_article_title_number()
        elif self.is_chapter_title():
            self.line_type = 'chapter_title'
            self.text = self.text.replace('**','').strip()
            self.number = self.extract_chapter_title_number()
        elif self.is_paragraph():
            self.line_type = 'paragraph'
            self.text = self.text.strip()
            self.number = self.extract_paragraph_number()
        elif self.is_subparagraph():
            self.line_type = 'subparagraph'
            self.text = self.text.strip()
            self.number = self.extract_subparagraph_number()

            if self.is_bulletpoint():
                    self.line_type = 'bulletpoint'
                    self.text = self.text.strip()
                    self.number = self.extract_bulletpoint_number()
        else:
            self.line_type = 'in_paragraph'
            self.text = self.text.strip()
            self.number = ''


    def is_section_title(self) -> t.Optional[str]:
        match = Rgx.is_section_title(self.text)
        return match.group(0).replace('##','').strip() if match else None

    def is_chapter_title(self) -> t.Optional[str]:
        match = Rgx.is_chapter_title(self.text)
        return match.group(0).replace('**','').strip() if match else None

    def is_article_title(self) -> t.Optional[str]:
        match = Rgx.is_article(self.text)
        return match.group(0).strip() if match else None

    def is_paragraph(self) -> t.Optional[str]:
        match = Rgx.is_paragraph(self.text)
        return match.group(0).strip() if match else None

    def extract_section_title_number(self) -> t.Optional[str]:
        match = Rgx.extract_section_title_number(self.text)
        return match.group(1).strip() if match else None

    def extract_article_title_number(self) -> t.Optional[str]:
        match = Rgx.extract_article_title_number(self.text)
        return match.group(1).strip() if match else None

    def extract_chapter_title_number(self) -> t.Optional[str]:
        match = Rgx.extract_chapter_title_number(self.text)
        return match.group(1).strip() if match else None

    def extract_paragraph_number(self) -> t.Optional[str]:
        match = Rgx.extract_paragraph_number(self.text)
        return match.group(1).strip() if match else None

    def extract_subparagraph_number(self) -> t.Optional[str]:
        match = Rgx.extract_subparagraph_number(self.text)
        return match.group(1).strip() if match else None

    def extract_bulletpoint_number(self) -> t.Optional[str]:
        match = Rgx.extract_bulletpoint_number(self.text)
        return match.group(1).strip() if match else None

    def parse_loc(self) -> t.Dict:
        return {}

class RecitalLine(Line):
    def __init__(self, line):
        super().__init__(line)
        self.first_number_from_title = self.extract_first_number_from_title()
        self.number_in_parenthesis = self.extract_number_in_parenthesis()


class RegulationLine(Line):
    def __init__(self, line):
        super().__init__(line)
        self.get_line_type()



def format_recital(author: str,lines: t.List[Line]) -> pd.DataFrame :
    if author in ['commission', 'council', 'coreper']:
        # extract the recital number from the text
        df = pd.DataFrame()
        df['text'] = [line.text for line in lines]
        df['title'] = [line.number_in_parenthesis for line in lines]
        df['number'] =  [Rgx.format_number(line.number_in_parenthesis) for line in lines]
        df['author'] = author
        df['amendment'] = ''

    elif author == 'final_four':
        data = []
        item = {}
        for line in lines:
            if line.starts_with("Recital"):
                item.update({
                    'title': line.text,
                    'number': Rgx.format_number(line.first_number_from_title)
                })
            elif (line.starts_with('parliament')):
                item.update({
                    'text': re.sub( r"^parliament:", '', line.text).strip()
                })
                data.append(item)
                item = {}
        df = pd.DataFrame(data)
        df['author'] = 'ff_parliament'
        df['amendment'] = ''
        df = df[df.text != ''].copy()
        df.reset_index(inplace = True, drop = True)
    elif author == 'ep_adopted':
        data = []
        item = {}
        for line in lines:
            if line.starts_with("Amendment"):
                item.update({
                    'amendment': line.text,
                })
            elif line.starts_with("Recital"):
                item.update({
                    'title': line.text,
                    'number': Rgx.format_number(line.extract_first_number_from_title())
                })
            elif line.has_text():
                item.update({
                    'text': line.text
                })
                data.append(item)
                item = {}
        df = pd.DataFrame(data)
        df['author'] = author

    return df

def format_regulation(author: str,texts: t.List) -> pd.DataFrame :
    if author in ['commission', 'council']:
        lines = [RegulationLine(txt) for txt in texts]
        data = []
        for line in lines:
            data.append({
                    'text': line.text,
                    'line_type': line.line_type,
                    'number': line.number,
                })

def parse_loc(text):
    art, par, sub, line_type = None, None, None, None
    bread = { }
    rgx = r"^loc: Article (\d+[a-z]*).*$"
    match = re.search(rgx,text)
    if match:
        art = match.group(1).strip()
        bread = { 'art': art}
        line_type = 'article_title'

    rgx = r"^loc: Article \d+[a-z]* - paragraph (\d+[a-z]*).*$"
    match = re.search(rgx,text)
    if match:
        par = match.group(1).strip()
        bread.update({'par': par })
        line_type = 'paragraph'

    rgx = r"^loc: Article (\d+[a-z]*) - paragraph (\d+[a-z]*)\s*-\s*point\s*(\d*[a-z]*).*$"
    match = re.search(rgx,text)
    if match:
        sub = match.group(3).strip()
        bread.update({'sub': sub})
        line_type = 'subparagraph'

    rgx = r"^loc: Article 3 - paragraph 1\s*-\s*point\s*(\d*[a-z]*).*$"
    match = re.search(rgx,text)
    if match:
        par = match.group(1).strip()
        bread = { 'art': '3', 'par': par}
        line_type = 'paragraph'

    return bread, line_type


def format_regulation_ep_adopted(author: str,texts: t.List) -> pd.DataFrame :
    lines = [Line(txt) for txt in texts]
    data = []
    item = {}
    current_amendment = ""
    current_location = ""
    for line in lines:
        if line.starts_with("Amendment"):
            current_amendment = line.text
            current_location = ""
            item = {
                'line_type': 'amendment',
                'amendment': line.text,
                'bread': {},
                'number': '',
                'text': line.text,
                'loc': current_location,
            }
        elif line.starts_with("loc"):
            current_location = line.text.replace('loc: ', '')
            bread, loc_line_type = parse_loc(line.text)
            item.update({
                'line_type': 'loc',
                'amendment': current_amendment,
                'bread': bread,
                'number': '',
                'text': line.text.replace('loc: ', ''),
                'loc': current_location,
            })
        elif line.has_text():
            line.get_line_type()

            item.update({
                'line_type': line.line_type,
                'amendment': current_amendment,
                'bread': bread,
                'number': line.number,
                'text': line.text,
                'loc': current_location,
            })
        data.append(item.copy())

    df = pd.DataFrame(data)
    df = df[['amendment', 'bread','number', 'text','line_type','loc']]

    return df

if __name__ == "__main__":

    # regulations
    df_regulations = pd.DataFrame()

    for author in regulation_files.keys():
        file = regulation_files[author]
        with open(file, 'r') as f:
            texts = [txt for txt in f.read().split('\n') if len(txt) >0]

        # TODO
        texts = texts[:500]
        df = format_regulation_ep_adopted(author,texts)
        print(df.line_type.value_counts())

        # df = format_regulation(author,texts)

        # df = build_bread_and_order(df).copy()
        # missorder = assert_order(df)

        # df.sort_values(by = ['order', 'author'], inplace = True)
        # df.reset_index(inplace = True, drop = True)

        # df_regulations = pd.concat([df_regulations, df])

    # print("Regulations",df_regulations.shape)
    # print(df_regulations.line_type.value_counts())
    # df = df_regulations.copy()


    # recitals
    # df_recitals = pd.DataFrame()
    # for author in ['commission','council','final_four','ep_adopted','coreper']:
    #     file = recital_files[author]
    #     with open(file, 'r') as f:
    #         texts = [txt for txt in f.read().split('\n')]

    #     lines = [RecitalLine(txt) for txt in texts  if len(txt) >0]

    #     df_recitals = pd.concat([df_recitals, format_recital(author,lines)])
    # df_recitals.sort_values(by = ['number','author'], inplace = True)
    # df_recitals.reset_index(inplace = True, drop = True)

    # print("Recitals",df_recitals.shape)

