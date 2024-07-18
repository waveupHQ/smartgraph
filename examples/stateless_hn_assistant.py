import asyncio
import json
import os
import httpx
from dotenv import load_dotenv

from smartgraph import AIActor, Edge, HumanActor, Node, SmartGraph, Task
from smartgraph.assistant_conversation import AssistantConversation

def get_top_hackernews_stories(num_stories: int = 10) -> str:
    """Get top stories from Hacker News."""
    response = httpx.get("https://hacker-news.firebaseio.com/v0/topstories.json")
    story_ids = response.json()

    stories = []
    for story_id in story_ids[:num_stories]:
        story_response = httpx.get(f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json")
        story = story_response.json()
        if "text" in story:
            story.pop("text", None)
        stories.append(story)
    return json.dumps(stories)

# Load environment variables
load_dotenv()

# Get API key and model from environment variables
api_key = os.getenv("OPENAI_API_KEY")
model = os.getenv("LLM_MODEL", "gpt-3.5-turbo")

# Initialize AssistantConversation
assistant = AssistantConversation(
    name="HN Assistant",
    tools=[{
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
    }],
    model=model,
    api_key=api_key,
)
assistant.add_function("get_top_hackernews_stories", get_top_hackernews_stories)

# Create actors without memory management
human_actor = HumanActor("User")
ai_actor = AIActor("AI", assistant=assistant)

# Create nodes
get_query_node = Node(id="get_query", actor=human_actor, task=Task(description="Get search query from user"))
search_node = Node(id="search", actor=ai_actor, task=Task(
    description="Summarize the top stories on Hacker News",
    prompt="Search Hacker News for: {input}. Then, provide a concise summary of the top stories."
))

# Create graph and add nodes and edges
graph = SmartGraph()
graph.add_node(get_query_node)
graph.add_node(search_node)
graph.add_edge(Edge(source_id="get_query", target_id="search"))
graph.add_edge(Edge(source_id="search", target_id="get_query"))

async def run_hn_assistant():
    print("Welcome to the Hacker News Assistant!")
    print("Ask about top stories or type 'exit' to end the conversation.")

    while True:
        try:
            user_input = input("You: ")
            if user_input.lower() == 'exit':
                print("Conversation ended.")
                break

            result = await graph.execute("get_query", {"response": user_input}, "hn_session")
            ai_response = result[0]['short_term'].get("response", "No results found.")
            print(f"\nHN Assistant: {ai_response}\n")

        except Exception as e:
            print(f"An error occurred: {str(e)}")
            print("Would you like to continue? (yes/no)")
            if input().lower() != 'yes':
                break

        assistant.reset_conversation()

if __name__ == "__main__":
    asyncio.run(run_hn_assistant())