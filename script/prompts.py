from langchain.prompts import HumanMessagePromptTemplate

NEW_SEED_QUESTION = HumanMessagePromptTemplate.from_template(
    """\
You are a AI and EU policy expert.

Your task is to formulate a question from the given context.

- The question should make sense to humans even when read without the given context.
- The question shoud only have one simple sentence and independent clause.
- The question should be short and straight to the point
- The question should be shorter than 15 words

Write in colloquial, everyday English in a concise and simple style.

context:{context}
"""
)

NEW_FILTER_QUESTION = HumanMessagePromptTemplate.from_template(
    """\
Determine if the given question
- contains only one independent clause

Specify reason and verdict in a valid json format.

question: What is the keyword that best describes the paper's focus in natural language understanding tasks?
{{"reason":"The specific paper being referred to is not mentioned in the question.", "verdict": "No"}}

question:{question}
"""  # noqa: E501
)

CONTEXT_FORMULATE = HumanMessagePromptTemplate.from_template(
    """Please extract relevant sentences from the provided context that can potentially help answer the following question.
Do not make any change to extracted sentences.
Remember to extract the author of the provided context when mentioned.

question:{question}
context:\n{context}
author and candidate sentences:\n
"""  # noqa: E501
)


NEW_ANSWER_FORMULATE = HumanMessagePromptTemplate.from_template(
    """\
You are an expert in EU policy making and in particular the Artificial Intelligence Act.
Answer the question using the information from the given context.

First write a short answer: one line, very simple to understand, in a colloquial everyday English.

Then, write an expert answer with more details.
- Develop your answer by giving the definition of specific directives, regulations or articles even when the context provides no such definition.
- mention the author if explicit
- if you don't know, say so, do not invent or imagine anything.
- Write in layman terms, in everyday simple English.


question:{question}
context:{context}

Write both short and expert answers in a valid json format.

{{
    'short': {{your short answer}},
    'expert': {{your expert answer}},
}}

"""  # noqa: E501
)

# ----------

REASONING_QUESTION = HumanMessagePromptTemplate.from_template(
    """\
You are a prompt rewriter. You will be provided with a question and a long context.Your task to is to complicate the given question to improve the difficulty of answering.
You should do complicate the question by rewriting question into a multi-hop reasoning question based on the provided context. The question should require the reader to make multiple logical connections or inferences using the information available in given context.
Here are some strategies to create multi-hop questions:

   - Bridge related entities: Identify information that relates specific entities and frame question that can be answered only by analysing information of both entities.

   - Use Pronouns: identify (he, she, it, they) that refer to same entity or concepts in the context, and ask questions that would require the reader to figure out what pronouns refer to.

   - Refer to Specific Details: Mention specific details or facts from different parts of the context including tables, code, etc and ask how they are related.

   - Pose Hypothetical Scenarios: Present a hypothetical situation or scenario that requires combining different elements from the context to arrive at an answer.

Rules to follow when rewriting question:
1. Ensure that the rewritten question can be answered entirely from the information present in the contexts.
2. Do not frame questions that contains more than 15 words. Use abbreviation wherever possible.
3. Make sure the question is clear and unambiguous.
4. phrases like 'based on the provided context','according to the context',etc are not allowed to appear in the question.

question: {question}
CONTEXTS:
{context}

Multi-hop Reasoning Question:
"""  # noqa: E501
)

MULTICONTEXT_QUESTION = HumanMessagePromptTemplate.from_template(
    """\
You are a prompt rewriter. You will be provided with a question and two set of contexts namely context1 and context2.
Your task is to complicate the given question in a way that answering it requires information derived from both context1 and context2.
Follow the rules given below while rewriting the question.
    1. The rewritten question should not be very long. Use abbreviation wherever possible.
    2. The rewritten question must be reasonable and must be understood and responded by humans.
    3. The rewritten question must be fully answerable from information present in context1 and context2.
    4. Read and understand both contexts and rewrite the question so that answering requires insight from both context1 and context2.
    5. phrases like 'based on the provided context','according to the context?',etc are not allowed to appear in the question.

question:\n{question}
context1:\n{context1}
context2:\n{context2}
"""  # noqa: E501
)


CONDITIONAL_QUESTION = HumanMessagePromptTemplate.from_template(
    """\
Rewrite the provided question to increase its complexity by introducing a conditional element.
The goal is to make the question more intricate by incorporating a scenario or condition that affects the context of the question.
Follow the rules given below while rewriting the question.
    1. The rewritten question should not be longer than 25 words. Use abbreviation wherever possible.
    2. The rewritten question must be reasonable and must be understood and responded by humans.
    3. The rewritten question must be fully answerable from information present context.
    4. phrases like 'provided context','according to the context?',etc are not allowed to appear in the question.
for example,
question: What are the general principles for designing prompts in LLMs?
Rewritten Question:how to apply prompt designing principles to improve LLMs performance in reasoning tasks

question:{question}
context:\n{context}
Rewritten Question
"""  # noqa: E501
)


COMPRESS_QUESTION = HumanMessagePromptTemplate.from_template(
    """\
Rewrite the following question to make it more indirect and shorter while retaining the essence of the original question. The goal is to create a question that conveys the same meaning but in a less direct manner.
The rewritten question should shorter so use abbreviation wherever possible.
Original Question:
{question}

Indirectly Rewritten Question:
"""  # noqa: E501
)


CONVERSATION_QUESTION = HumanMessagePromptTemplate.from_template(
    """\
Reformat the provided question into two separate questions as if it were to be part of a conversation. Each question should focus on a specific aspect or subtopic related to the original question.
question: What are the advantages and disadvantages of remote work?
Reformatted Questions for Conversation: What are the benefits of remote work?\nOn the flip side, what challenges are encountered when working remotely?
question:{question}

Reformatted Questions for Conversation:
"""  # noqa: E501
)

SCORE_CONTEXT = HumanMessagePromptTemplate.from_template(
    """Evaluate the provided context and assign a numerical score between 0 and 10 based on the following criteria:
1. Award a high score to context that thoroughly delves into and explains concepts.
2. Assign a lower score to context that contains excessive references, acknowledgments, external links, personal information, or other non-essential elements.
Output the score only.
Context:
{context}
Score:
"""  # noqa: E501
)
