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
import argparse
import uuid
# Local
import sys
sys.path.append('./script')
from weaviate_utils import *

# weaviate
import weaviate.classes as wvc

def property_from_dict(dct) ->  weaviate.collections.classes.config.Property:
    datatypes = {
        'uuid': wvc.DataType.UUID,
        'uuid_array': wvc.DataType.UUID,
        'text': wvc.DataType.TEXT,
        'text_array': wvc.DataType.TEXT_ARRAY,
        'float': wvc.DataType.NUMBER,
        'float_array': wvc.DataType.NUMBER_ARRAY,
        'int': wvc.DataType.INT,
        'int_array': wvc.DataType.INT_ARRAY,
        'date': wvc.DataType.DATE,
        'date_array': wvc.DataType.DATE_ARRAY,
    }
    assert dct.get('name') is not None, "missing name for the property"
    assert dct.get('dataType') is not None, "missing dataType for the property"
    assert dct.get('skip_vectorization') is not None, "missing skip_vectorization for the property"

    prop = wvc.Property(
            name = dct.get('name'),
            data_type=datatypes[dct.get('dataType')],
            skip_vectorization=dct.get('skip_vectorization'),
            vectorize_property_name=dct.get('vectorize_property_name') if dct.get('vectorize_property_name') is not None else False,
            tokenization=dct.get('tokenization'),
            # tokenization=dct.get('tokenization') if dct.get('tokenization') is not None else 'word',
            nestedProperties=dct.get('nestedProperties'),
            indexFilterable=dct.get('indexFilterable') if dct.get('indexFilterable') is not None else True,
            indexSearchable=dct.get('indexSearchable') if dct.get('indexSearchable') is not None else True,
        )

    return prop

if __name__ == "__main__":
    create_new_collection = True

    parser = argparse.ArgumentParser()
    parser.add_argument("--location", help="local or cloud", default = 'local')
    parser.add_argument("--collection_name", help="collection_name")
    args = parser.parse_args()

    collection_name = args.collection_name
    cluster_location = args.location

    client = connect_client(cluster_location)

    if client.is_live() & client.is_ready():
        print(f"client is live and ready on {cluster_location}")
    assert client.is_live() & client.is_ready(), "client is not live or not ready"

    collection_exists = collection_name in  list(client.collections.list_all().keys())
    print(f"{collection_name} (exists {collection_exists})\t cluster:{cluster_location}")

    vectorizer = which_vectorizer("OpenAI")

    # ----------------------------------------------------------------
    # Collections for final_four vertical
    # ----------------------------------------------------------------
    # load schema  AIAct_240218.json
    with open(f"./script/embedding/schemas/{collection_name}.json", 'r') as f:
        schema = json.load(f)
    properties = []
    for prop in schema:
        properties.append(property_from_dict(prop))

    if collection_exists:
        print(f'Are you sure you want to re create it ? \n(type the collection name to delete the existing on)\n {collection_name}')
        x = input()
        if x == collection_name:
            create_new_collection = True
            print('deleting existing collection')
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

