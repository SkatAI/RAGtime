'''
'''
import os, re, json, glob
import time, datetime
import pandas as pd
import numpy as np

# streamlit
import streamlit as st

# weaviate
from weaviate.classes import Filter

# local
from streamlit_weaviate_utils import *

import warnings

import psycopg2
from sqlalchemy import create_engine
from sqlalchemy import text as sqlalchemy_text
from db_utils import Database

def select_summary(id):

    query = f'''
        update analysis set selected = not selected where id = {id}
    '''
    with db.engine.connect() as connection:
        result = connection.execute(sqlalchemy_text(query))
        connection.commit()

def swap_featured(acte, scene):
    val = st.session_state['toggle_featured']
    if val:
        query = f'''
            update analysis set featured = 't' where play_id = {db.play_id} and acte = {acte} and scene = {scene}
        '''
    else:
        query = f'''
            update analysis set featured = 'f' where play_id = {db.play_id} and acte = {acte} and scene = {scene}
        '''

    with db.engine.connect() as connection:
        result = connection.execute(sqlalchemy_text(query))
        connection.commit()

def add_text(play_id, acte, scene):
    print('Hello add text')
    text = st.session_state[f"{play_id}_{acte}_{scene}_summary_key"].strip()

    query = f'''
        insert into analysis
            (play_id, experiment, category , acte, scene , text, selected)
        values
            ({play_id},'manual', 'summary', {acte}, {scene}, $${text}$$,'f');
    '''
    print(query)

    with db.engine.connect() as connection:
        result = connection.execute(sqlalchemy_text(query))
        connection.commit()



if __name__ == "__main__":

    warnings.filterwarnings("ignore", category=DeprecationWarning)

    st.set_page_config( page_title="groundtruth", page_icon=None, layout="wide", initial_sidebar_state="auto", menu_items={"About": "Knowledge Base on EU AI-act"})
    db = Database()
    data = pd.read_sql(f'''
            select *
            from groundtruth
            order by id
        ''', con=db.engine).acte.unique()



    with st.sidebar:
        st.subheader("Manage the ground truth dataset")

    # col1, c2 = st.columns([8,4])
    # with col1:
    st.write(data)
