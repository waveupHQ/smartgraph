import asyncio
import os

from dotenv import load_dotenv

from smartgraph import AIActor, Edge, HumanActor, Node, SmartGraph, Task
from smartgraph.assistant_conversation import AssistantConversation
from smartgraph.logging import SmartGraphLogger
from smartgraph.memory import MemoryManager
from smartgraph.tools import DuckDuckGoSearch

# Load environment variables
load_dotenv()

# Set up logging
logger = SmartGraphLogger.get_logger()
logger.set_level("INFO")

# Get API key and model from environment variables
api_key = os.getenv("OPENAI_API_KEY")
model = os.getenv("LLM_MODEL", "gpt-3.5-turbo")


async def main():
    # Initialize MemoryManager
    memory_manager = MemoryManager()

    # Initialize DuckDuckGoSearch
    ddg_search = DuckDuckGoSearch()

    # Initialize AssistantConversation with search tools
    assistant = AssistantConversation(
        name="Search Assistant",
        tools=[ddg_search.search_schema, ddg_search.news_schema],
        model=model,
        api_key=api_key,
    )

    # Add the search functions to the assistant
    assistant.add_function("duckduckgo_search", ddg_search.search)
    assistant.add_function("duckduckgo_news", ddg_search.news)

    # Create actors
    human_actor = HumanActor("User", memory_manager=memory_manager)
    ai_actor = AIActor("AI", assistant=assistant, memory_manager=memory_manager)

    # Create nodes
    user_input_node = Node(
        id="user_input", actor=human_actor, task=Task(description="Get search query from user")
    )
    search_node = Node(
        id="search",
        actor=ai_actor,
        task=Task(
            description="Perform web search and summarize results",
            prompt="Search the web for: {input}. Then, provide a concise summary of the most relevant information.",
        ),
    )
    present_results_node = Node(
        id="present_results", actor=ai_actor, task=Task(description="Present search results")
    )

    # Create edges
    edge1 = Edge(source_id="user_input", target_id="search")
    edge2 = Edge(source_id="search", target_id="present_results")
    edge3 = Edge(source_id="present_results", target_id="user_input")

    # Create SmartGraph
    graph = SmartGraph(memory_manager=memory_manager)

    # Add nodes and edges
    for node in [user_input_node, search_node, present_results_node]:
        graph.add_node(node)
    for edge in [edge1, edge2, edge3]:
        graph.add_edge(edge)

    # Run the search assistant
    print("Welcome to the Search Assistant!")
    print("Enter your search query or type 'exit' to end the conversation.")

    while True:
        try:
            result, should_exit = await graph.execute("user_input", {}, "search_session")

            if should_exit:
                print("Search session ended.")
                break

            # Display the search results
            search_results = result["short_term"].get("response", "")
            print("\nSearch Results:")
            print(search_results)
            print("\n---")

        except Exception as e:
            logger.error(f"An error occurred: {str(e)}")
            print("An error occurred. Would you like to continue? (yes/no)")
            response = input().lower()
            if response != "yes":
                break

    # After the search session, display the final memory state
    facts = await memory_manager.get_long_term("facts")
    preferences = await memory_manager.get_long_term("user_preferences")

    print("\nFinal Memory State:")
    print("Facts learned:")
    for fact in facts:
        print(f"- {fact}")
    print("\nUser Preferences:")
    for key, value in preferences.items():
        print(f"- {key}: {value}")


if __name__ == "__main__":
    asyncio.run(main())
