import asyncio
import json
import os

from dotenv import load_dotenv

from smartgraph import AIActor, Edge, HumanActor, MemoryManager, Node, SmartGraph, Task
from smartgraph.assistant_conversation import AssistantConversation
from smartgraph.logging import SmartGraphLogger

try:
    from duckduckgo_search import DDGS
except ImportError:
    raise ImportError(  # noqa: B904
        "`duckduckgo-search` not installed. Please install using `pip install duckduckgo-search`"
    )

# Set up logging
logger = SmartGraphLogger.get_logger()
logger.set_level("INFO")

# Load environment variables
load_dotenv()

# Get API key and model from environment variables
api_key = os.getenv("OPENAI_API_KEY")
model = os.getenv("LLM_MODEL", "gpt-3.5-turbo-1106")


class DuckDuckGoSearch:
    def __init__(self, max_results: int = 5):
        self.max_results = max_results
        self.ddgs = DDGS()

    def search(self, query: str) -> str:
        logger.debug(f"Searching DDG for: {query}")
        results = list(self.ddgs.text(keywords=query, max_results=self.max_results))
        return json.dumps(results, indent=2)

    def news(self, query: str) -> str:
        logger.debug(f"Searching DDG news for: {query}")
        results = list(self.ddgs.news(keywords=query, max_results=self.max_results))
        return json.dumps(results, indent=2)


# Initialize DuckDuckGoSearch
ddg_search = DuckDuckGoSearch()

# Define DuckDuckGo search tools
duckduckgo_search_tool = {
    "type": "function",
    "function": {
        "name": "duckduckgo_search",
        "description": "Search the web using DuckDuckGo",
        "parameters": {
            "type": "object",
            "properties": {"query": {"type": "string", "description": "The search query"}},
            "required": ["query"],
        },
    },
}

duckduckgo_news_tool = {
    "type": "function",
    "function": {
        "name": "duckduckgo_news",
        "description": "Get the latest news from DuckDuckGo",
        "parameters": {
            "type": "object",
            "properties": {"query": {"type": "string", "description": "The news query"}},
            "required": ["query"],
        },
    },
}

# Initialize assistant with DuckDuckGo search tools
assistant = AssistantConversation(
    name="Search Assistant",
    tools=[duckduckgo_search_tool, duckduckgo_news_tool],
    model=model,
    api_key=api_key,
)

# Add the search functions to the assistant
assistant.add_function("duckduckgo_search", ddg_search.search)
assistant.add_function("duckduckgo_news", ddg_search.news)

# Create a simple graph
memory_manager = MemoryManager()

# Create actors
human = HumanActor("User", memory_manager=memory_manager)
ai = AIActor("AI", assistant=assistant, memory_manager=memory_manager)

# Define tasks
get_query_task = Task(description="Get search query from user")
perform_search_task = Task(
    description="Perform web search, get latest news, and summarize results",
    prompt="Search the web and get the latest news for: {input}. Then, provide a concise summary of the most relevant information.",
)
present_results_task = Task(description="Present search results")

# Create nodes
get_query_node = Node(id="get_query", actor=human, task=get_query_task)
search_node = Node(id="search", actor=ai, task=perform_search_task)
present_results_node = Node(id="present_results", actor=ai, task=present_results_task)

# Create graph
graph = SmartGraph()

# Add nodes to the graph
graph.add_node(get_query_node)
graph.add_node(search_node)
graph.add_node(present_results_node)

# Add edges to define the flow
graph.add_edge(Edge(source_id="get_query", target_id="search"))
graph.add_edge(Edge(source_id="search", target_id="present_results"))
graph.add_edge(Edge(source_id="present_results", target_id="get_query"))


# Execute the graph
async def run_search_assistant():
    while True:
        try:
            result, should_exit = await graph.execute("get_query", {}, "search_session")
            if should_exit:
                break
            logger.info("\nSearch Results:")
            logger.info(result["short_term"].get("response", "No results found."))
            logger.info("\n---")
        except Exception as e:
            logger.error(f"Error during search assistant execution: {str(e)}")
            print("An error occurred. Please try again.")
        finally:
            assistant.reset_conversation()  # Reset conversation after each interaction


# Run the search assistant
if __name__ == "__main__":
    asyncio.run(run_search_assistant())
