# examples/example_llm_completion_api.py

import asyncio
import os
import time
from typing import List, Dict, Any

from dotenv import load_dotenv

from smartgraph.components import CompletionComponent
from smartgraph.logging import SmartGraphLogger

# Load environment variables
load_dotenv()

# Set up logging
logger = SmartGraphLogger.get_logger()
logger.set_level("DEBUG")

async def simulate_api_call(completion_component: CompletionComponent, input_text: str) -> Dict[str, Any]:
    logger.info(f"Processing input: {input_text}")
    start_time = time.time()
    result = await completion_component.process({"message": input_text})
    end_time = time.time()
    result['processing_time'] = end_time - start_time
    return result

async def process_inputs_sequentially(completion_component: CompletionComponent, inputs: List[str]):
    for input_text in inputs:
        result = await simulate_api_call(completion_component, input_text)
        print(f"Input: {input_text}")
        print(f"Output: {result.get('ai_response', 'Error: ' + result.get('error', 'Unknown error'))}")
        print(f"Processing time: {result['processing_time']:.2f} seconds\n")

async def process_inputs_concurrently(completion_component: CompletionComponent, inputs: List[str]):
    tasks = [simulate_api_call(completion_component, input_text) for input_text in inputs]
    results = await asyncio.gather(*tasks)
    for input_text, result in zip(inputs, results):
        print(f"Input: {input_text}")
        print(f"Output: {result.get('ai_response', 'Error: ' + result.get('error', 'Unknown error'))}")
        print(f"Processing time: {result['processing_time']:.2f} seconds\n")

async def run_example():
    # Initialize CompletionComponent
    completion_component = CompletionComponent(
        name="GPT_Completion",
        model="gpt-4o-mini",
        temperature=0.7,
        api_key=os.getenv("OPENAI_API_KEY"),
        system_context="You are a helpful assistant specialized in Python programming.",
        max_tokens=4000,
    )

    # Inputs to process
    inputs = [
        "What are the key features of Python?",
        "Explain the concept of reactive programming in Python.",
        "What are some popular Python libraries for data analysis?",
    ]

    print("Processing inputs sequentially:")
    await process_inputs_sequentially(completion_component, inputs)

    print("\nProcessing inputs concurrently:")
    await process_inputs_concurrently(completion_component, inputs)

    # Demonstrate changing system context
    completion_component.set_system_context(
        "You are now an assistant specialized in data science with Python."
    )
    result = await simulate_api_call(
        completion_component, "Summarize the advantages of using Python for data science."
    )
    print("After context change:")
    print(f"Output: {result.get('ai_response', 'Error: ' + result.get('error', 'Unknown error'))}")
    print(f"Processing time: {result['processing_time']:.2f} seconds\n")

    # Get conversation history
    history = completion_component.get_conversation_history()
    print("Conversation History:")
    for entry in history:
        print(f"{entry['role']}: {entry['content'][:50]}...")  # Print first 50 characters of each message

    # Clear conversation history
    completion_component.clear_conversation_history()
    print("\nConversation history cleared.")

    # Demonstrate processing after clearing history
    result = await simulate_api_call(completion_component, "Summarize what we've discussed about Python.")
    print("After clearing history:")
    print(f"Output: {result.get('ai_response', 'Error: ' + result.get('error', 'Unknown error'))}")
    print(f"Processing time: {result['processing_time']:.2f} seconds")

async def main():
    try:
        await run_example()
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(main())
