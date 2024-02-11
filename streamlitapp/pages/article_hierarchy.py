

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

def save(mapp, output_file_json = "./data/json/final_four_mapping-2024-02-06.json"):
    with open(output_file_json, "w", encoding="utf-8") as f:
        mapp.to_json(f, force_ascii=False, orient="records", indent=4)

def update_level_1(id):
    value = st.session_state[f"level_1_{id}"]
    mapp.loc[mapp.uuid == id, 'level_1'] = value
    mapp.loc[mapp.uuid == id, 'modified_at'] = datetime.datetime.now()
    save(mapp)

def update_level_2(id):
    value = st.session_state[f"level_2_{id}"]
    mapp.loc[mapp.uuid == id, 'level_2'] = value
    mapp.loc[mapp.uuid == id, 'modified_at'] = datetime.datetime.now()
    save(mapp)

def update_level_3(id):
    value = st.session_state[f"level_3_{id}"]
    mapp.loc[mapp.uuid == id, 'level_3'] = value
    mapp.loc[mapp.uuid == id, 'modified_at'] = datetime.datetime.now()
    save(mapp)

def update_modified(id):
    value = st.session_state[f"modified_{id}"]
    mapp.loc[mapp.uuid == id, 'modified_at'] = datetime.datetime.now()
    save(mapp)


def initialise_session():
    print()
    print("-- initialize_sessson")
    current = pd.read_json('./session.json').to_dict(orient = 'records')[0]
    st.session_state['section_key'] = current.get('section')
    st.session_state['title_key'] = current.get('title')
    st.session_state['level_1_key'] = current.get('level_1')

    return current

def update_session():
    print("-- update_session")

    current = [{
        'section': st.session_state.get('section_key'),
        'title': st.session_state.get('title_key'),
        'level_1': st.session_state.get('level_1_key'),
    }]
    with open('./session.json', "w", encoding="utf-8") as f:
        pd.DataFrame(current).to_json(f, force_ascii=False, orient="records", indent=4)

if __name__ == "__main__":
    layout = 'rows'

    st.set_page_config(
        page_title="AI-act Map text bits to articles",
        page_icon=None,
        layout="wide",
        initial_sidebar_state="auto")

    current = initialise_session()

    input_file = './data/json/final-four-2024-02-06.json'
    data = pd.read_json(input_file)

    mapping_file = './data/json/final_four_mapping-2024-02-06.json'
    mapp = pd.read_json(mapping_file)

    # ------------------------------------------------------------
    # Sidebar
    # ------------------------------------------------------------

    with st.sidebar:

        section_options = ["citation","recitals","regulation","annex"]
        gen_section = display_selectbox("Section",section_options,"section_key")

        if gen_section == 'regulation':
            # title_options = ['TITLE I', 'TITLE II', 'TITLE III', 'TITLE IV', 'TITLE V','TITLE VI', 'TITLE VII', 'TITLE VIII', 'TITLE IX', 'TITLE X', 'TITLE XI', 'TITLE XII','']
            title_options = sorted(data.regulation_title.unique())
            gen_title = display_selectbox("TITLE",title_options, "title_key")
        else:
            gen_title = ''

        # filter data
        cond = data.section == gen_section
        if gen_section in ['regulation']:
            cond = cond & (data.regulation_title == gen_title)
        data = data[cond].copy()
        data.reset_index(inplace= True, drop = True)

        # with st.sidebar:
        level_1_options = list(data.level_1.unique())

        if st.session_state.get('level_1_key') :
            if st.session_state.get("level_1_key") not in level_1_options:
                st.session_state.pop("level_1_key")
        gen_level_1 = display_selectbox("Article level 1",level_1_options,"level_1_key")

        data = data[data.level_1 == gen_level_1].copy()
        data.reset_index(inplace= True, drop = True)

        st.write(current)

    if layout == 'columns':
        for i, d in data.iterrows():
            st.divider()
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

    if layout == 'rows':
        for i, d in data.iterrows():
            st.divider()
            sch1, sch2, sch3 = st.columns([5,5,5])
            with sch1:
                item =  mapp[mapp.uuid == d.uuid].to_dict(orient = 'records')[0]
                st.write(f":gray[{d.pdf_order}] &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; :orange[{d.title}]", unsafe_allow_html=True)
            with sch2:
                col1, col2 = st.columns([1,12])
                with col1:
                    st.checkbox(' ',
                        not pd.isnull(item['modified_at']),
                        key = f'modified_{d.uuid}',
                        on_change = update_modified,
                        args=({d.uuid}),
                        label_visibility='collapsed',
                    )
                with col2:
                    st.caption(d.uuid)
            with sch3:
                sc1, sc2, sc3 = st.columns([1,1,1])
                with sc1:
                    st.selectbox('article',
                        level_1_options,
                        index = level_1_options.index(item['level_1']),
                        key = f'level_1_{d.uuid}',
                        on_change=update_level_1,
                        args=({d.uuid}),
                        label_visibility='visible',
                    )
                with sc2:
                    st.number_input('paragraph',
                        value=item['level_2'],
                        key=f'level_2_{d.uuid}',
                        on_change=update_level_2,
                        args=({d.uuid}),
                        label_visibility="visible"
                    )

                with sc3:
                    st.number_input('merge',
                        value=item['level_3'],
                        key=f'level_3_{d.uuid}',
                        on_change=update_level_3,
                        args=({d.uuid}),
                        label_visibility="visible")
            for source in ['commission', 'council', 'parliament', 'draft']:
                c1, c2 = st.columns([1,9])
                with c1:
                    st.subheader(f":grey[{source}]")
                with c2:
                    st.write(f":violet[{d[source]}]")







