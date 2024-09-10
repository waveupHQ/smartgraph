import asyncio
import os

from dotenv import load_dotenv

from smartgraph import ReactiveSmartGraph
from smartgraph.components import CompletionComponent, TextInputHandler
from smartgraph.tools.duckduckgo_toolkit import DuckDuckGoToolkit

# Load environment variables
load_dotenv()


class SmartAssistant(ReactiveSmartGraph):
    def __init__(self):
        super().__init__()
        pipeline = self.create_pipeline("Assistant")

        pipeline.add_component(TextInputHandler("Input"))
        pipeline.add_component(
            CompletionComponent(
                "AIAssistant",
                model="gpt-4o-mini",
                api_key=os.getenv("OPENAI_API_KEY"),
                system_context="You are a helpful assistant that can answer questions and perform web searches when needed.",
                toolkits=[DuckDuckGoToolkit()],
            )
        )

        self.compile()

    async def ask(self, question: str):
        return await self.execute_and_await("Assistant", question)


async def main():
    assistant = SmartAssistant()

    while True:
        user_input = input("Ask me anything (or type 'exit' to quit): ")
        if user_input.lower() == "exit":
            break

        response = await assistant.ask(user_input)
        print(
            f"Assistant: {response.get('ai_response', 'Sorry, I could not generate a response.')}"
        )


if __name__ == "__main__":
    asyncio.run(main())
