# examples/reactive_conversation_with_tool.py

import asyncio
import os
from dotenv import load_dotenv
from smartgraph import ReactiveAssistantConversation
from smartgraph.tools import TavilyTools
from smartgraph.logging import SmartGraphLogger

# Load environment variables
load_dotenv()

# Set up logging
logger = SmartGraphLogger.get_logger()
logger.set_level("INFO")  # Set to "DEBUG" for more detailed logging

# Set this to True to enable debug mode
DEBUG_MODE = False

async def main():
    try:
        # Check for API keys
        if not os.getenv("OPENAI_API_KEY") or not os.getenv("TAVILY_API_KEY"):
            logger.error("Missing API keys. Please set OPENAI_API_KEY and TAVILY_API_KEY in your environment.")
            return

        # Initialize TavilyTools
        tavily_tools = TavilyTools()
        logger.info("TavilyTools initialized successfully")

        # Initialize ReactiveAssistantConversation with Tavily search tools
        assistant = ReactiveAssistantConversation(
            name="Search Assistant",
            tools=[tavily_tools.search_schema, tavily_tools.search_with_context_schema],
            model="gpt-4-0613",
            api_key=os.getenv("OPENAI_API_KEY"),
            debug_mode=DEBUG_MODE
        )
        logger.info("ReactiveAssistantConversation initialized successfully")

        # Add the search functions to the assistant
        assistant.add_function("tavily_search", tavily_tools.search)
        assistant.add_function("tavily_search_with_context", tavily_tools.search_with_context)
        logger.info("Search functions added to the assistant")

        # Example usage
        user_input = "What are the latest developments in quantum computing?"
        print(f"User: {user_input}")

        logger.info(f"Processing user input: {user_input}")
        response = await assistant.process(user_input)
        # logger.info(f"Received response: {response}")

        print(f"Assistant: {response}")

    except Exception as e:
        logger.error(f"An error occurred: {str(e)}", exc_info=True)
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())

