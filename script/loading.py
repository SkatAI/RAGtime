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

# documents
from dataclasses import dataclass, field
from typing import List

from langchain.docstore.document import Document

@dataclass
class JsonDocument:
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
    docs: list[JsonDocument] = field(init=False)

    def __post_init__(self):
        self.docs = self.load_documents()

    def load_documents(self) -> List[JsonDocument]:
        with open(self.filename, 'r') as file:
            json_data = json.load(file)
        print(f"loaded {len(json_data)} docs")
        return [JsonDocument(**doc) for doc in json_data]

    def find(self,uuid) -> JsonDocument:
        for doc in self.docs:
            if doc.uuid == uuid:
                return doc

    def uuids(self) -> List[str]:
        return [d.uuid for d in self.docs]

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

    def __post_init__(self) -> None:
        pass

    def valid(self) -> bool:
        return (not self.header) & (len(self.path) > 1)

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

    def get_titles(self) -> List[str]:
        return list(set([snip.path for snip in self.items]))

    def find_by_title(self, title: str) -> List[Snip]:
        return [ item for item in self.items if( item.path == title ) & (not item.header )]

@dataclass
class Chunk:
    snip_list: List[Snip]
    text: str = field(init = False)
    title: str  = field(init = False)
    document_uuid: str = field(init = False)

    def __post_init__(self) -> None:
        self.get_text()
        self.get_title()
        self.get_document_uuid()

    def get_text(self) -> None:
        self.text = '\n'.join( [ item.text for item in self.snip_list  ]  )

    def get_title(self) -> None:
        # title
        titles = list(set([ item.path for item in self.snip_list  ]))
        assert len(titles) < 2, titles
        self.title = titles[0]

    def get_document_uuid(self) -> None:
        uuids = list(set([ item.document_uuid for item in self.snip_list  ]))
        assert len(uuids) == 1, uuids
        self.document_uuid = uuids[0]


@dataclass
class Chunks:
    snips: Snips
    chunks: List[Chunk] = field(init = False)

    def __post_init__(self):

        self.chunks = []
        for title in self.snips.get_titles():
            snip_list = self.snips.find_by_title(title)
            if len(snip_list) >0:
                chunk = Chunk(snip_list)
                self.chunks.append(chunk)

    def to_langchain_documents(self, max_documents : int ) -> List[Document]:
        documents = []
        for chunk  in self.chunks:
            documents.append(
                Document(
                    page_content='\n'.join([chunk.title, chunk.text]),
                    metadata={'document_uuid': chunk.document_uuid}
                )
            )
        if max_documents is not None:
            documents = random.sample(documents, max_documents)
        return documents



if __name__ == "__main__":

    documents_filename = 'data/json/documents.json'
    document_path = 'data/json/'

    files = glob.glob(os.path.join(document_path, '*.json'))
    files.pop( files.index(documents_filename)    )

    snips = Snips(files)

    chunks = Chunks(snips)

    chunks.to_langchain_documents(max_documents=10)