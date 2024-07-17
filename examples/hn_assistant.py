# /examples/hn_assistant.py
import asyncio
import json
import os

import httpx
from dotenv import load_dotenv

from smartgraph import AIActor, Edge, HumanActor, MemoryManager, Node, SmartGraph, Task
from smartgraph.assistant_conversation import AssistantConversation
from smartgraph.logging import SmartGraphLogger


def get_top_hackernews_stories(num_stories: int = 10) -> str:
    """Use this function to get top stories from Hacker News.

    Args:
        num_stories (int): Number of stories to return. Defaults to 10.

    Returns:
        str: JSON string of top stories.
    """
    # Fetch top story IDs
    response = httpx.get("https://hacker-news.firebaseio.com/v0/topstories.json")
    story_ids = response.json()

    # Fetch story details
    stories = []
    for story_id in story_ids[:num_stories]:
        story_response = httpx.get(f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json")
        story = story_response.json()
        if "text" in story:
            story.pop("text", None)
        stories.append(story)
    return json.dumps(stories)

# Set up logging
logger = SmartGraphLogger.get_logger()
logger.set_level("INFO")

# Load environment variables
load_dotenv()

# Get API key and model from environment variables
api_key = os.getenv("OPENAI_API_KEY")
model = os.getenv("LLM_MODEL", "gpt-3.5-turbo-1106")

# Manually define the function schema
get_top_stories_schema = {
    "type": "function",
    "function": {
        "name": "get_top_hackernews_stories",
        "description": "Get the top stories from Hacker News",
        "parameters": {
            "type": "object",
            "properties": {
                "num_stories": {
                    "type": "integer",
                    "description": "Number of stories to return",
                    "default": 10,
                }
            },
            "required": [],
        },
    },
}

# Initialize assistant
assistant = AssistantConversation(
    name="HN Assistant",
    tools=[get_top_stories_schema],
    tool_choice="auto",
    model=model,
    api_key=api_key,
)

# Add the search function to the assistant
assistant.add_function("get_top_hackernews_stories", get_top_hackernews_stories)


# Create a simple graph
memory_manager = MemoryManager()

# Create actors
human = HumanActor("User", memory_manager=memory_manager)
ai = AIActor("AI", assistant=assistant, memory_manager=memory_manager)

# Define tasks
get_query_task = Task(description="Get search query from user")
perform_search_task = Task(
    description="Summarize the top stories on hackernews?",
    prompt="Search on hackernews for: {input}. Then, provide a concise summary of the top stories.",
)
present_results_task = Task(description="Present top stories")

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
