"""
Updates an existing collection with new properties
https://weaviate.io/developers/weaviate/api/rest/schema#add-a-property
"""
import os, re, json, glob
import time, datetime
from datetime import timedelta
import pandas as pd
import typing as t

pd.options.display.max_columns = 100
pd.options.display.max_rows = 60
pd.options.display.max_colwidth = 100
pd.options.display.precision = 10
pd.options.display.width = 160
pd.set_option("display.float_format", "{:.4f}".format)
import numpy as np
import argparse

# Local
import sys

sys.path.append("./script")
from weaviate_utils import *

# weaviate
import weaviate.classes as wvc

def property_from_dict(dct: t.Dict) -> weaviate.collections.classes.config.Property:
    datatypes = {
        "uuid": wvc.DataType.UUID,
        "uuid_array": wvc.DataType.UUID,
        "text": wvc.DataType.TEXT,
        "text_array": wvc.DataType.TEXT_ARRAY,
        "float": wvc.DataType.NUMBER,
        "float_array": wvc.DataType.NUMBER_ARRAY,
        "int": wvc.DataType.INT,
        "int_array": wvc.DataType.INT_ARRAY,
        "date": wvc.DataType.DATE,
        "date_array": wvc.DataType.DATE_ARRAY,
    }
    assert dct.get("name") is not None, "missing name for the property"
    assert dct.get("dataType") is not None, "missing dataType for the property"
    assert dct.get("skip_vectorization") is not None, "missing skip_vectorization for the property"

    prop = wvc.Property(
        name=dct.get("name"),
        data_type=datatypes[dct.get("dataType")],
        skip_vectorization=dct.get("skip_vectorization"),
        vectorize_property_name=dct.get("vectorize_property_name")
        if dct.get("vectorize_property_name") is not None
        else False,
        tokenization=dct.get("tokenization"),
        nestedProperties=dct.get("nestedProperties"),
        indexFilterable=dct.get("indexFilterable") if dct.get("indexFilterable") is not None else True,
        indexSearchable=dct.get("indexSearchable") if dct.get("indexSearchable") is not None else True,
    )

    return prop


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--location", help="local or cloud", default="local")
    parser.add_argument("--collection_name", help="collection_name")
    args = parser.parse_args()

    collection_name = args.collection_name
    cluster_location = args.location

    client = connect_client(cluster_location)

    if client.is_live() & client.is_ready():
        print(f"client is live and ready on {cluster_location}")
    assert client.is_live() & client.is_ready(), "client is not live or not ready"

    collection_exists = collection_name in list(client.collections.list_all().keys())
    print(f"{collection_name} (exists {collection_exists})\t cluster:{cluster_location}")

    vectorizer = which_vectorizer("OpenAI")

    collection = client.collections.get(collection_name)
    config = collection.config.get()
    current_property_names = [ p.name for p in config.properties    ]

    # ----------------------------------------------------------------
    # Collections for final_four vertical
    # ----------------------------------------------------------------
    # load schema from collection name
    with open(f"./script/embedding/schemas/{collection_name}.json", "r") as f:
        schema = json.load(f)

    new_properties = [ prop for prop in schema if prop['name'] not in current_property_names ]

    if len(new_properties) > 0:
        for property in new_properties:
            collection.config.add_property(
                    property_from_dict(property)
                )

        # list properties
        collection = client.collections.get(collection_name)
        config = collection.config.get()
        current_property_names = [ p.name for p in config.properties    ]
    else:
        print("==> no new property detected in schema !!")

    print(f"collection {collection_name} has :{count_collection(collection)} records")
    print(f"collection {collection_name} has the following properties:{current_property_names} ")
    client.close()
