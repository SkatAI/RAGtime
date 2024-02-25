"""
review questions available in cloud storage
- add to ground truth
- delete question in storage

"""
import streamlit as st
import os, re, json
import time, datetime
import pandas as pd
import numpy as np
import psycopg2
from sqlalchemy import create_engine
from sqlalchemy import text as sqlalchemy_text
import warnings
import sys

sys.path.append("./script")
from db_utils import Database


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
            from live_qa
            order by id
        """,
        con=db.engine,
    )

    data["search"] = data["search"].apply(lambda d: json.loads(d))
    data["search_type"] = data["search"].apply(lambda d: d["search_type"])
    data["src_model"] = data["search"].apply(lambda d: d["model"])
    data["context"] = data["context"].apply(lambda d: json.loads(d))
    data["filters"] = data["filters"].apply(lambda d: json.loads(d))

    with st.sidebar:
        st.subheader("Manage the live Q&As")
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

        src_model_options = ["--"] + sorted(data.src_model.unique())
        src_model = st.selectbox(
            "model",
            src_model_options,
            index=0
            if st.session_state.get("src_model_key") is None
            else src_model_options.index(st.session_state.get("src_model_key")),
            key="src_model_key",
            help="""Model used""",
        )

    if answer_type is not None:
        if answer_type != "--":
            data = data[data.answer_type == answer_type].copy()

    if src_model is not None:
        if src_model != "--":
            data = data[data.src_model == src_model].copy()

    data.sort_values(by="created_at", ascending=False, inplace=True)

    st.write(f"{data.shape[0]} q&a")

    for i, d in data.iterrows():
        col1, col2, col3 = st.columns([4, 4, 8])
        with col1:
            st.caption(f"[{d.id}] {d.created_at}")
            st.caption(f"{d.answer_type}")
            st.caption(f"{d['search']}")
        with col2:
            st.write(f"_{d.query}_")
        with col3:
            st.write(d.answer)

    db.close()

    with st.sidebar:
        active_connections = db.engine.pool.status()
        st.write(f"-- active connections {active_connections}")

        st.write(
            """
- TODO: add to groundtruth button
- TODO: flag as duplicate, discarded, ...
- TODO: export as csv
- TODO: review / comment Q&A
"""
        )
