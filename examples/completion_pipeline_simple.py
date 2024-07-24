import asyncio
import os

from dotenv import load_dotenv

from smartgraph import Pipeline, ReactiveComponent
from smartgraph.components import CompletionComponent, TextInputHandler
from smartgraph.logging import SmartGraphLogger

# Load environment variables
load_dotenv()

# Set up logging
logger = SmartGraphLogger.get_logger()
logger.set_level("INFO")

class OutputComponent(ReactiveComponent):
    async def process(self, input_data: dict) -> str:
        logger.info(f"OutputComponent received: {input_data}")
        if "error" in input_data:
            output = f"Error: {input_data['error']}"
        else:
            output = f"Final output: {input_data.get('ai_response', 'No response')}"
        logger.info(f"OutputComponent processing: {output}")
        return output

def create_pipeline():
    pipeline = Pipeline("LLM Pipeline")
    
    input_handler = TextInputHandler("TextInput")
    completion_component = CompletionComponent(
        "GPT_Completion",
        model="gpt-4o-mini",
        temperature=0.7, 
        api_key=os.getenv("OPENAI_API_KEY")
    )
    output_component = OutputComponent("Output")
    
    pipeline.add_component(input_handler)
    pipeline.add_component(completion_component)
    pipeline.add_component(output_component)
    
    pipeline.connect_components("TextInput", "GPT_Completion")
    pipeline.connect_components("GPT_Completion", "Output")
    
    return pipeline

async def main():
    pipeline = create_pipeline()
    
    while True:
        user_input = input("Enter your prompt (or 'quit' to exit): ")
        if user_input.lower() == 'quit':
            break
        
        logger.info("Starting pipeline execution...")
        result = await pipeline.execute(user_input)
        print(f"\n{result}\n")

if __name__ == "__main__":
    asyncio.run(main())
