
import pandas as pd
from google.cloud import storage
import json

from utils import StorageWrap

if __name__ == "__main__":
    bucket_name = 'ragtime-ai-act'
    sw = StorageWrap(bucket_name)

    input_file = 'json/documents.json'
    print('-- loading ')
    df = sw.load_json(input_file)
    print(df.head())

    # export data to json file in bucket
    df['test'] = "Hello world"

    print('-- saving ')
    output_file = "json/documents_test.json"
    sw.info(output_file)

    sw.save_json(df, output_file)
    blob = sw.info(output_file)

