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
import argparse
import uuid
# Local
import sys
sys.path.append('./script')
from weaviate_utils import *

# weaviate
import weaviate
import weaviate.classes as wvc
from weaviate.classes import Filter

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=ResourceWarning)


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--location", help="local or cloud", default = 'local')
    parser.add_argument("--collection_name", help="collection_name")
    parser.add_argument("--dataset", help="dataset in ./data/rag/*.json")
    args = parser.parse_args()

    cluster_location = args.location
    collection_name = args.collection_name
    input_file = f"./data/rag/{args.dataset}"

    client = connect_client(cluster_location)

    if client.is_live() & client.is_ready():
        print(f"client is live and ready on {cluster_location}")
    assert client.is_live() & client.is_ready(), "client is not live or not ready"


    data = pd.read_json(input_file)
    print("-- loaded ",data.shape[0], "items")

    collection = client.collections.get(collection_name)
    print(f"collection {collection_name} has :{count_collection(collection)} records")

    start = 0
    step = 1000
    while start < data.shape[0]:
        print(start)
        rng = range(start, min([start+ step,data.shape[0]]))
        batch_result = collection.data.insert_many(
            data.loc[rng].to_dict(orient = 'records')
        )
        if batch_result.has_errors:
            print(list(batch_result.errors))

        count_collection(collection)
        start += step

    print("--")
    print(f"collection {collection_name} has :{count_collection(collection)} records")
