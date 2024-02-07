

'''
Re build chunks of AI act into article and sections
TODO: st.query_params
TODO: preset drop downs to level_1, 2, 3
'''
# usual suspects
import os, re, json, glob
import time, datetime
import pandas as pd
import numpy as np

# streamlit
import streamlit as st

import yaml
from yaml.loader import SafeLoader

import warnings

def display_selectbox(
        header: str,
        options: list,
        select_key: str
    ) -> str:
    index = 0 if st.session_state.get(select_key) is None else options.index(st.session_state.get(select_key))
    return st.selectbox(
            header,
            options,
            index = index,
            key = select_key
        )


if __name__ == "__main__":
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    st.set_page_config(
        page_title="AI-act Map text bits to articles",
        page_icon=None,
        layout="wide",
        initial_sidebar_state="auto")
    # removes space above select box
    st.markdown(
        """
        <style>
        [data-baseweb="select"] {
            margin-top: -40px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    input_file = './data/json/final-four-2024-02-06.json'
    final_four_map_file = "./data/json/final_four_article_map.json"

    data = pd.read_json(input_file)


    # ------------------------------------------------------------
    # Sidebar
    # ------------------------------------------------------------

    with st.sidebar:

        # source_options = ["commission","draft", "council", "parliament"]
        # gen_source = display_selectbox("From",source_options,"source_key")

        section_options = ["citation","recitals","regulation","annex"]
        gen_section = display_selectbox("Section",section_options,"section_key")
        # gen_section = 'regulation'

        if gen_section == 'regulation':
            title_options = ['TITLE I', 'TITLE II', 'TITLE III', 'TITLE IV', 'TITLE V','TITLE VI', 'TITLE VII', 'TITLE VIII', 'TITLE IX', 'TITLE X', 'TITLE XI', 'TITLE XII','']
            gen_title = display_selectbox("TITLE",title_options, "title_key")
        else:
            gen_title = None

    # filter data
    cond = data.section == gen_section
    if gen_section in ['recitals','regulation']:
        cond = cond & (data.regulation_title == gen_title)
    data = data[cond].copy()
    data.reset_index(inplace= True, drop = True)

    with st.sidebar:
        article_options = list(data[data.title.str.contains('Article')].article.unique())
        if 'article_key' in st.session_state:
            if st.session_state.get("article_key") not in article_options:
                st.session_state.pop("article_key")
        gen_article = display_selectbox("Article",article_options,"article_key")

    data = data[data.article == gen_article].copy()
    data.reset_index(inplace= True, drop = True)

    for i, d in data.iterrows():
        st.divider()
        c1, c2, c3, c4, c5 = st.columns([3,3,3,3,3])
        with c1:
            st.write(d.title)
            sc1, sc2, sc3 = st.columns([1,1,1])
            with sc1:
                # st.write(gen_article)
                st.selectbox('',[gen_article.split(' ')[-1]], key = f'art_{d.number}', label_visibility='hidden', placeholder='art')
            with sc2:
                st.selectbox('',range(0,10), key = f'par_{d.number}', label_visibility='hidden', placeholder='par')
            with sc3:
                st.selectbox('',range(0,10), key = f'subpar_{d.number}', label_visibility='hidden', placeholder='subpar')
        with c2:
            st.write(d.commission)
        with c3:
            st.write(d.council)
        with c4:
            st.write(d.parliament)
        with c5:
            st.write(d.draft)

        # with c4:



