import asyncio
import os

from dotenv import load_dotenv

from smartgraph.components import CompletionComponent
from smartgraph.logging import SmartGraphLogger

# Load environment variables
load_dotenv()


async def main():
    # Create a CompletionComponent
    completion = CompletionComponent(
        "AI_Completion", model="gpt-4o-mini", temperature=0.7, api_key=os.getenv("OPENAI_API_KEY")
    )

    # Set up logging
    logger = SmartGraphLogger.get_logger()
    logger.set_level("INFO")

    def on_next(value):
        logger.info(f"Received: {value}")

    def on_error(error):
        logger.error(f"Error: {error}")

    def on_completed():
        logger.info("Completed")

    # Process a message
    input_data = {"message": "What is the capital of France?"}

    # Create and subscribe to the Observable
    observable = completion.process(input_data)
    disposable = observable.subscribe(on_next, on_error, on_completed)

    # Wait for the completion
    await asyncio.sleep(10)  # Adjust this value based on expected response time

    # Clean up
    disposable.dispose()


if __name__ == "__main__":
    asyncio.run(main())
