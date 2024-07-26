# examples/example_llm_completion_with_tool.py

import asyncio
import os

from dotenv import load_dotenv

from smartgraph.components import CompletionComponent
from smartgraph.logging import SmartGraphLogger
from smartgraph.tools.weather_toolkit import WeatherToolkit

# Load environment variables
load_dotenv()

# Set up logging
logger = SmartGraphLogger.get_logger()
logger.set_level("INFO")


async def process_with_llm(input_message: str) -> dict:
    # Create a WeatherToolkit
    weather_toolkit = WeatherToolkit(api_key=os.getenv("OPENWEATHER_API_KEY"))

    # Create a CompletionComponent with the WeatherToolkit
    completion = CompletionComponent(
        "AI_Completion",
        model="gpt-3.5-turbo",
        temperature=0.7,
        api_key=os.getenv("OPENAI_API_KEY"),
        toolkits=[weather_toolkit],
    )

    input_data = {"message": input_message}
    logger.info(f"Processing input: {input_message}")

    try:
        result = await completion.process(input_data)
        if "error" in result:
            logger.error(f"Error during processing: {result['error']}")
            return {"error": result["error"]}
        else:
            logger.info(f"Received: {result}")
            return {"response": result.get("ai_response", "No response")}
    except Exception as e:
        logger.error(f"Unexpected error during processing: {str(e)}", exc_info=True)
        return {"error": str(e)}


async def main():
    # Simulate an API call with a weather-related question
    input_message = "What's the current temperature in London?"
    result = await process_with_llm(input_message)

    if "error" in result:
        print(f"Error: {result['error']}")
    else:
        print(f"AI Response: {result['response']}")


if __name__ == "__main__":
    asyncio.run(main())
