'''
Loading jsonl from documents
using dataclasses
'''
import os, re, json, glob
import pandas as pd
from tqdm import tqdm
pd.options.display.max_columns = 160
pd.options.display.max_rows = 60
pd.options.display.max_colwidth = 160
pd.options.display.precision = 10
pd.options.display.width = 160
pd.set_option("display.float_format", "{:.4f}".format)
import numpy as np
import random
random.seed(800)

docs_concatenate = 2

# documents
from dataclasses import dataclass, field
from typing import List

@dataclass
class Document:
    id: int
    uuid: str
    refs: List[str]
    urls: List[str]
    title: str
    subtitle: str
    description: str
    date_published: str # datetime.date
    issuer: str
    related: List[str]
    lang: List[str]
    format: str

    def __post_init__(self):
        self.footer = f"Author: {self.issuer}, {self.date_published}"

@dataclass
class Documents:
    filename: str
    docs: list[Document] = field(init=False)

    def __post_init__(self):
        self.docs = self.load_documents()

    def load_documents(self) -> List[Document]:
        with open(self.filename, 'r') as file:
            json_data = json.load(file)  # Use json.load for files, json.loads for strings.
        print(f"loaded {len(json_data)} docs")
        return [Document(**doc) for doc in json_data]

    def find(self,uuid) -> Document:
        for doc in self.docs:
            if doc.uuid == uuid:
                return doc

    def uuids(self) -> List[str]:
        return [d.uuid for d in docs]

@dataclass
class Snip():
    document_uuid:str
    document_section:str
    document_section_number:int
    type:str
    id:str
    uuid:str
    path:str
    header:bool
    text:str
    belongs_to: Document = field(init = False)

    def __post_init__(self):
        # find the parent document
        # self.belongs_to =
        pass



@dataclass
class Snips:
    filenames: List[str]
    items: List[Snip] = field(init = False)

    def __post_init__(self) -> None:
        self.items = self.load()

    def load(self) -> List[Snip]:
        snips = []
        for filename in self.filenames:
            with open(filename, 'r') as file:
                json_data = json.load(file)
            snips += [Snip(**snip) for snip in json_data]
            print(f"loaded {len(json_data)} snips from {filename}. total : {len(snips)}")

        return snips

    def get_documents(self,documents:Documents) -> List[str]:
    # def get_document_uuids(self) -> List[str]:
        document_uuids = list(set([ snip.document_uuid for snip in self.items  ]))
        return  [documents.find(uuid).footer for uuid in document_uuids]

if __name__ == "__main__":

    documents_filename = 'data/json/documents.json'

    document_path = 'data/json/'
    files = glob.glob(os.path.join(document_path, '*.json'))
    files.pop( files.index(documents_filename)    )

    snips = Snips(files)
    docs = Documents(documents_filename)
    print(snips.get_documents(docs))


    # Number of concatenated consecutive paragraphs

    # chunks = []
    # for doc_name in docu_names:
    #     data = pd.read_json(doc_name)

    #     headers = data.path.unique()
    #     for header in headers:
    #         # don't want simple headers
    #         cond = (data.path == header) & (~data.header)

    #         if data[cond].shape[0] > 0:
    #             for k in range(0, data[cond].shape[0], docs_concatenate):
    #                 end_ = min(data[cond].shape[0], k+docs_concatenate)
    #                 chunks.append('\n'.join([ header] + list(data[cond][k: end_].text.values) + [footer] ))


