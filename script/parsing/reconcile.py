'''
Create unique dataframe that includes all text versions from
- commission
- council
- final four
- ep adopted
- coreper
start with recital
TODO: '01~a.000' for title IA : sorted(['01.000', '02.000', '01~a.000'])
TODO: detect bullet points withing paragraphs
TODO: in build_order_from_bread add bullet points (~iii?)
TODO: add markup to final four regulation
TODO: ingest data/txt/adopted-amendments/EP-amendments-parliament-regulation.txt
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
pd.options.display.max_colwidth = 120
pd.options.display.precision = 10
pd.options.display.width = 140
pd.set_option("display.float_format", "{:.2f}".format)
import numpy as np
import typing as t

# in final four we only want the parliament version to reconcile titles between final four and ep-adopted
recital_files = {
    'commission':'./data/txt/52021-PC0206-commission/52021PC0206-recitals.txt',
    'council':'./data/txt/ST-15698-2022-council/ST-15698-recital.txt',
    'final_four':'./data/txt/final_four/AIAct-final-four-simple-recitals.txt',
    'ep_adopted':'./data/txt/adopted-amendments/EP-amendments-parliament-recital.txt',
    'coreper':'./data/txt/coreper-feb2/AIA-Trilogue-Coreper20240202-recitals.txt',
}
regulation_files = {
    'commission':'./data/txt/52021-PC0206-commission/52021PC0206-regulation.txt',
    'council':'./data/txt/ST-15698-2022-council/ST-15698-regulation.txt',
    # 'final_four':'./data/txt/final_four/AIAct-final-four-simple-recitals.txt',
    # 'ep_adopted':'./data/txt/adopted-amendments/EP-amendments-parliament-recital.txt',
    'coreper':'data/txt/coreper-feb2/AIA-Trilogue-Coreper20240202-regulation.txt',
}


roman_to_num = {
    'I': 1, 'IA': '1~a', 'II': 2, 'III': 3, 'IV': 4,'V': 5, 'VI': 6, 'VII': 7, 'VIII': 8,
    'VIIIA': '8~a',
    'IX': 9, 'X': 10, 'XI': 11, 'XII': 12
}


def format_number(text: str) -> str:
    rgx     = r"(^[-]{0,1})(\d+)([a-z+-]{0,3}\d*)"
    match   = re.match(rgx, text)
    assert match is not None, "no number to be found"
    sign    = match.group(1).strip()
    num     = match.group(2).strip().zfill(3)
    letters = match.group(3).strip()

    return f"{num}{sign}{letters}"

assert format_number('1') == '001'
assert format_number('1a') == '001a'
assert format_number('-1a') == '001-a'
assert format_number('-1') == '001-'
assert format_number('80z+1') == '080z+1'
assert format_number('80-x') == '080-x'

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

class RecitalLine(Line):
    def __init__(self, line):
        super().__init__(line)
        self.first_number_from_title = self.extract_first_number_from_title()
        self.number_in_parenthesis = self.extract_number_in_parenthesis()


class RegulationLine(Line):
    def __init__(self, line):
        super().__init__(line)
        self.get_line_type()

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

            # if self.is_bulletpoint():
            #     self.line_type = 'bulletpoint'
            #     self.text = self.text.strip()
            #     self.number = self.extract_bulletpoint_number()

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
        self.line_type = 'article_title'
        return match.group(0).strip() if match else None

    def is_paragraph(self) -> t.Optional[str]:
        match = Rgx.is_paragraph(self.text)
        self.line_type = 'paragraphe'
        return match.group(0).strip() if match else None

    def is_subparagraph(self) -> t.Optional[str]:
        match = Rgx.is_subparagraph(self.text)
        self.line_type = 'subparagraphe'
        return match.group(0).strip() if match else None

    def is_bulletpoint(self) -> t.Optional[str]:
        match = Rgx.is_bulletpoint(self.text)
        self.line_type = 'bulletpoint'
        return match.group(0).strip() if match else None

class Rgx(object):
    # def roman(n): return chr(0x215F + n)

    @classmethod
    def extract_section_title_number(cls, text: str) -> re.Match:
        rgx = r"^TITLE\s([I,X,V,A]+)\s*:.*$"
        return re.search(rgx, text)

    @classmethod
    def extract_chapter_title_number(cls, text: str) -> re.Match:
        # Chapter 1: CLASSIFICATION OF AI SYSTEMS AS HIGH-RISK
        rgx = r"^Chapter\s*(\d+)\s*:.*$"
        return re.search(rgx, text)

    @classmethod
    def extract_article_title_number(cls, text: str) -> re.Match:
        rgx = r"^Article\s(\d+)\s*:.*$"
        return re.search(rgx, text)

    @classmethod
    def extract_paragraph_number(cls, text: str) -> re.Match:
        rgx = r"^(\d+)\..*$"
        return re.search(rgx, text)

    @classmethod
    def extract_subparagraph_number(cls, text: str) -> re.Match:
        rgx = r"^\(([a-z]{0,2})\).*$"
        return re.search(rgx, text)

    @classmethod
    def extract_bulletpoint_number(cls, text: str) -> re.Match:
        rgx = r"^\(([ivx]{1,3})\).*$"
        return re.search(rgx, text)

    @classmethod
    def extract_number_in_parenthesis(cls, text: str) -> re.Match:
        # (1) (12) (1a) (-12a) (80z+1)
        rgx = r"^\(([-]*\s*\d+\s*[a-z+-]{0,3}\d*)\).*$"
        return re.search(rgx, text)

    @classmethod
    def extract_first_number_from_title(cls, text: str) -> re.Match:
        # Recital 12a
        rgx = r"[-]{0,1}\d+[a-z]{0,3}"
        return re.search(rgx, text)

    @classmethod
    def starts_with(cls, start_str: str, text: str) -> re.Match:
        rgx = rf"{start_str}"
        return re.search(rgx,text)

    @classmethod
    def is_section_title(cls, text: str) -> re.Match:
        rgx = r"^## TITLE"
        return re.search(rgx,text)

    @classmethod
    def is_chapter_title(cls, text: str) -> re.Match:
        rgx = r"^\*\* chapter"
        return re.search(rgx,text, re.IGNORECASE)

    @classmethod
    def is_article(cls, text: str) -> re.Match:
        rgx = r"^== Article"
        return re.search(rgx,text)

    @classmethod
    def is_paragraph(cls, text: str) -> re.Match:
        rgx = r"^(\d+)\."
        return re.search(rgx,text)

    @classmethod
    def is_subparagraph(cls, text: str) -> re.Match:
        rgx = r"^\(([a-z]{0,3})\).*$"
        return re.search(rgx,text)

    @classmethod
    def is_bulletpoint(cls, text: str) -> re.Match:
        rgx = r"^\((ⅰ|ii|iii|iv|v|vi|vii|viii|ix|x|xi|xii|xiii)\).*$"
        return re.search(rgx,text)


def format_recital(author: str,lines: t.List[Line]) -> pd.DataFrame :
    if author in ['commission', 'council', 'coreper']:
        # extract the recital number from the text
        df = pd.DataFrame()
        df['text'] = [line.text for line in lines]
        df['title'] = [line.number_in_parenthesis for line in lines]
        df['number'] =  [format_number(line.number_in_parenthesis) for line in lines]
        df['author'] = author
        df['amendment'] = ''

    elif author == 'final_four':
        data = []
        item = {}
        for line in lines:
            if line.starts_with("Recital"):
                item.update({
                    'title': line.text,
                    'number': format_number(line.first_number_from_title)
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
                    'number': format_number(line.extract_first_number_from_title())
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
    data = []
    for line in lines:
        data.append({
                'text': line.text,
                'line_type': line.line_type,
                'number': line.number,
            })
    df = pd.DataFrame(data)
    df['author'] = author
    return df

if __name__ == "__main__":

    # recitals
    df_recitals = pd.DataFrame()
    for author in ['commission','council','final_four','ep_adopted','coreper']:
        file = recital_files[author]
        with open(file, 'r') as f:
            lines = [RecitalLine(txt) for txt in f.read().split('\n') if len(txt) >0]

        df_recitals = pd.concat([df_recitals, format_recital(author,lines)])
    df_recitals.sort_values(by = ['number','author'], inplace = True)
    df_recitals.reset_index(inplace = True, drop = True)

    print("Recitals",df_recitals.shape)

    # regulations
    df_regulations = pd.DataFrame()
    for author in ['commission','council','coreper']:
    # for author in ['council']:
        file = regulation_files[author]
        with open(file, 'r') as f:
            lines = [RegulationLine(txt) for txt in f.read().split('\n') if len(txt) >0]

        df_regulations = pd.concat([df_regulations, format_regulation(author,lines)])

    print("Regulations",df_regulations.shape)
    print(df_regulations.line_type.value_counts())
    df = df_regulations.copy()

    def build_order_from_bread(bread: t.Dict ) -> str:
        # {"TTL": "XII", "art": "85", "par": "3", "sub": "a"}
        order = [str(roman_to_num[bread['TTL']]).zfill(2)]
        if bread.get('cha'):
            order.append(str(bread.get('cha')).zfill(3))
        else:
            order.append('000')
        if bread.get('art'):
            order.append(str(bread.get('art')).zfill(3))
        if bread.get('par'):
            order.append(str(bread.get('par')).zfill(3))
        if bread.get('sub'):
            order.append(str(bread.get('sub')))
        # TODO add bullet points (~iii?)
        if bread.get('inp'):
            order.append('~'+str(bread.get('inp')))
        return '.'.join(order)

    # build path
    bread = {}
    current_inp = 0
    for i, d in df.iterrows():
        if d.line_type == 'section_title':
            bread = {'TTL': d.number}
        elif d.line_type == 'chapter_title':
            bread.update({'cha': d.number})
            bread.pop('art', None)
            bread.pop('par', None)
            bread.pop('sub', None)
            bread.pop('inp', None)
        elif d.line_type == 'article_title':
            bread.update({'art': d.number})
            bread.pop('par', None)
            bread.pop('sub', None)
            bread.pop('inp', None)
        elif d.line_type == 'paragraph':
            bread.update({'par': d.number})
            bread.pop('sub', None)
            current_inp = 0
            bread.pop('inp', None)
        elif d.line_type == 'subparagraph':
            bread.update({'sub': d.number})
            bread.pop('inp', None)
            # TODO check if bullet point isneatd of paragraph
        elif d.line_type == 'in_paragraph':
            bread.update({'inp': str(current_inp)})
            bread.pop('sub', None)
            current_inp +=1

        df.loc[i, 'bread'] = json.dumps(bread)
        df.loc[i, 'order'] = build_order_from_bread(bread)
