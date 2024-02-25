# To run the example below, ensure the environment variable OPENAI_API_KEY is set
import openai
from langsmith.run_trees import RunTree

# This can be a user input to your app
question = "Can you summarize this morning's meetings?"
# This can be retrieved in a retrieval step
context = "During this morning's meeting, we solved all world conflict."


messages = [
    {
        "role": "system",
        "content": "You are a helpful assistant. Please respond to the user's request only based on the given context.",
    },
    {"role": "user", "content": f"Question: {question}\nContext: {context}"},
]

# Create a top-level run
pipeline = RunTree(name="Chat Pipeline", run_type="chain", inputs={"question": question})

# Create a child run
child_llm_run = pipeline.create_child(
    name="OpenAI Call",
    run_type="llm",
    inputs={"messages": messages},
)

# Generate a completion
client = openai.Client()
chat_completion = client.chat.completions.create(model="gpt-3.5-turbo", messages=messages)

# End the runs and log them
child_llm_run.end(outputs=chat_completion)
child_llm_run.post()

pipeline.end(outputs={"answer": chat_completion.choices[0].message.content})
pipeline.post()
