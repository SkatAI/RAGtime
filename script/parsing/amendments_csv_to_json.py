"""
# ECR	European Conservatives and Reformists Group
# EPP	Group of the European Peoples Party (Christian Democrats)
# Greens/EFA	Group of the Greens/European Free Alliance
# GUE/NGL	The Left group in the European Parliament - GUE/NGL
# ID	Identity and Democracy Group
# Renew	Renew Europe Group
# S&D	Group of the Progressive Alliance of Socialists and Democrats in the European Parliament

# CULT	Committee on Culture and Education
# IMCO-LIBE	Committee on the Internal Market and Consumer Protection Committee on Civil Liberties, Justice and Home Affairs
# ITRE	Committee on Industry, Research and Energy
# JURI	Committee on Legal Affairs
# TRAN	Committee on Transport and Tourism
"""

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

committees = {
    "Committee on Transport and Tourism": "TRAN",
    "Committee on Legal Affairs": "JURI",
    "Committee on Industry, Research and Energy": "ITRE",
    "Committee on Culture and Education": "CULT",
    "Committee on the Internal Market and Consumer Protection\nCommittee on Civil Liberties, Justice and Home Affairs": "IMCO-LIBE",
}

political_groups = {
    "European Conservatives and Reformists Group": "ECR",
    "Group of the European Peoples Party (Christian Democrats)": "EPP",
    "Group of the Greens/European Free Alliance": "Greens/EFA",
    "The Left group in the European Parliament - GUE/NGL": "GUE/NGL",
    "Identity and Democracy Group": "ID",
    "Renew Europe Group": "Renew",
    "Group of the Progressive Alliance of Socialists and Democrats in the European Parliament": "S&D",
}

if __name__ == "__main__":
    # ----------------------------------------------------------------------
    # committee
    # ----------------------------------------------------------------------

    csv_ = "/Users/alexis/Google Drive/My Drive/SkatAI/SkatAI projects/RAG-AI-act/data/amendments_committees.csv"
    data = pd.read_csv(csv_)

    cols = {
        "Amendment Number": "amendment_number",
        "Document Type": "document_type",
        "Numbering": "title",
        "Text Proposed by the Commission": "commission",
        "Amendment Text": "text",
        "ID": "id",
        "Group": "author",
    }

    data.rename(columns=cols, inplace=True)
    data.drop(columns=["document_type", "commission", "id"], inplace=True)

    data["uuid"] = [str(uuid.uuid4()) for n in range(len(data))]

    # ----------------------------------------------------------------------
    # clean up title and text
    # ----------------------------------------------------------------------
    # rm footer with docx ref
    # AD\1262500EN.docx 5/74 PE719.827v02-00 EN
    # PE719.827v02-00 6/74 AD\1262500EN.docx EN
    # text = "Consistently with PE719.637v02-00 12/42 AD\1258237EN.docx EN the objectives of Union harmonisation legislation to facilitate the free movement"

    print(data[data.text.str.contains(".docx")].shape, "rows contains .docx refs")

    tokens = [
        ("PE719", " EN"),
        ("PE731", " EN"),
        ("PR\\\\12", " EN"),
        ("AD\\\\12", " EN"),
        ("AD\\\\12", "9/49"),
        ("AD\\\\12", "25/42"),
        ("PR\\\\12", "19/161"),
        ("PR\\\\12", "23/161"),
    ]
    for token in tokens:
        rgx = token[0] + ".*?" + ".docx" + ".*?" + token[1]
        data["text"] = data["text"].apply(lambda txt: re.sub(rgx, " ", txt).strip())
        print(data[data.text.str.contains(".docx")].shape, "text rows contains .docx refs")

    for token in tokens:
        rgx = token[0] + ".*?" + ".docx" + ".*?" + token[1]
        data["title"] = data["title"].apply(lambda txt: re.sub(rgx, " ", txt).strip())
        print(
            data[data.title.str.contains(".docx")].shape,
            "title rows contains .docx refs",
        )

    # long titles
    # data['len_'] = data.title.apply(len)
    for token in ["Directive", "Regulation"]:
        cond = data.title.str.contains(token)
        print(data[cond].shape, "title rows contains:", token)

        for i, d in data[cond].iterrows():
            data.loc[i, "title"] = d.title.split(token)[0].strip()
        print(data[cond].shape, "title rows contains:", token)

    # specific titles
    data.loc[140, "title"] = "Annex III – paragraph 1 – point 2 – point a"
    data.loc[720, "title"] = "Annex III – paragraph 1 – point 8 – point a a (new)"
    data.loc[721, "title"] = "Annex IV – paragraph 1 – point 1"
    data.loc[693, "title"] = "Article 68 a (new)"

    # rm consecutive spaces from cols 3 to 7
    rgx = r"\s+"
    data["text"] = data["text"].apply(lambda txt: re.sub(rgx, " ", txt).strip())

    rgx = r"\\\\uf0b7"
    data["text"] = data["text"].apply(lambda txt: re.sub(rgx, " ", txt).strip())

    # rm numbers glued to words
    rgx = r"\b([a-z]+)\d{1,2}\b"
    data["text"] = data["text"].apply(lambda txt: re.sub(rgx, r"\1", txt).strip())

    # data author
    data["author"] = data.author.apply(lambda d: committees[d])

    data["amendment_number"] = data.amendment_number.apply(lambda d: int(d.split(" ")[1]))

    cols = ["uuid", "amendment_number", "author", "title", "text"]
    data = data[cols].copy()
    output_file_json = "./data/json/amendments_committees-2024-02-09.json"
    with open(output_file_json, "w", encoding="utf-8") as f:
        data.to_json(f, force_ascii=False, orient="records", indent=4)

    # ----------------------------------------------------------------------
    # political groups
    # ----------------------------------------------------------------------

    csv_ = "/Users/alexis/Google Drive/My Drive/SkatAI/SkatAI projects/RAG-AI-act/data/amendments_political_groups.csv"
    data = pd.read_csv(csv_)
    cols = {
        "number": "amendment_number",
        "proposers": "proposers",
        "title": "title",
        "Text proposed by the Commission": "commission",
        "amendment": "text",
        "group": "author",
    }

    data.rename(columns=cols, inplace=True)
    # Nulls
    data.fillna(value={"commission": "", "text": ""}, inplace=True)

    data["uuid"] = [str(uuid.uuid4()) for n in range(len(data))]

    rgx = r"\s+"
    data["text"] = data["text"].apply(lambda txt: re.sub(rgx, " ", txt).strip())

    # rm numbers glued to words
    rgx = r"\b([a-z]+)\d{1,2}\b"
    data["text"] = data["text"].apply(lambda txt: re.sub(rgx, r"\1", txt).strip())

    # data author
    data["author"] = data.author.apply(lambda d: political_groups[d])

    cols = [
        "uuid",
        "amendment_number",
        "author",
        "proposers",
        "title",
        "commission",
        "text",
    ]
    data = data[cols].copy()
    output_file_json = "./data/json/amendments_political_groups-2024-02-09.json"
    with open(output_file_json, "w", encoding="utf-8") as f:
        data.to_json(f, force_ascii=False, orient="records", indent=4)
