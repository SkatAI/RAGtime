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
from lines import Line, RecitalLine, AnnexLine


class Annex(object):
    # order of files is important: must get commission before ep-adopted for reconciliation
    files = {
        "commission": "./data/txt/52021-PC0206-commission/52021PC0206-annex.txt",
        "council": "./data/txt/ST-15698-2022-council/ST-15698-annex.txt",
        # 'final_four':'./data/txt/final_four/AIAct-final-four-simple-recitals.txt',
        # 'ep_adopted':'./data/txt/adopted-amendments/EP-amendments-parliament-regulation.txt',
        "coreper": "data/txt/coreper-feb2/AIA-Trilogue-Coreper20240202-annex.txt",
    }

    roman_to_num = {
        "I": 1,
        "II": 2,
        "IIa": "2a",
        "III": 3,
        "IV": 4,
        "V": 5,
        "VI": 6,
        "VII": 7,
        "VIII": 8,
        "VIIIa": "8a",
        "IX": 9,
        "IXa": "9a",
        "IXb": "9b",
        "X": 10,
        "XI": 11,
        "IXb": "11b",
        "IXc": "11c",
        "XII": 12,
    }
    letters_to_num = {"A": 1, "B": 2, "C": 3}

    def __init__(self, author) -> None:
        self.author = author
        self.filename = Annex.files[author]
        self.load_texts()

    def load_texts(self) -> None:
        with open(self.filename, "r") as f:
            self.texts = [txt for txt in f.read().split("\n") if len(txt) > 0]

    def process(self):
        self.format()
        self.build_bread()
        self.build_order()
        self.validate()
        self.wrapup()
        return self

    def wrapup(self):
        self.df["author"] = self.author
        self.df.sort_values(by=["order", "author"], inplace=True)
        self.df.reset_index(inplace=True, drop=True)

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

        order = [str(Annex.roman_to_num[bread["anx"]]).zfill(3)]

        if bread.get("prt"):
            order.append(
                str(Annex.roman_to_num[bread["prt"]]).zfill(2)
                # str(bread.get('prt')).zfill(2)
            )
        else:
            order.append("00")

        if bread.get("sct"):
            order.append(
                str(Annex.letters_to_num[bread["sct"]]).zfill(2)
                # str(bread.get('sct')).zfill(2)
            )
        else:
            order.append("00")

        if bread.get("art"):
            order.append(zfillnum(str(bread.get("art"))))
        if bread.get("par"):
            order.append(zfillnum(str(bread.get("par"))))
            if bread.get("pln"):
                order.append(str(bread.get("pln").zfill(2)))
            else:
                order.append("0".zfill(2))
        if bread.get("sub"):
            order.append(str(bread.get("sub")))
        if bread.get("bpt"):
            order.append(str(bread.get("bpt")))

        buff = ["---", "---", "---", "---", "--", "-", "-"]
        if len(order) < 7:
            # missing = 7 - len(order)
            order += buff[len(order) - 7 :]

        return ".".join(order)

    def build_order(self):
        for i, d in self.df.iterrows():
            order = Annex.build_order_from_bread(d.bread)
            self.df.loc[i, "order"] = order
        # single out duplicates
        current_bread_str = ""
        current_bread_count_ = 0
        for i, d in self.df[self.df.order.duplicated(keep=False)].iterrows():
            if d.bread is not None:
                bread = json.loads(d.bread)
                if current_bread_str == d.bread:
                    current_bread_count_ += 1

                else:
                    current_bread_count_ = 0
                current_bread_str = d.bread

                bread.update({"pln": str(current_bread_count_)})
                self.df.loc[i, "bread"] = json.dumps(bread)
                self.df.loc[i, "order"] = Annex.build_order_from_bread(bread)


# ------------------------------------------------------------------
#  Commission
# ------------------------------------------------------------------


class DocCommissionRegulation(Annex):
    def __init__(self, author):
        super().__init__(author)
        self.lines = [AnnexLine(txt) for txt in self.texts]

    def format(self):
        data = []
        for line in self.lines:
            data.append(
                {
                    "text": line.text,
                    "line_type": line.line_type,
                    "number": line.number,
                }
            )
        self.df = pd.DataFrame(data)

    def build_bread(self):
        bread = {}
        current_par_line = 0
        for i, d in self.df.iterrows():
            if d.line_type == "section_title":
                bread = {"TTL": d.number}
            elif d.line_type == "annex_title":
                bread = {"anx": d.number}
            elif d.line_type == "annex_part":
                bread.update({"prt": d.number})
                bread.pop("sct", None)
                bread.pop("art", None)
                bread.pop("par", None)
                bread.pop("sub", None)
                bread.pop("pln", None)
                bread.pop("bpt", None)
            elif d.line_type == "annex_section":
                bread.update({"sct": d.number})
                bread.pop("prt", None)
                bread.pop("art", None)
                bread.pop("par", None)
                bread.pop("sub", None)
                bread.pop("pln", None)
                bread.pop("bpt", None)
            elif d.line_type == "chapter_title":
                bread.update({"cha": d.number})
                bread.pop("art", None)
                bread.pop("par", None)
                bread.pop("sub", None)
                bread.pop("pln", None)
                bread.pop("bpt", None)
            elif d.line_type == "article_title":
                bread.update({"art": d.number})
                bread.pop("par", None)
                bread.pop("sub", None)
                bread.pop("pln", None)
                bread.pop("bpt", None)
            elif d.line_type == "paragraph":
                current_par_line = 0
                bread.update({"par": d.number})
                bread.update({"pln": str(current_par_line)})
                bread.pop("sub", None)
                bread.pop("bpt", None)
            elif d.line_type == "subparagraph":
                bread.update({"pln": str(current_par_line)})
                bread.update({"sub": d.number})
                bread.pop("bpt", None)
            elif d.line_type == "bulletpoint":
                bread.update({"bpt": d.number})
                bread.update({"pln": str(current_par_line)})
                bread.pop("inp", None)
            elif d.line_type == "in_paragraph":
                current_par_line += 1
                bread.update({"pln": str(current_par_line)})
                bread.pop("sub", None)

            self.df.loc[i, "bread"] = json.dumps(bread)

    def validate(self):
        missorder = []
        for i, j in zip(self.df.index, self.df.sort_values(by="order").index):
            if i != j:
                missorder.append((i, j))
        # assert len(missorder) == 0, f"{len(missorder)} in missorder\n{missorder[:10]}"
        if len(missorder) > 0:
            print(f"!! {len(missorder)} in missorder\n{missorder[:10]}")


# ------------------------------------------------------------------
#  Coreper
# ------------------------------------------------------------------


class DocCoreperRegulation(DocCommissionRegulation):
    def __init__(self, author):
        super().__init__(author)
        self.lines = [AnnexLine(txt) for txt in self.texts]

    def validate(self):
        pass


if __name__ == "__main__":
    data = pd.DataFrame()

    author = "commission"
    print("==", author)
    com = DocCoreperRegulation(author)
    com.process()
    data = pd.concat([data, com.df])

    author = "council"
    print("==", author)
    cnl = DocCoreperRegulation(author)
    cnl.process()

    data = pd.concat([data, cnl.df])

    author = "coreper"
    print("==", author)
    cor = DocCoreperRegulation(author)
    cor.process()

    data = pd.concat([data, cor.df])

    data.fillna("", inplace=True)
    data.sort_values(by=["order", "author"], inplace=True)
    data.reset_index(inplace=True, drop=True)

    output_file_json = "./data/rag/annex-20240220.json"
    with open(output_file_json, "w", encoding="utf-8") as f:
        data.to_json(f, force_ascii=False, orient="records", indent=4)
