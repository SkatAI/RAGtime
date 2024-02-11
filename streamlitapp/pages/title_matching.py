'''



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
warnings.filterwarnings("ignore", category=DeprecationWarning)

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
            on_change = update_session,
            key = select_key
        )

if __name__ == "__main__":

    st.set_page_config(
        page_title="AI-act Map amendments titles to ",
        page_icon=None,
        layout="wide",
        initial_sidebar_state="auto")

    input_file = './data/json/final_four_author-2024-02-06.json'
    data = pd.read_json(input_file)

    matching_file = './data/json/matching/title_matching_0_100.jsonl'
    match = pd.read_json(matching_file)

    # ------------------------------------------------------------
    # Sidebar
    # ------------------------------------------------------------

    for i, d in match.iterrows():

        c1, c2, c3, c4, c5 = st.columns([3,3,3,3,3])
        item =  mapp[mapp.uuid == d.uuid].to_dict(orient = 'records')[0]
        with c1:
            st.write(f":gray[{d.pdf_order}] &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; :orange[{d.title}]", unsafe_allow_html=True)
            sch1, sch2 = st.columns([1,8])
            with sch1:
                st.checkbox(' ',
                    not pd.isnull(item['modified_at']),
                    key = f'modified_{d.uuid}',
                    on_change = update_modified,
                    args=({d.uuid}),
                    label_visibility='collapsed',
                )
            with sch2:
                st.caption(d.uuid)
            sc1, sc2, sc3 = st.columns([1,1,1])
            with sc1:
                st.selectbox(' ',
                    level_1_options,
                    index = level_1_options.index(item['level_1']),
                    key = f'level_1_{d.uuid}',
                    on_change=update_level_1,
                    args=({d.uuid}),
                    label_visibility='collapsed',
                )
            with sc2:
                st.number_input(' ',
                    value=item['level_2'],
                    key=f'level_2_{d.uuid}',
                    on_change=update_level_2,
                    args=({d.uuid}),
                    label_visibility="collapsed"
                )

            with sc3:
                st.number_input(' ',
                    value=item['level_3'],
                    key=f'level_3_{d.uuid}',
                    on_change=update_level_3,
                    args=({d.uuid}),
                    label_visibility="collapsed")
        with c2:
            st.write(f":violet[{d.commission}]")
        with c3:
            st.write(f":blue[{d.council}]")
        with c4:
            st.write(f":blue[{d.parliament}]")
        with c5:
            st.write(f":violet[{d.draft}]")

