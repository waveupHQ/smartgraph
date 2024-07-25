import asyncio
import os

from dotenv import load_dotenv

from smartgraph.components import CompletionComponent
from smartgraph.logging import SmartGraphLogger

# Load environment variables
load_dotenv()

# Set up logging
logger = SmartGraphLogger.get_logger()
logger.set_level("INFO")


async def process_input(completion: CompletionComponent, input_text: str) -> None:
    input_data = {"message": input_text}

    try:
        result = await completion.process(input_data)
        if "error" in result:
            logger.error(f"Error during processing: {result['error']}")
            print(f"\nAn error occurred: {result['error']}\n")
        else:
            logger.info(f"Received: {result}")
            print(f"\nAI Response: {result.get('ai_response', 'No response')}\n")
    except Exception as e:
        logger.error(f"Unexpected error during processing: {str(e)}", exc_info=True)
        print(f"\nAn unexpected error occurred: {str(e)}\n")


async def main():
    # Create a CompletionComponent
    completion = CompletionComponent(
        "AI_Completion", model="gpt-4o-mini", temperature=0.7, api_key=os.getenv("OPENAI_API_KEY")
    )

    while True:
        user_input = input("Enter your question (or 'quit' to exit): ")
        if user_input.lower() == "quit":
            break

        logger.info(f"Processing input: {user_input}")
        await process_input(completion, user_input)


if __name__ == "__main__":
    asyncio.run(main())
