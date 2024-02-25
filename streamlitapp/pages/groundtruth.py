"""
"""
import os, re, json, glob
import time, datetime
import pandas as pd
import numpy as np
import tempfile

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


def select_qa(id):
    query = f"""
        update groundtruth set active = not active where id = {id}
    """
    with db.engine.connect() as connection:
        result = connection.execute(sqlalchemy_text(query))
        connection.commit()


if __name__ == "__main__":
    warnings.filterwarnings("ignore", category=DeprecationWarning)

    st.set_page_config(
        page_title="groundtruth",
        page_icon=None,
        layout="wide",
        initial_sidebar_state="auto",
        menu_items={"About": "Knowledge Base on EU AI-act"},
    )

    db = Database()
    # active_connections = db.engine.pool.status().checkedout()

    data = pd.read_sql(
        f"""
            select *
            from groundtruth
            order by id
        """,
        con=db.engine,
    )

    with st.sidebar:
        st.subheader("Manage the groundtruth dataset")
        answer_type_options = ["--"] + sorted(data.answer_type.unique())
        answer_type = st.selectbox(
            "Answer type",
            answer_type_options,
            index=0
            if st.session_state.get("answer_type_key") is None
            else answer_type_options.index(st.session_state.get("answer_type_key")),
            key="answer_type_key",
            help="""short answers vs longer expert answers""",
        )

        active_options = ["--"] + sorted(["active", "disabled"])
        active_flag = st.selectbox(
            "Active /disabled",
            active_options,
            index=0
            if st.session_state.get("active_key") is None
            else active_options.index(st.session_state.get("active_key")),
            key="active_key",
            help="""active / disabled q&as""",
        )

    if answer_type is not None:
        if answer_type != "--":
            data = data[data.answer_type == answer_type].copy()

    if active_flag is not None:
        if active_flag != "--":
            data = data[data.active == (active_flag == "active")].copy()

    data.sort_values(by=["id", "active"], inplace=True)

    hcol1, hcol2, hcol3 = st.columns([1, 1, 8])
    with hcol1:
        st.write(f"{data.shape[0]} q&as")
    with hcol2:
        csv = data.to_csv(index=False).encode("utf-8")
        filename = f"groundtruth_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        st.download_button("to csv", csv, filename, "text/csv", key="download-csv")

    for i, d in data.iterrows():
        col1, col2, col3 = st.columns([1, 4, 8])
        with col1:
            st.checkbox(
                str(d["id"]),
                value=d["active"] == 1,
                on_change=select_qa,
                args=(d["id"],),
            )
        with col2:
            st.write(f"_{d.question}_")
            st.caption(f"{d.answer_type}, {d.source}")
        with col3:
            st.write(d.answer)

    db.close()

    with st.sidebar:
        active_connections = db.engine.pool.status()
        st.write(f"-- active connections {active_connections}")
        st.write(
            """
- TODO: add a new Q&A
- TODO: edit Q&A
- TODO: review / comment Q&A
"""
        )
