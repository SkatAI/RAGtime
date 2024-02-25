"""
use ragas to create a test set of questions answers
"""
import os, re, json, glob
import time, datetime
from datetime import timedelta
import pandas as pd
import hashlib
from tqdm import tqdm

pd.options.display.max_columns = 160
pd.options.display.max_rows = 60
pd.options.display.max_colwidth = 160
pd.options.display.precision = 10
pd.options.display.width = 160
pd.set_option("display.float_format", "{:.4f}".format)
import numpy as np
import random

random.seed(800)
import argparse

# OpenAI
import openai
import tiktoken

# LangChain
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain

from langchain.chains import SequentialChain
from langchain.docstore.document import Document
from langchain.prompts import HumanMessagePromptTemplate

# ragas
import ragas
from ragas.testset import TestsetGenerator

# monkey patching with new prompts
import typing as t

from ragas_patching import (
    _filter_question_patched,
    _seed_question_patched,
    _generate_answer_patched,
    generate_patched,
)

TestsetGenerator._filter_question = _filter_question_patched
TestsetGenerator._seed_question = _seed_question_patched
TestsetGenerator._generate_answer = _generate_answer_patched
TestsetGenerator.generate = generate_patched

# huggingface
from datasets import Dataset

import warnings

warnings.simplefilter(action="ignore", category=UserWarning)

model = "gpt-4-0125-preview"
model = "gpt-3.5-turbo-1106"
test_size = 4
docs_concatenate = 2
max_documents = 10

from loading import (
    Snips,
    Chunks,
)

if __name__ == "__main__":
    document_path = "data/json/"
    documents_filename = os.path.join(document_path, "documents.json")

    files = glob.glob(os.path.join(document_path, "*.json"))
    files.pop(files.index(documents_filename))

    snips = Snips(files)

    chunks = Chunks(snips)

    documents = chunks.to_langchain_documents(max_documents=max_documents)

    assert len(documents) >= test_size, f"not enough documents {len(documents)} for test_size {test_size}"

    # only generate simple questions
    testset_distribution = {
        "simple": 1.0,
        "reasoning": 0.0,
        "multi_context": 0.0,
        "conditional": 0.0,
    }

    testsetgenerator = TestsetGenerator.from_default(
        openai_generator_llm=model,
        openai_filter_llm=model,
        chat_qa=0.0,
        chunk_size=2048,
        testset_distribution=testset_distribution,
    )

    testset = testsetgenerator.generate(documents, test_size=test_size)
    output_file = f"./data/question_answers_{datetime.datetime.now().strftime('%Y%m%d%H%M')}.jsonl"
    testset.to_jsonl(output_file)

    # df = testset.to_pandas().copy()

    # save
    # testset.to_pandas()
    # df.rename(columns = {'ground_truth':'answer'}, inplace = True)
    # df = df[['question', 'answer', 'ground_truth_context', 'context', 'question_type', 'episode_done']].copy()

    # with open(output_file, "a") as file:
    #     for entry in df.to_dict(orient = 'records'):
    #         try:
    #             entry['answer'] = json.loads(entry['answer'][0])
    #         except:
    #             pass
    #         json.dump(entry, file, indent=4)
    #         file.write("\n")

    # for d in df.head().to_dict(orient = "records"):
    #     try:
    #         d['answer'] = json.loads(d['answer'][0])
    #     except:
    #         d['answer'] = d['answer'][0]

    #     print("\n","--"*20)
    #     print(f"question: {d['question']}")
    #     print(f"-- answer: \n{d['answer']}")
    #     print(f"\n--answer context:  \n{d['ground_truth_context'][0]}")
    #     print(f"\n--context:  \n{d['context'][0]}")

    # mdc = pd.read_json('data/json/documents.json').to_dict(orient = 'records')[0]
    # footer = f"Author: {mdc['issuer']}, {mdc['date_published']}"
    # docu_names = [
    #         'data/json/52021PC0206-explanatory-memorandum.json',
    #         'data/json/52021PC0206-recitals.json',
    #         'data/json/52021PC0206-regulation.json',
    #         ]

    # # Number of concatenated consecutive paragraphs

    # chunks = []
    # for doc_name in docu_names:
    #     data = pd.read_json(doc_name)

    #     headers = data.path.unique()
    #     for header in headers:
    #         # don't want simple headers
    #         cond = (data.path == header) & (~data.header)

    #         if data[cond].shape[0] > 0:
    #             for k in range(0, data[cond].shape[0], docs_concatenate):
    #                 end_ = min(data[cond].shape[0], k+docs_concatenate)
    #                 chunks.append('\n'.join([ header] + list(data[cond][k: end_].text.values) + [footer] ))

    # print(f"{len(chunks)} chunks")

    # estimate chunks length
    # encoding = tiktoken.get_encoding("cl100k_base")
    # tokens_ = [len(encoding.encode(txt)) for txt in chunks]
    # print(f"tokens: mean {np.mean(tokens_)} median  {np.median(tokens_)} stdf  {np.std(tokens_)}")
