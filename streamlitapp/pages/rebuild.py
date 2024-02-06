'''
Re build chunks of AI act into article and sections
'''
# usual suspects
import os, re, json, glob
import time, datetime
import pandas as pd
pd.options.display.max_columns = 100
pd.options.display.max_rows = 60
pd.options.display.max_colwidth = 180
pd.options.display.precision = 10
pd.options.display.width = 240
pd.set_option("display.float_format", "{:.4f}".format)
import numpy as np

# streamlit
import streamlit as st
# weaviate
from weaviate.classes import Filter

# open AI
from openai import OpenAI

# LangChain
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain

from langchain.chains import SequentialChain

# local
from  weaviate_utils_copy import *
from retrieve import Retrieve

import yaml
from yaml.loader import SafeLoader

import warnings

if __name__ == "__main__":
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    st.set_page_config(
        page_title="AI-act combine text chunks",
        page_icon=None,
        layout="wide",
        initial_sidebar_state="auto")


    # sidebar: source, section
    with st.sidebar:
        # st.image("logo-gustave-eiffel.png")
        # if st.session_state["authentication_status"]:

        source_options = ["draft", "council", "parliament"]
        gen_source = st.selectbox(
                "From",
                source_options,
                index = 0 if st.session_state.get("source_key") is None else source_options.index(st.session_state.get("source_key")),
                key = "source_key"
            )

        section_options = ["recitals","regulation","annex"]
        gen_section = st.selectbox(
                "Section",
                section_options,
                index = 0 if st.session_state.get("section_key") is None else section_options.index(st.session_state.get("section_key")),
                key = "section_key"
            )

        # load ref and process title
        ref = pd.read_json(f'./data/json/52021PC0206-{gen_section}.json')
        if gen_section == 'regulation':
            rgx_source = r".*?(Article \d+).*?Section (\d+)"
            rgx_target = r'\1(\2)'
            ref['title'] = ref.path.apply(lambda pth : re.sub(rgx_source, rgx_target, pth))

            ref['title'] = ref.path.apply(lambda pth : re.sub(rgx_source, rgx_target, pth))
            ref['title'] = ref.title.apply(lambda pth : pth.split('>>')[-1].split(':')[0].strip())
        else:
            ref['title'] = ref.path


        if gen_section == 'regulation':
            title_options = ['TITLE I', 'TITLE II', 'TITLE III', 'TITLE IV', 'TITLE V','TITLE VI', 'TITLE VII', 'TITLE VIII', 'TITLE IX', 'TITLE X', 'TITLE XI', 'TITLE XII','']
            gen_title = st.selectbox(
                    "TITLE",
                    title_options,
                    index = 0 if st.session_state.get("title_key") is None else title_options.index(st.session_state.get("title_key")),
                    key = "title_key"
                )

        else:
            gen_title = None

        if (gen_section == 'regulation') & (gen_title is not None):

            article_options = list(ref[ref.path.str.contains(gen_title)].title.unique())
            st.write(f"article_options: {article_options}")

            if st.session_state.get("article_key") is None :
                index = 0
            elif  st.session_state.get("article_key") in article_options:
                index = article_options.index(st.session_state.get("article_key"))
            else:
                index = 0


            gen_article = st.selectbox(
                    "article",
                    article_options,
                    index = index,
                    key = "article_key"
                )
        else:
            gen_article = None

    # open json
    input_file = './data/json/final-four-2024-02-05.json'
    data = pd.read_json(input_file)
    data = data[(data.section == gen_section) ].copy()
    if gen_section in ['recitals','regulation']:
        if gen_article is not None:
            cond = (data.regulation_title == gen_title) & (data.title.str.contains(gen_article))
            st.write(f"gen_article {gen_article}")
        else:
            cond = (data.regulation_title == gen_title)

        data = data[ cond].copy()


    else:
        ref = pd.read_json(f'./data/json/52021PC0206-explanatory-memorandum.json')


    st.write(f"Loaded {data.shape} rows. Section **{gen_section}**. From **{gen_source}** ")
    if gen_title is not None:
        cond = ref.path.str.contains(gen_title)
        st.write(list(ref[cond].title))
        st.table(ref[cond][['title','text']])

    for i, d in data.iterrows():
        st.divider()
        # match = ref[(ref.title == d.title) & (~ref.header)].copy()
        match = ref[(ref.title == d.title)].copy()
        if match.shape[0] == 0:
            st.subheader(":red[No match]")
        elif match.shape[0] == 1:
            st.subheader(f":blue[ {match.title.values[0]}]")
            st.caption(match.text.values[0])
        elif match.shape[0] > 1:
            st.subheader(":red[multiple match]")
            st.write(match)

        # if len(d[gen_source]) >0:
        st.write(f" {d.number} - {d.title}")
        # for src in ["commission", "council", "parliament","draft"]:
        for src in ["commission","draft"]:
            sc1, sc2 = st.columns([1,7])
            with sc1:
                st.write(src)
            with sc2:
                st.write(f"{d[src]}")



        # TODO the version that matches the draft  is in color
        # distance between : commission and draft / draft and most matching


        # sc1, sc2, sc3, sc4 = st.columns([2,8,1,8])

        # with sc1:
        #     st.write(f" {d.number} - {d.title}")
        # with sc2:
        #     st.write(f"{d.commission}")
        #     st.write(f"[{len(d.commission)}]")
        # with sc3:
        #     st.caption('_')
        # with sc4:
        #     st.write(d[gen_source])
        #     st.write(f"[{len(d[gen_source])}]")
