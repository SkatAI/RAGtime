'''
embeds final four
# TODO
'''
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
import numpy as np
import typing as t
# Local
import sys
sys.path.append('./script')
from weaviate_utils import *

# OpenAI
# import openai
# import tiktoken

# weaviate
import weaviate
import weaviate.classes as wvc
from weaviate.classes import Filter


if __name__ == "__main__":
    client = connect_client(location="local")

    input_file = "./data/json/final_four_author-2024-02-06.json"

    data = pd.read_json(input_file)
    print("-- loaded ",data.shape[0], "items")

    data['level'] = data.apply(lambda d: '.'.join([str(d.level_1), str(d.level_2), str(d.level_3)]), axis = 1)
    data.reset_index(inplace = True, drop = True)
    # ----------------------------------------------------------------
    # titles
    # ----------------------------------------------------------------

    collection_name = "AIAct_FF_titles_01"
    columns = ['vvid','section','author','pdf_order','level','title']
    # collection_name = "AIAct_FF_texts_01"
    # columns = ['vvid','section','author','pdf_order','level','title','text']

    collection = client.collections.get(collection_name)

    start = 0
    step = 1000
    while start < data.shape[0]:
        print(start)
        rng = range(start, min([start+ step,data.shape[0]]))
        batch_result = collection.data.insert_many(
            data.loc[rng][columns].to_dict(orient = 'records')
        )
        if batch_result.has_errors:
            print(list(batch_result.errors))
            # raise "stopping"

        count_collection(collection)
        start += step

    # ----------------------------------------------------------------
    # Match
    # ----------------------------------------------------------------
    input_file = "./data/json/amendments_political_groups-2024-02-09.json"
    amd = pd.read_json(input_file)

    def closest(title: str, num: int ) -> t.List[weaviate.collections.classes.internal.Object]:
        response = collection.query.near_text(
            query = title,
            limit = num,
            filters = Filter.by_property("author").equal('commission'),
            return_metadata = [ 'distance', 'certainty', 'score', 'explain_score', 'is_consistent'],
        )
        return response.objects

    def closest(title: str, num: int ) -> t.List[weaviate.collections.classes.internal.Object]:
        response = collection.query.hybrid(
            query = title,
            limit = num,
            filters = Filter.by_property("author").equal('commission'),
            return_metadata = [ 'distance', 'certainty', 'score', 'explain_score', 'is_consistent'],
        )
        return response.objects

df = []
tgt_cols = ['vvid', 'uuid', 'section', 'title', 'author', 'text', 'pdf_order', 'regulation_title', 'level']

for i in range(2):
    samp = amd.sample()
    title_amd = samp.title.values[0]
    uuid_amd = samp.uuid.values[0]
    results = closest(title_amd, 2)
    k = 0
    for item in results:
        if k == 0:
            print()
        # print(f"{title_amd:50} -> {item.properties['title']:50} \t  certainty {np.round(item.metadata.certainty, 4)} \t {np.round(item.metadata.distance, 4)}")
        print(f"{title_amd:50} -> {item.properties['title']:50} \t  certainty {item.metadata.__dict__}")
        k+=1

        vvid_tgt = str(item.properties['vvid'])
        uuid_tgt = data[data.vvid == vvid_tgt].uuid.unique()[0]
        it = item.properties.copy()

        it['amd'] = samp.to_dict(orient = 'records')
        it['tgt'] = data[data.uuid == uuid_tgt][tgt_cols].to_dict(orient = 'records')
        df.append(it)

df = pd.DataFrame(df)
df.sort_values(by = 'certainty', ascending = True, inplace = True)
