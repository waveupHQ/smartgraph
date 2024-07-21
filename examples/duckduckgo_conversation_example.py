# examples/duckduckgo_conversation_example.py

import asyncio
import os

from dotenv import load_dotenv

from smartgraph import ReactiveAssistantConversation
from smartgraph.logging import SmartGraphLogger
from smartgraph.tools.duckduckgo_toolkit import DuckDuckGoToolkit

# Load environment variables
load_dotenv()

# Set up logging
logger = SmartGraphLogger.get_logger()
logger.set_level("DEBUG")  # Set to "DEBUG" for more detailed logging

# Set this to True to enable debug mode
DEBUG_MODE = True

async def main():
    try:
        # Check for API key
        if not os.getenv("OPENAI_API_KEY"):
            logger.error("Missing API key. Please set OPENAI_API_KEY in your environment.")
            return

        # Initialize DuckDuckGoToolkit
        duckduckgo_toolkit = DuckDuckGoToolkit(max_results=3)
        logger.info("DuckDuckGoToolkit initialized successfully")

        # Initialize ReactiveAssistantConversation with DuckDuckGo toolkit
        assistant = ReactiveAssistantConversation(
            name="Search and News Assistant",
            toolkits=[duckduckgo_toolkit],
            model="gpt-4o-mini",
            api_key=os.getenv("OPENAI_API_KEY"),
            debug_mode=DEBUG_MODE
        )
        logger.info("ReactiveAssistantConversation initialized successfully")

        # Example conversation flow
        conversation = [
            "Can you find any recent news about electric vehicles?",
            "What's the current situation of the COVID-19 pandemic globally?",
            "Tell me a fun fact about Deadpool & Wolverine movie 2024."
        ]

        for user_input in conversation:
            print(f"\nUser: {user_input}")
            logger.info(f"Processing user input: {user_input}")
            try:
                response = await assistant.process(user_input)
                print(f"Assistant: {response}")
            except Exception as e:
                logger.error(f"Error processing input: {str(e)}", exc_info=True)
                print(f"Assistant: I'm sorry, but I encountered an error while processing your input. Please try again later.")

    except Exception as e:
        logger.error(f"An unexpected error occurred: {str(e)}", exc_info=True)
        print("An unexpected error occurred. Please check the logs for more information.")

if __name__ == "__main__":
    asyncio.run(main())