"""
loads amendments committees and political groups

'amd_title': title from the amendment
'tgt_title': title found in final four data
'certainty': score
'match': boolean match if above threshold
'amd_uuids': amendments with same amd_title title => different groups, committees and multiple amendments by same entity
'tgt_uuid': uuid of the found title in final four data
'tgt_vvids': items with same uuid in final four data


"""
import os, re, json, glob
from datetime import timedelta
import pandas as pd
from tqdm import tqdm

pd.options.display.max_columns = 100
pd.options.display.max_rows = 60
pd.options.display.max_colwidth = 100
pd.options.display.precision = 10
pd.options.display.width = 160
pd.set_option("display.float_format", "{:.4f}".format)
import argparse
import numpy as np
import typing as t

# Local
import sys

sys.path.append("./script")
from weaviate_utils import *

# weaviate
import weaviate
import weaviate.classes as wvc
from weaviate.classes import Filter


def closest(title: str, num: int) -> t.List[weaviate.collections.classes.internal.Object]:
    response = collection.query.near_text(
        query=title,
        limit=num,
        # filters = Filter.by_property("author").equal('commission'),
        return_metadata=[
            "distance",
            "certainty",
            "score",
            "explain_score",
            "is_consistent",
        ],
    )
    return response.objects


def to_jsonl(data: t.List, filename: str) -> None:
    with open(filename, "a") as file:
        for item in data:
            json_str = json.dumps(item, indent=4)
            file.write(json_str + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", help="start")
    parser.add_argument("--step", help="step", default=500)
    args = parser.parse_args()

    start = int(args.start)
    end_ = start + int(args.step)
    print(f"{start} - {end_}")

    client = connect_client(location="local")

    # ----------------------------------------------------------------
    # titles
    # ----------------------------------------------------------------

    collection_name = "AIAct_FF_titles_01"
    collection = client.collections.get(collection_name)

    # ----------------------------------------------------------------
    # Match
    # ----------------------------------------------------------------
    input_file = "./data/json/final_four_author-2024-02-06.json"
    regl = pd.read_json(input_file)

    input_file = "./data/json/amendments_political_groups-2024-02-09.json"
    amd = pd.read_json(input_file)

    match_threshold = 0.96
    data = []
    tgt_cols = [
        "vvid",
        "uuid",
        "section",
        "title",
        "author",
        "text",
        "pdf_order",
        "regulation_title",
        "level",
    ]
    amd_titles = sorted(amd.title.unique())
    for amd_title in tqdm(amd_titles[start:end_]):
        cond = amd.title == amd_title
        amd_uuids = amd[cond].uuid.unique()
        amd_title = amd_title.replace("\u2013", "")
        item = closest(amd_title, 1)[0]
        tgt_uuid = regl[regl.vvid == str(item.properties["vvid"])].uuid.unique()[0]
        tgt_vvids = regl[(regl.uuid == tgt_uuid)].vvid.unique()
        data.append(
            {
                "amd_title": amd_title,
                "tgt_title": item.properties["title"],
                "certainty": np.round(item.metadata.certainty, 4),
                "match": item.metadata.certainty > match_threshold,
                "amd_uuids": amd_uuids.tolist(),
                "tgt_uuid": tgt_uuid,
                "tgt_vvids": tgt_vvids.tolist(),
            }
        )

    output_file_json = f"./data/json/matching/title_matching_{start}_{end_}.jsonl"
    to_jsonl(data, output_file_json)
