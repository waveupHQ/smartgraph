import asyncio
import os

from dotenv import load_dotenv

from smartgraph import Pipeline
from smartgraph.components import CompletionComponent
from smartgraph.components.input_handlers import TextInputHandler
from smartgraph.logging import SmartGraphLogger

# Load environment variables
load_dotenv()

# Set up logging
logger = SmartGraphLogger.get_logger()
logger.set_level("INFO")


def create_pipeline():
    pipeline = Pipeline("LLM Pipeline")

    input_handler = TextInputHandler("TextInput")
    completion_component = CompletionComponent(
        "GPT_Completion",
        model="gpt-4o-mini",
        temperature=0.7,
        api_key=os.getenv("OPENAI_API_KEY"),
        system_context="You are a helpful assistant specialized in Python programming.",
        max_tokens=4000,
    )

    pipeline.add_component(input_handler)
    pipeline.add_component(completion_component)
    pipeline.connect_components("TextInput", "GPT_Completion")

    return pipeline


async def process_input(pipeline, input_text: str) -> dict:
    logger.info(f"Processing input: {input_text}")
    result = await pipeline.execute(input_text)
    return result


async def run_example():
    pipeline = create_pipeline()
    completion_component = pipeline.components["GPT_Completion"]

    # Process a series of inputs
    inputs = [
        "What are the key features of Python?",
        "Explain the concept of reactive programming in Python.",
    ]

    for input_text in inputs:
        result = await process_input(pipeline, input_text)
        print(f"Input: {input_text}")
        print(
            f"Output: {result.get('ai_response', 'Error: ' + result.get('error', 'Unknown error'))}\n"
        )

    # Demonstrate changing system context
    completion_component.set_system_context(
        "You are now an assistant specialized in data science with Python."
    )
    result = await process_input(
        pipeline, "What are some popular Python libraries for data analysis?"
    )
    print(
        f"After context change - Output: {result.get('ai_response', 'Error: ' + result.get('error', 'Unknown error'))}\n"
    )

    # Get conversation history
    history = completion_component.get_conversation_history()
    print("Conversation History:")
    for entry in history:
        print(
            f"{entry['role']}: {entry['content'][:50]}..."
        )  # Print first 50 characters of each message

    # Clear conversation history
    completion_component.clear_conversation_history()
    print("\nConversation history cleared.")

    # Get conversation history
    history = completion_component.get_conversation_history()
    print("Conversation History:")
    for entry in history:
        print(
            f"{entry['role']}: {entry['content'][:50]}..."
        )  # Print first 50 characters of each message

    # Demonstrate processing after clearing history
    result = await process_input(pipeline, "Summarize what we've discussed about Python.")
    print(
        f"After clearing history - Output: {result.get('ai_response', 'Error: ' + result.get('error', 'Unknown error'))}"
    )


if __name__ == "__main__":
    asyncio.run(run_example())
