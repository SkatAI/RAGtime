"""
Build whole dataset for RAG ingestion
- amendments
"""

# usual libs
import os, re, json, glob
import time, datetime
from datetime import timedelta
import pandas as pd
import argparse
from tqdm import tqdm

pd.options.display.max_columns = 30
pd.options.display.max_rows = 60
pd.options.display.max_colwidth = 80
pd.options.display.precision = 4
pd.options.display.width = 0
pd.set_option("display.float_format", "{:.2f}".format)
import numpy as np
import typing as t
import uuid
from regex_utils import Rgx
from lines import Line, RecitalLine, RegulationLine

if __name__ == "__main__":
    input_file_amendment = "./data/json/amendments_political_groups-2024-02-09.json"
    output_file_amendment = "./data/rag/amendments_20240227.json"

    # ------------------------------------------------------------------------------------
    # regulation: only recital content, one liner
    # ------------------------------------------------------------------------------------
    # load amendment
    data = pd.read_json(input_file_amendment)
    data["section"] = "amendments"
    data["content_type"] = "amendment"
    data['title'] = data.apply(lambda d : f"Amendment {d.amendment_number}: {d.title}  ", axis = 1)

    data = data[["uuid", "text", "title", "author", "section", "content_type", "proposers"]].copy()

        # "author":"commission",
        # "section":"recitals",
        # "content_type":"recital",
        # "title":"Recital 1",
        # "text":"(1) The purpose of this Regulation is to improve the functioning of the internal market by laying down a uniform legal framework in particular for the development, marketing and use of artificial intelligence in conformity with Union values. This Regulation pursues a number of overriding reasons of public interest, such as a high level of protection of health, safety and fundamental rights, and it ensures the free movement of AI-based goods and services cross-border, thus preventing Member States from imposing restrictions on the development, marketing and use of AI systems, unless explicitly authorised by this Regulation.",
        # "uuid":"3a0b6ddb-55ea-4cd5-8b03-47fb0b58af2b"


    with open(output_file_amendment, "w", encoding="utf-8") as f:
        data.to_json(f, force_ascii=False, orient="records", indent=4)
