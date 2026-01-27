'''
tutorial
https://blog.logrocket.com/langsmith-test-llms-ai-applications/
'''

# create a langsmith client
from langsmith import Client
from langchain.chat_models import ChatOpenAI
# from langchain.agents import AgentType, initialize_agent, load_tools
import uuid
import os

from langchain.smith import run_on_dataset
from langchain.smith import RunEvalConfig

if __name__ == "__main__":
    client = Client()

    assert 1 == 2

    # create project
    # client.list_projects(), client.read_project()
    p_name = 'flashcards-generator-daecbf5c-584f-4c7e-863d-fea7201528b8'
    os.environ["LANGCHAIN_PROJECT"] = p_name
    # session = client.create_project(
    #     project_name='flashcards-generator-daecbf5c-584f-4c7e-863d-fea7201528b8',
    #     description="A project that generates flashcards from user input",
    # )

    session = client.read_project(project_name = p_name)

    llm = ChatOpenAI(temperature=0)

    if False:
        message = llm.invoke("Do you know how to generate flashcards?")
        message.content
        prompt = f"Summarize this text: {message.content}"
        summary = llm.invoke(prompt)
        summary.content

    if False:
        # creating unlablled dataset
        # dataset : key, value
        dataset_name = "aiact_learning_fundamentals"

        # Creating a blank dataset
        dl_dataset = client.create_dataset(
            dataset_name=dataset_name,
            description="A deck containing flashcards on The Ai act",
            data_type="kv",
        )

        # storing inputs only
        example_inputs = [
            "Generate a single flashcard on the definition of AI",
            "Generate a single flashcard on the definition of Biometric systems",
            "Generate a single flashcard on the condition for being labeled as a high risk AI system",
        ]

        for ex in example_inputs:
            # Each example input must be unique
            client.create_example(
                inputs={"input": ex},
                outputs=None,
                dataset_id=dl_dataset.id,
            )



        results = run_on_dataset(
            client=client,
            dataset_name=dataset_name,
            llm_or_chain_factory=llm,
            project_name="unlabeled_test",
        )

        # eval

        # List the eval criteria
        '''
        to list all the criterias
        from langchain.evaluation import Criteria
        list(Criteria)

        '''

        eval_config = RunEvalConfig(
            evaluators=[
                RunEvalConfig.Criteria("conciseness"),
                RunEvalConfig.Criteria("coherence"),
                RunEvalConfig.Criteria("relevance"),
            ]
        )


        results = run_on_dataset(
            client=client,
            dataset_name=dataset_name,
            llm_or_chain_factory=llm,
            evaluation=eval_config,
            project_name="criteria_test",
        )


    # creating labelled dataset
    dataset_name = "AI-Act-Q&A"

    csv_path = "./data/groundtruth/groundtruth_20240226_114221.csv"
    input_keys = ["question"]
    output_keys = ["answer"]

    csv_dataset = client.upload_csv(
        csv_file=csv_path,
        input_keys=["question"],
        output_keys=["answer"],
        name=dataset_name,
        data_type="kv",
    )

    # creating custom evaluation
    eval_config = RunEvalConfig(
        evaluators=[
            RunEvalConfig.Criteria(
                {"has_reference": "Does the answer contain a reference to a specific article, section, or any part of a EU legislation ?"}
            ),
            RunEvalConfig.Criteria(
                {"is_complex_question": "Is the question complex with dependent sentence clause?"}
            ),
        ]
    )
    # run evaluation on dataset
    results = run_on_dataset(
        client,
        dataset_name,
        llm,
        evaluation=eval_config,
        project_name="custom_criteria_test_csv",
    )
