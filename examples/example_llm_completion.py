# /examples/example_llm_completion.py
import asyncio
import os
from typing import AsyncGenerator, Dict

from dotenv import load_dotenv

from smartgraph.components import CompletionComponent
from smartgraph.logging import SmartGraphLogger

# Load environment variables
load_dotenv()

# Set up logging
logger = SmartGraphLogger.get_logger()
logger.set_level("INFO")


async def main():
    # Create a CompletionComponent
    completion = CompletionComponent(
        "AI_Completion",
        model="claude-3-haiku-20240307",
        temperature=0.7,
        # stream=True,  # Set to False for non-streaming mode
        api_key=os.getenv("ANTHROPIC_API_KEY"),
    )

    user_input = "Explain reactive programming"
    logger.info(f"Processing input: {user_input}")

    try:
        result = await completion.process({"message": user_input})

        if isinstance(result, dict):
            # Non-streaming response
            if "error" in result:
                logger.error(f"Error during processing: {result['error']}")
                print(f"\nAn error occurred: {result['error']}\n")
            else:
                logger.info(f"Received: {result}")
                print(f"\nAI Response: {result.get('ai_response', 'No response')}\n")
        else:
            # Streaming response
            logger.info("Receiving streaming response")
            full_response = ""
            async for chunk in result:
                if (
                    chunk.get("choices")
                    and chunk["choices"][0].get("delta")
                    and chunk["choices"][0]["delta"].get("content")
                ):
                    content = chunk["choices"][0]["delta"]["content"]
                    print(content, end="", flush=True)
                    full_response += content
            print()  # New line after full response
            logger.info(f"Full response received: {full_response}")

    except Exception as e:
        logger.error(f"Unexpected error during processing: {str(e)}", exc_info=True)
        print(f"\nAn unexpected error occurred: {str(e)}\n")


if __name__ == "__main__":
    asyncio.run(main())
