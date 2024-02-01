from __future__ import annotations

import typing as t
import warnings
from collections import defaultdict, namedtuple
from dataclasses import dataclass,  asdict
import json
try:
    from llama_index.indices.query.embedding_utils import get_top_k_embeddings
    from llama_index.node_parser import SimpleNodeParser
    from llama_index.readers.schema import Document as LlamaindexDocument
    from llama_index.schema import BaseNode
except ImportError:
    raise ImportError(
        "llama_index must be installed to use this function. "
        "Please, install it with `pip install llama_index`."
    )

import numpy as np
import numpy.testing as npt
import pandas as pd
from langchain.embeddings import OpenAIEmbeddings
from langchain.embeddings.base import Embeddings
from langchain.prompts import ChatPromptTemplate
from langchain.schema.document import Document as LangchainDocument
from numpy.random import default_rng
from tqdm import tqdm

from ragas.llms import llm_factory
from ragas.testset.prompts import (
    ANSWER_FORMULATE,
    COMPRESS_QUESTION,
    CONDITIONAL_QUESTION,
    CONTEXT_FORMULATE,
    CONVERSATION_QUESTION,
    FILTER_QUESTION,
    MULTICONTEXT_QUESTION,
    REASONING_QUESTION,
    SCORE_CONTEXT,
    SEED_QUESTION,
)

from prompts import (
    NEW_SEED_QUESTION,
    NEW_FILTER_QUESTION,
    NEW_ANSWER_FORMULATE,
)

from ragas.testset.utils import load_as_score
from ragas.utils import load_as_json

if t.TYPE_CHECKING:
    from ragas.llms.base import RagasLLM


DEFAULT_TEST_DISTRIBUTION = {
    "simple": 0.4,
    "reasoning": 0.2,
    "multi_context": 0.2,
    "conditional": 0.2,
}

question_deep_map = {
    "reasoning": "_reasoning_question",
    "conditional": "_condition_question",
}

DataRowPatched = namedtuple(
    "DataRowPatched",
    [
        "question",
        "ground_truth_context",
        "answer",
        "context",
        "question_type",
        "episode_done",
    ],
)


@dataclass
class TestDatasetPatched:
    """
    TestDataset class
    """

    test_data: t.List[DataRowPatched]

    def to_pandas(self) -> pd.DataFrame:
        data_samples = []
        for data in self.test_data:
            data = {
                "question": data.question,
                "ground_truth_context": data.ground_truth_context,
                "answer": data.answer,
                "context": data.context,
                "question_type": data.question_type,
                "episode_done": data.episode_done,
            }
            data_samples.append(data)

        return pd.DataFrame.from_records(data_samples)

    def to_jsonl(self, filename: str) -> None:
        with open(filename, 'w') as file:
            for data in self.test_data:
                json_str = json.dumps(asdict(data), indent=4)
                file.write(json_str + '\n')


from ragas.testset.utils import load_as_score
from ragas.utils import load_as_json

def _filter_question_patched(self, question: str) -> bool:
    print(f"q: {question}")
    human_prompt = NEW_FILTER_QUESTION.format(question=question)
    prompt = ChatPromptTemplate.from_messages([human_prompt])

    results = self.critic_llm.generate(prompts=[prompt])
    results = results.generations[0][0].text.strip()
    json_results = load_as_json(results)
    if json_results.get("verdict") == 'No':
        print(f"question not valid: \n {question} \n reason: {json_results.get('reason')} ")
    return json_results.get("verdict") != "No"

def _seed_question_patched(self, context: str) -> str:
    human_prompt = NEW_SEED_QUESTION.format(context=context)
    prompt = ChatPromptTemplate.from_messages([human_prompt])
    results = self.generator_llm.generate(prompts=[prompt])
    return results.generations[0][0].text.strip()

def _generate_answer_patched(self, question: str, context: t.List[str]) -> t.List[str]:
    return [
        self._qc_template(NEW_ANSWER_FORMULATE, qstn, context[i])
        for i, qstn in enumerate(question.split("\n"))
    ]


def generate_patched(
    self,
    documents: t.List[LlamaindexDocument] | t.List[LangchainDocument],
    test_size: int,
) -> TestDatasetPatched:
    if not isinstance(documents[0], (LlamaindexDocument, LangchainDocument)):
        raise ValueError(
            "Testset Generatation only supports LlamaindexDocuments or LangchainDocuments"  # noqa
        )

    if isinstance(documents[0], LangchainDocument):
        # cast to LangchainDocument since its the only case here
        documents = t.cast(t.List[LangchainDocument], documents)
        documents = [
            LlamaindexDocument.from_langchain_format(doc) for doc in documents
        ]
    # Convert documents into nodes
    node_parser = SimpleNodeParser.from_defaults(
        chunk_size=self.chunk_size, chunk_overlap=0, include_metadata=True
    )
    documents = t.cast(t.List[LlamaindexDocument], documents)
    document_nodes: t.List[BaseNode] = node_parser.get_nodes_from_documents(
        documents=documents
    )
    # maximum 1 seed question per node
    if test_size > len(document_nodes):
        raise ValueError(
            """Maximum possible number of samples exceeded,
                            reduce test_size or add more documents"""
        )

    available_nodes = document_nodes
    doc_nodes_map = self._generate_doc_nodes_map(document_nodes)
    count_neighbours = sum(len(val) > 1 for _, val in doc_nodes_map.items())
    if count_neighbours < len(documents) // 2:
        warnings.warn("Most documents are too short")

    count = 0
    samples = []

    pbar = tqdm(total=test_size)
    while count < test_size and available_nodes != []:
        evolve_type = self._get_evolve_type()
        curr_node = self.rng.choice(np.array(available_nodes), size=1)[0]
        available_nodes = self._remove_nodes(available_nodes, [curr_node])

        neighbor_nodes = doc_nodes_map[curr_node.source_node.node_id]

        # Append multiple nodes randomly to remove chunking bias
        size = self.rng.integers(1, 3)
        nodes = (
            self._get_neighbour_node(curr_node, neighbor_nodes)
            if size > 1 and evolve_type != "multi_context"
            else [curr_node]
        )

        text_chunk = " ".join([node.get_content() for node in nodes])
        # score = self._filter_context(text_chunk)
        # if not score:
        #     continue
        seed_question = self._seed_question(text_chunk)
        is_valid_question = self._filter_question(seed_question)
        if not is_valid_question:
            continue

        if evolve_type == "multi_context":
            # Find most similar chunk in same document
            node_embedding = self._embed_nodes([nodes[-1]])
            neighbor_nodes = self._remove_nodes(neighbor_nodes, nodes)
            neighbor_emb = self._embed_nodes(neighbor_nodes)

            _, indices = get_top_k_embeddings(
                list(node_embedding.values())[0],
                list(neighbor_emb.values()),
                similarity_cutoff=self.threshold / 10,
            )
            if indices:
                # type cast indices from list[Any] to list[int]
                indices = t.cast(t.List[int], indices)
                best_neighbor = neighbor_nodes[indices[0]]
                question = self._multicontext_question(
                    question=seed_question,
                    context1=text_chunk,
                    context2=best_neighbor.get_content(),
                )
                text_chunk = "\n".join([text_chunk, best_neighbor.get_content()])
            else:
                continue

        # for reasoning and conditional modes, evolve question with the
        # functions from question_deep_map
        else:
            evolve_fun = question_deep_map.get(evolve_type)
            question = (
                getattr(self, evolve_fun)(seed_question, text_chunk)
                if evolve_fun
                else seed_question
            )

        # compress question or convert into conversational questions
        if evolve_type != "simple":
            prob = self.rng.uniform(0, 1)
            if self.chat_qa and prob <= self.chat_qa:
                question = self._conversational_question(question=question)
            else:
                question = self._compress_question(question=question)

        # is_valid_question = self._filter_question(question)
        if is_valid_question:
            context = self._generate_context(question, text_chunk)
            is_conv = len(context) > 1
            answer = self._generate_answer(question, context)
            for i, (qstn, ctx, ans) in enumerate(
                zip(question.split("\n"), context, answer)
            ):
                episode_done = False if is_conv and i == 0 else True
                samples.append(
                    DataRowPatched(qstn, [ctx], [ans], [text_chunk], evolve_type, episode_done)
                )
            count += 1
            pbar.update(count)

    return TestDatasetPatched(test_data=samples)
