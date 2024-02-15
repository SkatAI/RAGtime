'''
Create unique dataframe that includes all text versions from
- commission
- council
- final four
- ep adopted
- coreper
start with recital

TODO: refactor with classes for each types of document

TODO: ingest data/txt/adopted-amendments/EP-amendments-parliament-regulation.txt
TODO: add markup to final four regulation
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
pd.options.display.max_colwidth = 50
pd.options.display.precision = 10
pd.options.display.width = 220
pd.set_option("display.float_format", "{:.2f}".format)
import numpy as np
import typing as t
from regex_utils import Rgx
from lines import Line, RecitalLine, RegulationLine
from reconcile_regulation import DocCommissionRegulation


# build path
def build_bread(df: pd.DataFrame) -> pd.DataFrame:
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
    return df



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
    lines = [RegulationLine(txt) for txt in texts]
    data = []
    for line in lines:
        data.append({
                'text': line.text,
                'line_type': line.line_type,
                'number': line.number,
            })
    return pd.DataFrame(data)

# def parse_loc(text):
#     art, par, sub, line_type = None, None, None, None
#     bread = { }
#     rgx = r"^loc: Article (\d+[a-z]*).*$"
#     match = re.search(rgx,text)
#     if match:
#         art = match.group(1).strip()
#         bread = { 'art': art}
#         line_type = 'article_title'

#     rgx = r"^loc: Article \d+[a-z]* - paragraph (\d+[a-z]*).*$"
#     match = re.search(rgx,text)
#     if match:
#         par = match.group(1).strip()
#         bread.update({'par': par })
#         line_type = 'paragraph'

#     rgx = r"^loc: Article (\d+[a-z]*) - paragraph (\d+[a-z]*)\s*-\s*point\s*(\d*[a-z]*).*$"
#     match = re.search(rgx,text)
#     if match:
#         sub = match.group(3).strip()
#         bread.update({'sub': sub})
#         line_type = 'subparagraph'

#     # specific for article 3:
#     rgx = r"^loc: Article 3 - paragraph 1\s*-\s*point\s*(\d*[a-z]*).*$"
#     match = re.search(rgx,text)
#     if match:
#         par = match.group(1).strip()
#         bread = { 'art': '3', 'par': par}
#         line_type = 'paragraph'

#     return bread, line_type


# def format_regulation_ep_adopted(author: str,texts: t.List) -> pd.DataFrame :
#     data = []
#     item = {}
#     current_amendment = ""
#     current_location = ""
#     lines = [Line(txt) for txt in texts]
#     for line in lines:
#         if line.starts_with("Amendment"):
#             current_amendment = line.text
#             current_location = ""
#             item = {
#                 'line_type': 'amendment',
#                 'amendment': line.text,
#                 'number': '',
#                 'text': line.text,
#                 'loc': current_location,
#             }
#         elif line.starts_with("loc"):
#             current_location = line.text.replace('loc: ', '')
#             item.update({
#                 'line_type': 'loc',
#                 'amendment': current_amendment,
#                 'text': line.text.replace('loc: ', ''),
#                 'loc': current_location,
#             })
#         elif line.has_text():
#             line.get_line_type()
#             item.update({
#                 'line_type': line.line_type,
#                 'amendment': current_amendment,
#                 'number': '',
#                 'number': line.number,
#                 'text': line.text,
#                 'loc': current_location,
#             })
#         data.append(item.copy())

#     df = pd.DataFrame(data)
#     return df



line_type_map = {'section_title': 'TTL', 'chapter_title': 'cha','article': 'art', 'article_title':'art', 'paragraph': 'par', 'subparagraph': 'sub', 'bulletpoint': 'bpt', 'in_paragraph': 'inp'}
# line_type_map = { v:k for k,v in  line_type_map.items()   }

# def build_bread_from_location(item: pd.Series) -> t.Optional[dict]:
#     # from line.text and location, builds bread
#     # 1st looks at line type from the line then adds info from location

#     if item.line_type in line_type_map.keys():
#         # init from line_type and number
#         bread = { line_type_map[item.line_type]: item.number, }

#         # extract whatever info is in location
#         locline = Line(item['loc'])
#         art = locline.extract_article_title_number()
#         par = locline.extract_paragraph_number_from_loc()
#         sub = locline.extract_subparagraph_number_from_loc()

#         # update bread with missing info found in location
#         if item.line_type == 'paragraph':
#                     bread.update({
#                         'art': art,
#                     })
#         elif item.line_type == 'subparagraph':
#                     bread.update({
#                         'art': art,
#                         'par': par,
#                     })
#         elif item.line_type == 'bulletpoint':
#                     bread.update({
#                         'art': art,
#                         'par': par,
#                         'sub': sub,
#                     })
#         elif item.line_type == 'in_paragraph':
#                     bread.update({
#                         'art': art,
#                         'par': par,
#                     })
#         return bread
#     else:
#         return None


class Document(object):

    def __init__(self, author, filename) -> None:
        self.author = author
        self.filename = filename

    def load_texts(self) -> None:
        with open(self.filename, 'r') as f:
            self.texts = [txt for txt in f.read().split('\n') if len(txt) >0]

    def format(self) -> None:
        pass



if __name__ == "__main__":

    author = 'commission'
    df = DocCommission(regulation_files[author]).process()
    print(df.head())




    author = 'ep_adopted'
    doc = DocEpAdopted(author, regulation_files[author])
    doc.format()
    doc.build_bread()
    doc.validate()

    # regulations
    dfreg = pd.DataFrame()

    for author in regulation_files.keys():
        file = regulation_files[author]
        with open(file, 'r') as f:
            texts = [txt for txt in f.read().split('\n') if len(txt) >0]


            # check anomalies in bread
            anomalies =[]
            for i, d in df.iterrows():
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
            print(df.line_type.value_counts())
            df['author'] = author
            df = df[~df.line_type.isin(['loc', 'amendment'])].copy()
            df.reset_index(inplace = True, drop = True)
            df.drop(columns = ['loc'], inplace = True )
            dfreg = pd.concat([dfreg, df])

            df.sort_values(by = ['order', 'author'], inplace = True)
            df.reset_index(inplace = True, drop = True)

            dfreg = pd.concat([dfreg, df])

    dfreg.fillna('', inplace = True)


    # recitals
    df_recitals = pd.DataFrame()
    for author in ['commission','council','final_four','ep_adopted','coreper']:
        file = Document.recital_files[author]
        with open(file, 'r') as f:
            texts = [txt for txt in f.read().split('\n')]

        lines = [RecitalLine(txt) for txt in texts  if len(txt) >0]

        df_recitals = pd.concat([df_recitals, format_recital(author,lines)])
    df_recitals.sort_values(by = ['number','author'], inplace = True)
    df_recitals.reset_index(inplace = True, drop = True)

    print("Recitals",df_recitals.shape)

