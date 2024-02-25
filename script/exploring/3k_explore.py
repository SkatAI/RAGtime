"""
- stability of proposers vs groups
- relative activities of groups: number of amendments
- articles / recitals with most amendments
- for a given article / recital, how many amendments resp to groups
- main topic per group

topics visualizations
https://towardsdatascience.com/advanced-visualisations-for-text-data-analysis-fc8add8796e2

- whole AI act
- per groups in 3k
- per adopted amendments
-

1) match items with [kw]
- per items: generate list of kw: Keybert, noun chunks, topic modeling
- for each item select 10 best or above threshold

2) viz : TSNE / PCA
from
kws, embeddings and categories
-

3) per article and recital: find category



per item, extract kw : topics,


"""
import os, re, json, glob
import pandas as pd

pd.options.display.max_columns = 120
pd.options.display.max_rows = 60
pd.options.display.precision = 10
pd.options.display.max_colwidth = 100
pd.options.display.width = 200
import numpy as np
import typing as t

import sys

sys.path.append("./script")
sys.path.append("./script/parsing")
from regex_utils import Rgx
import matplotlib.pyplot as plt
import seaborn as sns

from collections import Counter

if __name__ == "__main__":
    political_groups = {
        "European Conservatives and Reformists Group": "ECR",
        "Group of the European Peoples Party (Christian Democrats)": "EPP",
        "Group of the Greens/European Free Alliance": "Greens/EFA",
        "The Left group in the European Parliament - GUE/NGL": "GUE/NGL",
        "Identity and Democracy Group": "ID",
        "Renew Europe Group": "Renew",
        "Group of the Progressive Alliance of Socialists and Democrats in the European Parliament": "S&D",
    }

    data_file = "./data/json/3k_regulation.json"
    data = pd.read_json(data_file)

    # reorder gpe as categories
    gpe_order_list = ["GUE/NGL", "S&D", "Greens/EFA", "Renew", "EPP", "ECR", "ID"]
    data["gpe"] = data["gpe"].astype("category")
    data["gpe"] = data["gpe"].cat.set_categories(gpe_order_list, ordered=True)

    print(f"loaded {data.shape} records")
    print(f"There's a total of {data.shape[0]} amendments.")

    data["section"] = "other"
    for i, d in data.iterrows():
        if Rgx.starts_with("Recital", d.title):
            data.loc[i, "section"] = "recital"
        elif Rgx.starts_with("Article", d.title):
            data.loc[i, "section"] = "regulation"
        elif Rgx.starts_with("Annex", d.title):
            data.loc[i, "section"] = "annex"

    data["section"] = data["section"].astype("category")
    data["section"] = data["section"].cat.set_categories(["recital", "regulation", "annex", "other"], ordered=True)

    print("- amendments per section")
    print(data.section.value_counts())
    # --------------------------------------------------------------------------------
    #  Stability of proposers vs groups
    # --------------------------------------------------------------------------------
    print(f"- {len(data.proposers.unique())} sets of proposers for {len(political_groups)} political groups")
    data["proposer_count"] = data.proposers.apply(lambda p: len(p.split(",")))
    print(
        f"- proposers sets range from {min(data['proposer_count'])} member to {max(data['proposer_count'])} members with on average {np.round(np.mean(data['proposer_count']),1)}, median {np.median(data['proposer_count'])} "
    )
    data["proposer_list"] = data.proposers.apply(lambda p: p.split(","))

    proposers = []
    for i, d in data.iterrows():
        proposers += d.proposer_list
    proposers = [pro.strip() for pro in proposers if pro.strip() != ""]

    # most influential person
    influence = pd.DataFrame(Counter(proposers).most_common(), columns=["name_", "num_amendments"])

    prop_groups = data[["proposers", "gpe"]].drop_duplicates().copy()
    prop_groups["proposer_list"] = prop_groups.proposers.apply(lambda p: p.split(","))

    affiliations = []
    for i, pg in prop_groups.iterrows():
        for prop in pg.proposer_list:
            affiliations.append({"name": prop, "gpe": pg.gpe})

    affiliations = pd.DataFrame(affiliations)
    affiliations.drop_duplicates(inplace=True)

    affiliations = {d["name"].strip(): d.gpe for _, d in affiliations.iterrows() if d["name"].strip() != ""}

    influence["gpe"] = influence.name_.apply(lambda d: affiliations[d])
    influence["name_gpe"] = influence.apply(lambda d: " - ".join([d.name_, d.gpe]), axis=1)

    plt.figure(figsize=(8, 8))
    barplot = sns.barplot(
        x="num_amendments",
        y="name_gpe",
        # hue="gpe",
        # orient = 'h',
        data=influence.head(20),
    )

    plt.title("top 20 Proposers")
    plt.xlabel("number of Amendments")
    plt.ylabel("Proposer")

    # plt.legend(title="Group")
    plt.grid(axis="x", linestyle="--")
    plt.tight_layout()
    plt.show()

    plt.savefig("./img/top_proposers.png")

    # --------------------------------------------------------------------------------
    #  groups with most amendments
    # --------------------------------------------------------------------------------

    plt_data = (
        data[data.section != "other"][["gpe", "section", "number"]]
        .groupby(by=["gpe", "section"])
        .count()
        .reset_index()
        .sort_values(by=["gpe", "section"])
    )
    plt.figure(figsize=(12, 6))
    barplot = sns.barplot(
        y="number",
        x="gpe",
        hue="section",
        orient="v",
        data=plt_data,
    )

    plt.title("number of Amendments per Group and section")
    plt.ylabel("number of Amendments")
    plt.xlabel("Group")

    plt.legend(title="Section")
    plt.grid(axis="y", linestyle="--")
    plt.tight_layout()
    for p in barplot.patches:
        height = p.get_height()
        if height > 0:
            plt.text(p.get_x() + p.get_width() / 2.0, height + 5, int(height), ha="center")
    plt.show()
    plt.savefig("./img/num_amendments_vs_gpe_section.png")

    # --------------------------------------------------------------------------------
    #  article / recital / annex with most amendments
    # --------------------------------------------------------------------------------
    data["item"] = data.title.apply(lambda d: " ".join(d.split(" ")[:2]))
    data.item.value_counts()
