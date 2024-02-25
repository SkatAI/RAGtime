"""
One shot scriptß
gets files from bucket
ingest into db
"""

import os, re, json
import pandas as pd

pd.options.display.max_columns = 100
pd.options.display.max_rows = 60
pd.options.display.max_colwidth = 100
pd.options.display.precision = 10
pd.options.display.width = 160
pd.set_option("display.float_format", "{:.2f}".format)
import numpy as np
from tqdm import tqdm

from sqlalchemy import create_engine
import sys

sys.path.append("./script")
from db_utils import Database

sys.path.append("./streamlitapp")
from google_storage_utils import StorageWrap


if __name__ == "__main__":
    if True:
        sw = StorageWrap()
        buckets = sw.list_buckets()
        print(buckets)
        sw.set_bucket("ragtime-ai-act")
        blobs = [blb for blb in sw.bucket.list_blobs(prefix="sessions")]
        df = []
        for blob in tqdm(blobs):
            df.append(json.loads(blob.download_as_string(client=None)))

        df = pd.DataFrame(df)

    # df = data.copy()

    df["query"] = df["query"].apply(lambda d: d.strip())
    df["search"] = df["search"].apply(lambda d: json.dumps(d))

    def split_context(context):
        uuids = context["uuids"].split(",")
        context["uuids"] = [id.strip() for id in uuids]
        titles = context["titles"].split(",")
        context["titles"] = [txt.strip() for txt in titles]
        return context

    df["context"] = df["context"].apply(lambda d: split_context(d))
    df["context"] = df["context"].apply(lambda d: json.dumps(d))
    df["answer_type"] = ""
    data = []
    for i, d in df.iterrows():
        item = d.copy()
        item.update({"answer": d["answer"]["answer_with_context"], "answer_type": "contextual"})
        data.append(item)
        if d["answer"]["answer_bare"] != "":
            item = d.copy()
            item.update({"answer": d["answer"]["answer_bare"], "answer_type": "no-context"})
            data.append(item)

    data = pd.DataFrame(data)
    data.reset_index(inplace=True, drop=True)

    def set_filters(txt):
        if txt is not None:
            return json.dumps({"document": txt})
        else:
            return ""

    data["filters"] = data.author.apply(lambda txt: set_filters(txt))

    data.rename(columns={"date": "created_at"}, inplace=True)
    data = data[["query", "answer", "search", "filters", "context", "answer_type", "created_at"]].copy()

    # data.to_csv('./data/live_questions_20240224.csv', index = False, quoting = csv.QUOTE_ALL)
    # TODO get into db

    db = Database()
    data.to_sql(name="live_qa", con=db.engine, if_exists="append", index=False)
    db.close()
