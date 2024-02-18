'''
- topics etc

'''
import os, re, json, glob
import pandas as pd
pd.options.display.max_columns = 120
pd.options.display.max_rows = 60
pd.options.display.precision = 10
pd.options.display.max_colwidth = 100
pd.options.display.width = 200
import numpy as np
import typing as t
from tqdm import tqdm

import sys
sys.path.append('./script')
sys.path.append('./script/parsing')
from regex_utils import Rgx
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns

from collections import Counter

import spacy
nlp = spacy.load("en_core_web_md")
from nltk.corpus import stopwords
stopwords = stopwords.words('english') + ['shall']
from string import punctuation
punctuation += '‘’'
punctuation = punctuation.replace('-', '')

from keybert import KeyBERT
import openai
from openai import OpenAI
import spacy
from scipy.spatial.distance import cosine
from sklearn.manifold import TSNE
from sklearn.preprocessing import MinMaxScaler


political_groups = {
    "European Conservatives and Reformists Group": "ECR",
    "Group of the European Peoples Party (Christian Democrats)": "EPP",
    "Group of the Greens/European Free Alliance": "Greens/EFA",
    "The Left group in the European Parliament - GUE/NGL": "GUE/NGL",
    "Identity and Democracy Group": "ID",
    "Renew Europe Group": "Renew",
    "Group of the Progressive Alliance of Socialists and Democrats in the European Parliament": "S&D",
}

def get_embeddings(texts: t.List[str], model: str ="text-embedding-3-small") -> t.List[float]:
    texts =[ txt.replace("\n", " ") for txt in texts]
    stuff = client.embeddings.create(input = texts, model=model)
    embeds = np.array(
        [d.embedding for d in stuff.data]
    )
    return embeds

def rm_punct(text: str) -> str:
    return ''.join([txt for txt in text if txt not in punctuation])

def extract_noun_chunks(text: str) -> t.List[str]:
    text = text.replace('\n',' ').strip()
    text = re.sub(r"\d+\.|\([a-z]{1,3}\)", '', text)
    text = re.sub(r"\s+", ' ', text).strip()
    doc = nlp(text)
    ncs = []
    for chunk in doc.noun_chunks:
        chk = chunk.text.lower().strip()
        chk = ' '.join( [ tk for tk in chk.split(' ') if tk not in stopwords  ]    )
        chk = rm_punct(chk)
        if len(chk) >2:
            chk_doc = nlp(chk)
            chk = ' '.join([token.lemma_ for token in chk_doc])
            chk = re.sub(r"\s-\s", '-', chk)
            ncs.append(chk)

    ncs = sorted(set(ncs))
    return ncs

if __name__ == "__main__":
    kw_model = KeyBERT()
    openai.api_key = os.environ["OPENAI_APIKEY"]
    client = OpenAI()

    # 3k amendments
    # data_file = "./data/json/3k_regulation.json"
    # data = pd.read_json(data_file)

    # coreper regulation
    data_file = "./data/json/regulation_full.json"
    data = pd.read_json(data_file)
    data = data[data.author == 'coreper'].copy()
    data.reset_index(inplace = True, drop = True)

    # extract title, art and paragraphs
    data['dbrd'] = data.bread.apply(json.loads)
    data['ttl']  = data.dbrd.apply(lambda b : f"TITLE {str(b.get('TTL')).zfill(4)}" if b.get('TTL') else '' )
    data['art']  = data.dbrd.apply(lambda b : f"Article {str(b.get('art')).zfill(4)}" if b.get('art') else '' )
    data['par']  = data.dbrd.apply(lambda b : f"paragraph {str(b.get('par')).zfill(4)}" if b.get('par') else '' )

    # group by articles
    arts = data.groupby(by = ['ttl','art'], as_index=False).agg({'text': '\n'.join}  )
    pars = data.groupby(by = ['ttl','art', 'par'], as_index=False).agg({'text': '\n'.join}  )

    print("-- extract noun chunks articles")
    arts['keywords'] = arts.text.apply(lambda txt : ';'.join(extract_noun_chunks(txt)))
    arts['keywords'] = arts.keywords.str.split(';')
    arts['keywords_count'] = arts.keywords.apply(lambda lst : len(lst))

    print("-- extract noun chunks paragraphs")
    pars['keywords'] = pars.text.apply(lambda txt : ';'.join(extract_noun_chunks(txt)))
    pars['keywords'] = pars.keywords.str.split(';')
    pars['keywords_count'] = pars.keywords.apply(lambda lst : len(lst))

    # aggregate all kw
    keywords = [   ]
    for i, d in pars.iterrows():
        keywords += d.keywords

    kw_count = Counter(keywords).most_common(202)[2:]

    assert 1 == 2
    # embeddings
    tokens = [kw[0] for kw in kw_count]
    frequencies = [kw[1] for kw in kw_count]
    embeds = get_embeddings(tokens)
    print(f"embeds: {embeds.shape}")

    scaler = MinMaxScaler(feature_range=(50, 5000))  # Scale frequencies to suitable sizes for bubbles
    scaled_frequencies = scaler.fit_transform(np.array(frequencies).reshape(-1, 1)).flatten()

    tsne = TSNE(n_components=2, random_state=0, perplexity = 30)
    reduced_embeddings = tsne.fit_transform(embeds)

    sns.set(style="white")

    fig, ax = plt.subplots(1,1, figsize=(12, 8))
    # plt.figure(figsize=(12, 8))
    for i, keyword in enumerate(tokens[:100]):
        plt.scatter(reduced_embeddings[i, 0], reduced_embeddings[i, 1], s=scaled_frequencies[i], label=keyword, alpha = 0.5)
        plt.text(reduced_embeddings[i, 0], reduced_embeddings[i, 1], keyword, fontsize=9)

    # plt.xlabel('t-SNE Feature 1')
    # plt.ylabel('t-SNE Feature 2')

    ax.tick_params(bottom=False)

    plt.title('Keywords Visualization based on Similarity and Frequency')
    sns.despine(left=True, bottom=True)
    plt.tight_layout()
    plt.show()

    # --------------------------------------------
    #  TSNE
    # --------------------------------------------
    from sklearn.manifold import TSNE

    df = pd.read_csv('output/embedded_1k_reviews.csv')
    matrix = df.ada_embedding.apply(eval).to_list()

    # Create a t-SNE model and transform the data
    tsne = TSNE(n_components=2, perplexity=15, random_state=42, init='random', learning_rate=200)
    vis_dims = tsne.fit_transform(matrix)

    colors = ["red", "darkorange", "gold", "turquiose", "darkgreen"]
    x = [x for x,y in vis_dims]
    y = [y for x,y in vis_dims]
    color_indices = df.Score.values - 1

    colormap = matplotlib.colors.ListedColormap(colors)
    plt.scatter(x, y, c=color_indices, cmap=colormap, alpha=0.3)
    plt.title("Amazon ratings visualized in language using t-SNE")

    # extract noun chunks with spacy
    print()
    kws = []
    for k in range(1,3):
        ngrams = (k,k)
        kws += kw_model.extract_keywords(text,
                keyphrase_ngram_range=ngrams,
                stop_words='english',
                use_mmr=True, diversity=0.1,
                top_n = 10
            )
    tokens = sorted([ kw[0] for kw   in  kws if (kw[1] > 0.25)])
    kws = []
    for token in tokens:
        token = ' '.join( [ tk for tk in token.split(' ') if tk not in stopwords    ]    )
        if len(token) >1:
            kws.append(token)

    kws = sorted(list(set(kws)))

    tokens = sorted(set(ncs + kws))

    arts.loc[i,'kw'] = ';'.join(sorted(list(set(ncs + kws))))

    kws = sorted(list(set(ncs + kws)))
    kw_embeddings = [get_embedding(kw) for kw in tokens]

    text_embedding = get_embedding(art.text)
    similarity_scores = [1 - cosine(text_embedding, kwemb) for kwemb in kw_embeddings]

    # Sort and select top N noun chunks
    kws_scores = list(zip(kws, similarity_scores))
    sorted_kws = sorted(kws_scores, key=lambda x: x[1], reverse=True)

    top_n = 20  # Adjust based on your needs
    top_n_chunks = sorted_chunks[:top_n]



    # --------------------------------------------------------------------------------
    # Keyword extraction with KeyBert
    # --------------------------------------------------------------------------------
    for i, art in arts.iterrows():
        kws = []
        for k in range(1,4):
            ngrams = (k,k)
            kws += kw_model.extract_keywords(art.text,
                    keyphrase_ngram_range=ngrams,
                    stop_words='english',
                    use_mmr=True, diversity=0.7,
                    top_n = 20
                )
        arts.loc[i,'kws'] = ';'.join([ kw[0] for kw   in  kws  ])




    # --------------------------------------------------------------------------------
    # rank noun chunks with embeddings similarity
    # --------------------------------------------------------------------------------

    # Load the model


    # Process the text
    text = arts.loc[7].text
    doc = nlp(text)
    # Get noun chunks and their embeddings
    nlp = spacy.load("en_core_web_md")
    chunks = []
    for chunk in doc.noun_chunks:
        print(chunk)
        rgx = r"^\s*the\s+"
        chunk = re.sub(r"^\s*the\s+", "", str(chunk), flags=re.IGNORECASE)
        chunks.append(chunk)

    noun_chunks = list(set([chunk.text for chunk in doc.noun_chunks]))
    noun_chunk_embeddings = [get_embedding(chunk) for chunk in noun_chunks]

    # processed_text = ' '.join( [token.text for token in doc if token.pos_ in ('NOUN', 'ADJ', 'VERB') and not token.is_stop])
    # doc = nlp(processed_text)
    # Calculate similarities with the text embedding
    text_embedding = get_embedding(text)
    similarity_scores = [1 - cosine(text_embedding, chunk_embedding) for chunk_embedding in noun_chunk_embeddings]

    # Sort and select top N noun chunks
    chunk_scores = list(zip(noun_chunks, similarity_scores))
    sorted_chunks = sorted(chunk_scores, key=lambda x: x[1], reverse=True)
    top_n = 20  # Adjust based on your needs
    top_n_chunks = sorted_chunks[:top_n]

    # Print or use the top N chunks
    for chunk, score in top_n_chunks:
        print(f"{chunk}: {score}")






    import gensim
    import nltk
    from gensim import corpora
    from gensim.models import LdaModel
    from gensim.utils import simple_preprocess
    from nltk.corpus import stopwords
    from pypdf import PdfReader
    from langchain.chains import LLMChain
    from langchain.prompts import ChatPromptTemplate
    from langchain.llms import OpenAI

    def preprocess(text, stop_words):
        result = []
        for token in simple_preprocess(text, deacc=True):
            if token not in stop_words and len(token) > 3:
                result.append(token)
        return result

    def preprocess(doc):
        return ' '.join( [token.text for token in doc if token.pos_ in ('NOUN', 'ADJ', 'VERB') and not token.is_stop])


    def get_topic_lists(texts, num_topics, words_per_topic):
        # Preprocess the documents

        # Create a dictionary and a corpus
        dictionary = corpora.Dictionary(texts)
        corpus = [dictionary.doc2bow(doc) for doc in texts]

        # Build the LDA model
        lda_model = LdaModel(
                corpus,
                num_topics=num_topics,
                id2word=dictionary,
                passes=25
            )

        # Retrieve the topics and their corresponding words
        topics = lda_model.print_topics(num_words=words_per_topic)

        # Store each list of words from each topic into a list
        topics_ls = []
        for topic in topics:
            words = topic[1].split("+")
            topic_words = [word.split("*")[1].replace('"', '').strip() for word in words]
            topics_ls.append(topic_words)

        return topics_ls


    def topics_summary(llm, topics):

        string_lda = ""
        for list in topics:
            string_lda += str(list) + "\n"

        # Create the template
        template_string = '''
    You are an expert in Artifical Intelligence and European Union policy making.
    You are given a list of {num_topics} topics related to AI regulation.
    Each topic consists of a list of words.
    Your task is to describe each topic in a simple sentence and write down three possible different subthemes.

    Do not provide an introduction or a conclusion, only describe the topics.
    Do not mention the word "topic" when describing the topics.

    Use the following template for the response.
    <topic number>: sentence describing the topic
    a) Phrase describing the first subtheme
    b) Phrase describing the second subtheme
    c) Phrase describing the third subtheme

    Topics:
    """{string_lda}"""
    '''

        # LLM call
        prompt_template = ChatPromptTemplate.from_template(template_string)
        chain = LLMChain(llm=llm, prompt=prompt_template)
        response = chain.invoke({ "string_lda" : string_lda, "num_topics" : num_topics })

        return response



    texts = arts.text.values

    num_topics = 10
    words_per_topic = 20

    topics = get_topic_lists(texts, num_topics, words_per_topic)

    llm = OpenAI(openai_api_key=os.environ["OPENAI_APIKEY"], max_tokens=-1)

    summary = topics_summary(llm, topics)
    print(summary)