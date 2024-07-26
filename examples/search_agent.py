# examples/search_agent.py

import asyncio
import os

from dotenv import load_dotenv

from smartgraph.components import CompletionComponent
from smartgraph.logging import SmartGraphLogger
from smartgraph.tools.tavily_toolkit import TavilyToolkit

# Load environment variables
load_dotenv()

# Set up logging
logger = SmartGraphLogger.get_logger()
logger.set_level("INFO")  # Set to "DEBUG" for more detailed logging

# Set this to True to enable debug mode
DEBUG_MODE = False


async def process_question(assistant: CompletionComponent, question: str) -> str:
    try:
        logger.info(f"Processing user input: {question}")
        result = await assistant.process({"message": question})
        if "error" in result:
            logger.error(f"Error during processing: {result['error']}")
            return "I'm sorry, but I encountered an error while processing your question. Please try again later."
        else:
            return result.get("ai_response", "No response generated.")
    except Exception as e:
        logger.error(f"Error processing question: {str(e)}", exc_info=True)
        return "I'm sorry, but I encountered an error while processing your question. Please try again later."


async def main():
    try:
        # Check for API keys
        if not os.getenv("OPENAI_API_KEY") or not os.getenv("TAVILY_API_KEY"):
            logger.error(
                "Missing API keys. Please set OPENAI_API_KEY and TAVILY_API_KEY in your environment."
            )
            return

        # Initialize TavilyToolkit
        tavily_toolkit = TavilyToolkit(api_key=os.getenv("TAVILY_API_KEY"))
        logger.info("TavilyToolkit initialized successfully")

        # Initialize CompletionComponent with Tavily toolkit
        assistant = CompletionComponent(
            name="Search Assistant",
            model="gpt-4o-mini",
            api_key=os.getenv("OPENAI_API_KEY"),
            toolkits=[tavily_toolkit],
            system_context="You are a helpful assistant that can search the internet for information.",
            temperature=0.7,
            max_tokens=150,  # Adjust as needed
        )
        logger.info("CompletionComponent initialized successfully")

        # Example usage
        questions = [
            "What are the latest developments in quantum computing?",
            "How does the weather in New York compare to London today?",
            "Can you summarize the plot of the latest blockbuster movie?",
        ]

        for question in questions:
            print(f"\nUser: {question}")
            response = await process_question(assistant, question)
            print(f"Assistant: {response}")

    except Exception as e:
        logger.error(f"An unexpected error occurred: {str(e)}", exc_info=True)
        print("An unexpected error occurred. Please check the logs for more information.")


if __name__ == "__main__":
    asyncio.run(main())
