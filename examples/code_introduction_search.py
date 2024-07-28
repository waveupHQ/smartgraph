import asyncio
import os

from dotenv import load_dotenv

from smartgraph import ReactiveSmartGraph
from smartgraph.components import CompletionComponent, TextInputHandler
from smartgraph.tools.duckduckgo_toolkit import DuckDuckGoToolkit

# Load environment variables
load_dotenv()


class SearchAssistant(ReactiveSmartGraph):
    def __init__(self):
        super().__init__()
        pipeline = self.create_pipeline("SearchAssistant")

        pipeline.add_component(TextInputHandler("TextInput"))
        pipeline.add_component(
            CompletionComponent(
                "GPT_Completion",
                model="gpt-4o-mini",
                api_key=os.getenv("OPENAI_API_KEY"),
                toolkits=[DuckDuckGoToolkit()],
            )
        )

        # Compile the graph
        self.compile()

    async def search(self, query):
        return await self.execute("SearchAssistant", query)


async def main():
    assistant = SearchAssistant()
    result = await assistant.search("Who win the first medal in Paris's JO 2024?")
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
