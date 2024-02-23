# TODO TITLE VIIIA comes between TITLE IV and TITLE V but with article 52a. must force TTL order on this chapter


import os, re, json, glob
import time, datetime
from datetime import timedelta
import pandas as pd
import argparse
from tqdm import tqdm
pd.options.display.max_columns = 120
pd.options.display.max_rows = 60
pd.options.display.precision = 10
pd.options.display.max_colwidth = 100
pd.options.display.width = 200
pd.set_option("display.float_format", "{:.2f}".format)
import numpy as np
import typing as t
from regex_utils import Rgx
from lines import Line, RecitalLine, RegulationLine

class Regulation(object):
    # order of files is important: must get commission before ep-adopted for reconciliation
    files = {
        'commission':'./data/txt/52021-PC0206-commission/52021PC0206-regulation.txt',
        'council':'./data/txt/ST-15698-2022-council/ST-15698-regulation.txt',
        # 'final_four':'./data/txt/final_four/AIAct-final-four-simple-recitals.txt',
        # 'ep_adopted':'./data/txt/adopted-amendments/EP-amendments-parliament-regulation.txt',
        'coreper':'data/txt/coreper-feb2/AIA-Trilogue-Coreper20240202-regulation.txt',
    }

    roman_to_num = {'I': 1, 'IA': '001~a', 'II': 2, 'III': 3, 'IV': 4,'V': 5, 'VI': 6, 'VII': 7, 'VIII': 8,'VIIIA': '008~a','IX': 9, 'X': 10, 'XI': 11, 'XII': 12}

    def __init__(self, author) -> None:
        self.author = author
        self.filename = Regulation.files[author]
        self.load_texts()

    def load_texts(self) -> None:
        with open(self.filename, 'r') as f:
            self.texts = [txt for txt in f.read().split('\n') if len(txt) >0]

    def process(self):
        self.format()
        self.build_bread()
        self.build_order()
        self.validate()
        self.wrapup()
        return self

    def wrapup(self):
        self.df['author'] = self.author
        self.df.sort_values(by = ['order', 'author'], inplace = True)
        self.df.reset_index(inplace = True, drop = True)

    @classmethod
    def build_order_from_bread(cls, bread):
        if bread is None:
            return None
        def zfillnum(txt: str) -> t.Optional[str]:
            rgx = r"([-]{0,1})(\d+)([a-z]{0,2})"
            match = re.search(rgx, txt)
            if match:
                sign = match.group(1)
                num = match.group(2).zfill(3)
                let = match.group(3)
                return f"{sign}{num}{let}"

        if isinstance(bread, str):
            bread = json.loads(bread)

        order = [str(Regulation.roman_to_num[bread['TTL']]).zfill(3)]

        if bread.get('cha'):
            order.append(zfillnum(str(bread.get('cha'))))
        else:
            order.append('000')

        if bread.get('art'):
            order.append(zfillnum(str(bread.get('art'))))
        if bread.get('par'):
            order.append(zfillnum(str(bread.get('par'))))
            if bread.get('pln'):
                order.append(str(bread.get('pln').zfill(2)))
            else:
                order.append('0'.zfill(2))
        if bread.get('sub'):
            order.append(str(bread.get('sub')))
        if bread.get('bpt'):
            order.append(str(bread.get('bpt')))
        if bread.get('inp'):
            order.append('~'+str(bread.get('inp')))

        buff = ['---','---','---','---','--', '-', '-']
        if len(order) < 7:
            # missing = 7 - len(order)
            order += buff[len(order) -7:]

        return '.'.join(order)

    def build_order(self):
        for i,d in self.df.iterrows():
            order = Regulation.build_order_from_bread(d.bread)
            # if len(order.split('.')) < 7:
            #     assert 1 == 2
            self.df.loc[i, 'order'] = order
        # single out duplicates
        current_bread_str = ''
        current_bread_count_ = 0
        for i,d in self.df[self.df.order.duplicated(keep = False)].iterrows():
            if (d.bread is not None) :
                bread = json.loads(d.bread)
                if current_bread_str == d.bread:
                    current_bread_count_ += 1

                else:
                    current_bread_count_ = 0
                current_bread_str = d.bread

                bread.update({'pln': str(current_bread_count_) })
                self.df.loc[i, 'bread'] = json.dumps(bread)
                self.df.loc[i, 'order'] = Regulation.build_order_from_bread(bread)


# ------------------------------------------------------------------
#  Commission
# ------------------------------------------------------------------

class DocCommissionRegulation(Regulation):
    def __init__(self,  author):
        super().__init__( author)
        self.lines = [RegulationLine(txt) for txt in self.texts]

    def format(self):
        data = []
        for line in self.lines:
            data.append({
                    'text': line.text,
                    'line_type': line.line_type,
                    'number': line.number,
                })
        self.df = pd.DataFrame(data)

    def build_bread(self):

        bread = {}
        current_par_line = 0
        for i, d in self.df.iterrows():
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

            self.df.loc[i, 'bread'] = json.dumps(bread)


    def validate(self):
        missorder = []
        for i,j in zip(self.df.index, self.df.sort_values(by = 'order').index):
            if i != j:
                missorder.append((i,j))
        # assert len(missorder) == 0, f"{len(missorder)} in missorder\n{missorder[:10]}"
        if len(missorder) > 0:
            print(f"!! {len(missorder)} in missorder\n{missorder[:10]}")

    def extract_breads(self):
        cbrds = pd.DataFrame(list(self.df.bread.apply(json.loads)))
        cbrds.fillna('', inplace = True)
        cbrds = cbrds[['TTL', 'cha', 'art']].drop_duplicates().copy()
        return cbrds


# ------------------------------------------------------------------
#  EP Adopted
# ------------------------------------------------------------------
class DocEpadoptedRegulation(Regulation):
    line_type_map = {'section_title': 'TTL', 'chapter_title': 'cha','article': 'art', 'article_title':'art', 'paragraph': 'par', 'subparagraph': 'sub', 'bulletpoint': 'bpt', 'in_paragraph': 'inp'}
    def __init__(self, author, commission_breads):
        super().__init__(author)
        self.commission_breads = commission_breads
        self.lines = [Line(txt) for txt in self.texts]

    def format(self) -> None:
        data = []
        item = {}
        current_amendment, current_title = "", ""

        for line in self.lines:
            if line.starts_with("Amendment"):
                current_amendment = line.text
                current_title = ""
                item = {
                    'line_type': 'amendment',
                    'amendment': line.text,
                    'number': '',
                    'text': line.text,
                    'title': current_title,
                }
            elif line.starts_with("loc"):
                current_title = line.text.replace('loc: ', '')
                item.update({
                    'line_type': 'title',
                    'amendment': current_amendment,
                    'text': line.text.replace('loc: ', ''),
                    'title': current_title,
                })
            elif line.has_text():
                line.get_line_type()
                item.update({
                    'line_type': line.line_type,
                    'amendment': current_amendment,
                    'number': '',
                    'number': line.number,
                    'text': line.text,
                    'title': current_title,
                })
            data.append(item.copy())

        self.df = pd.DataFrame(data)

    @classmethod
    def build_bread_from_title(cls, item: pd.Series) -> t.Optional[dict]:
        # from line.text and title, builds bread
        # 1st looks at line type from the line then adds info from title

        if item.line_type in DocEpadoptedRegulation.line_type_map.keys():
            # init from line_type and number
            bread = { DocEpadoptedRegulation.line_type_map[item.line_type]: item.number, }

            # extract whatever info is in title
            titleline = Line(item['title'])
            art = titleline.extract_article_title_number()
            par = titleline.extract_paragraph_number_from_title()
            sub = titleline.extract_subparagraph_number_from_title()

            # update bread with missing info found in title
            if item.line_type == 'paragraph':
                        bread.update({
                            'art': art,
                        })
            elif item.line_type == 'subparagraph':
                        bread.update({
                            'art': art,
                            'par': par,
                        })
            elif item.line_type == 'bulletpoint':
                        bread.update({
                            'art': art,
                            'par': par,
                            'sub': sub,
                        })
            elif item.line_type == 'in_paragraph':
                        bread.update({
                            'art': art,
                            'par': par,
                        })
            return json.dumps(bread)
        else:
            return None

    def consolidate_bread(self):
        # second pass: get missing info from previous bread
        prev_bread = {}
        current_inpar = 0
        for i, d in self.df.iterrows():
            if (d.bread is not None) & (prev_bread is not None):
                bread = json.loads(d.bread)
                if (d.line_type == 'paragraph') & (bread.get('art') is None)  & (prev_bread.get('art') is not None):
                    bread.update({'art': prev_bread['art']})
                if (d.line_type == 'subparagraph') & (bread.get('art') is None)  & (prev_bread.get('art') is not None):
                    bread.update({'art': prev_bread['art']})
                if (d.line_type == 'subparagraph') & (bread.get('par') is None)  & (prev_bread.get('par') is not None):
                    bread.update({'par': prev_bread['par']})
                if (d.line_type == 'bulletpoint') & (bread.get('sub') is None) & (prev_bread.get('sub') is not None):
                    bread.update({'sub': prev_bread['sub']})
                if (d.line_type == 'bulletpoint') & (bread.get('par') is None) & (prev_bread.get('par') is not None):
                    bread.update({'par': prev_bread['par']})
                if (d.line_type == 'in_paragraph') & (bread.get('par') is None) & (prev_bread.get('par') is not None):
                    bread.update({'par': prev_bread['par']})
                if (d.line_type == 'in_paragraph') & ((bread.get('inp') is None) | (bread.get('inp') == '')) :

                    bread.update({'inp': str(current_inpar)})
                if d.line_type != 'in_paragraph':
                    current_inpar = 0
                else:
                    current_inpar +=1

                self.df.loc[i, 'bread'] = json.dumps(bread)
                prev_bread = bread

    def bread_import_titles(self):
        for i, d in self.df.iterrows():
            if d.bread is not None:
                bread = json.loads(d.bread)
                # get TTL from commission_breads article
                if bread is not None:
                    if bread.get('art') is not None:
                        match = re.search( r'(\d+)' , bread.get('art'))
                        art = match.group(1)

                    if (bread.get('TTL') is None):
                        ttls = list(self.commission_breads[self.commission_breads.art == art].TTL.unique())
                        assert len(ttls) == 1
                        bread.update({"TTL": ttls[0]})
                    if (bread.get('cha') is None):
                        chas = list(self.commission_breads[self.commission_breads.art == art].cha.unique())
                        assert len(chas) == 1
                        bread.update({"cha": chas[0]})
                self.df.loc[i, 'bread'] = json.dumps(bread)


    def build_bread(self) -> None:
        self.df['bread'] = self.df.apply(DocEpadoptedRegulation.build_bread_from_title, axis = 1)
        self.consolidate_bread()
        self.bread_import_titles()

    def validate(self):
        anomalies =[]
        for i, d in self.df.iterrows():
            if d.bread is not None:
                bread = json.loads(d.bread)
                if bread is not None:
                    if (d.line_type == 'art') & (sorted(bread.keys()) != sorted(['TTL', 'cha','art'])  ):
                        anomalies.append((i,bread))
                    elif (d.line_type == 'par') & (sorted(bread.keys()) != sorted(['TTL', 'cha','art','par'])):
                        anomalies.append((i,bread))
                    elif (d.line_type == 'sub') & (sorted(bread.keys()) != sorted(['TTL', 'cha','art','par','sub'])):
                        anomalies.append((i,bread))
                    elif (d.line_type == 'bpt') & (sorted(bread.keys()) != sorted(['TTL', 'cha','art','bpt','par','sub'])):
                        anomalies.append((i,bread))
                    elif (d.line_type == 'inp') & (sorted(bread.keys()) != sorted(['TTL', 'cha','art','bpt','inp','par','sub'])):
                        anomalies.append((i,bread))
                    if any([v is None for k,v in bread.items()]):
                        anomalies.append((i,bread))
                    if any([v == '' for k,v in bread.items() if k != 'cha']):
                        anomalies.append((i,bread))
        assert len(anomalies) == 0, f"{len(anomalies)} anomalies: \n{anomalies[:10]}"

    def wrapup(self):
        self.df['author'] = self.author
        self.df = self.df[~self.df.line_type.isin(['title','amendment'])].copy()
        self.df.sort_values(by = ['order', 'author'], inplace = True)
        self.df.reset_index(inplace = True, drop = True)

# ------------------------------------------------------------------
#  Coreper
# ------------------------------------------------------------------

class DocCoreperRegulation(DocCommissionRegulation):
    def __init__(self,  author):
        super().__init__( author)
        self.lines = [RegulationLine(txt) for txt in self.texts]

    def validate(self):
        pass

if __name__ == "__main__":

    data = pd.DataFrame()

    author = 'coreper'
    print("==", author)
    cor = DocCoreperRegulation(author).process()
    # cor.format()
    # cor.build_bread()
    # cor.build_order()
    # cor.validate()


    data = pd.concat([data, cor.df])

    author = 'commission'
    print("==", author)
    com = DocCommissionRegulation(author).process()
    com.df['author'] = author
    commission_breads = com.extract_breads()

    data = pd.concat([data, com.df])

    author = 'council'
    print("==", author)
    cnl = DocCommissionRegulation(author).process()

    data = pd.concat([data, cnl.df])

    if False:
        # ep_adopted are not included in the rag data
        author = 'ep_adopted'
        print("==", author)
        epa = DocEpadoptedRegulation(author, commission_breads).process()
        data = pd.concat([data, epa.df])

    data.fillna('', inplace = True)
    data.sort_values(by = ['order', 'author'], inplace = True)
    data.reset_index(inplace = True, drop = True)

    output_file_json = "./data/rag/regulation-20240220.json"
    with open(output_file_json, "w", encoding="utf-8") as f:
        data.to_json(f, force_ascii=False, orient="records", indent=4)
