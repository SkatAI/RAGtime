'''
Creates 2 collection for reconciling the final four docs with amendments from committees and political groups
'''
import os, re, json, glob
import time, datetime
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

# Local
import sys
sys.path.append('./script')
from weaviate_utils import *

# weaviate
import weaviate.classes as wvc


if __name__ == "__main__":
    create_new_collection = True
    collection_name = "AIAct_FF_texts_01"
    collection_name = "AIAct_FF_titles_01"
    # connect to weaviate
    cluster_location = "local"
    # cluster_location = "cloud-cluster"
    client = connect_client(cluster_location)

    if client.is_live() & client.is_ready():
        print("client is live and ready")
    assert client.is_live() & client.is_ready(), "client is not live or not ready"


    collection_exists = collection_name in  list(client.collections.list_all().keys())


    # ----------------------------------------------------------------
    # Collections for final_four vertical
    # 1 for titles
    # 1 for texts
    # ----------------------------------------------------------------
    vectorizer = which_vectorizer("OpenAI")
    if collection_name == "AIAct_FF_titles_01":
        # vectorize the title, don't keep the text
        properties = [
            # meta: non vectorized
            wvc.Property(name='vvid', data_type=wvc.DataType.UUID, skip_vectorization=True),
            wvc.Property(name='section', data_type=wvc.DataType.TEXT, skip_vectorization=True),
            wvc.Property(name='author', data_type=wvc.DataType.TEXT, skip_vectorization=True),
            wvc.Property(name='pdf_order',data_type=wvc.DataType.TEXT, skip_vectorization=True),
            wvc.Property(name='level',data_type=wvc.DataType.TEXT, skip_vectorization=True),
            # vectorized
            wvc.Property(name='title', data_type=wvc.DataType.TEXT, vectorize_property_name = False),
        ]

    if collection_name == "AIAct_FF_texts_01":
        # vectorize the text but keep the title as meta
        properties = [
            # meta: non vectorized
            wvc.Property(name='vvid', data_type=wvc.DataType.UUID, skip_vectorization=True),
            wvc.Property(name='section', data_type=wvc.DataType.TEXT, skip_vectorization=True),
            wvc.Property(name='author', data_type=wvc.DataType.TEXT, skip_vectorization=True),
            wvc.Property(name='pdf_order',data_type=wvc.DataType.TEXT, skip_vectorization=True),
            wvc.Property(name='level',data_type=wvc.DataType.TEXT, skip_vectorization=True),
            wvc.Property(name='title',data_type=wvc.DataType.TEXT, skip_vectorization=True),
            # vectorized
            wvc.Property(name='text', data_type=wvc.DataType.TEXT, vectorize_property_name = False),
        ]

    if collection_exists:
        print(f'Are you sure you want to re create it ? (type the collection name to continue)\n {collection_name}')
        x = input()
        if x == collection_name:
            create_new_collection = True
            print('deleting collection')
            client.collections.delete(collection_name)
        else:
            create_new_collection = False

    if create_new_collection:
        collection = create_collection(
                client,
                collection_name,
                vectorizer,
                properties,
            )
        print('-- collection created')
    else:
        print("ok not creating the collection")

    collection = client.collections.get(collection_name)
    print(f"collection {collection_name} has :{count_collection(collection)} records")

