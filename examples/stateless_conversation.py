import asyncio
import os

from dotenv import load_dotenv

from smartgraph import AIActor, Edge, HumanActor, Node, SmartGraph, Task
from smartgraph.assistant_conversation import AssistantConversation
from smartgraph.logging import SmartGraphLogger

# Load environment variables
load_dotenv()

# Set up logging
logger = SmartGraphLogger.get_logger()
logger.set_level("INFO")

# Get API key and model from environment variables
api_key = os.getenv("OPENAI_API_KEY")
model = os.getenv("LLM_MODEL", "gpt-3.5-turbo")

# System message for the AI assistant
SYSTEM_MESSAGE = """
You are a helpful AI assistant. Your responses should be informative, polite, and concise.
If you're unsure about something, it's okay to say you don't know.
"""

async def main():
    # Initialize AssistantConversation
    assistant = AssistantConversation(
        name="Stateless AI Assistant",
        model=model,
        api_key=api_key,
    )

    # Create actors
    human_actor = HumanActor(name="User", memory_manager=None)
    ai_actor = AIActor(name="AI", assistant=assistant, memory_manager=None)

    # Create nodes
    user_input_node = Node(
        id="user_input",
        actor=human_actor,
        task=Task(description="Get user input")
    )
    ai_response_node = Node(
        id="ai_response",
        actor=ai_actor,
        task=Task(
            description="AI response",
            prompt=f"{SYSTEM_MESSAGE}\nUser: {{input}}\nAI:"
        )
    )

    # Create edges
    edge1 = Edge(source_id="user_input", target_id="ai_response")
    edge2 = Edge(source_id="ai_response", target_id="user_input")

    # Create SmartGraph
    graph = SmartGraph()

    # Add nodes and edges
    for node in [user_input_node, ai_response_node]:
        graph.add_node(node)
    for edge in [edge1, edge2]:
        graph.add_edge(edge)

    print("Welcome to the Stateless Conversation System!")
    print("Type 'exit' to end the conversation.")

    while True:
        try:
            result, should_exit = await graph.execute("user_input", {}, "stateless_conversation")
            
            if should_exit:
                print("Conversation ended.")
                break

            # Display the AI's response
            ai_response = result['short_term'].get('response', 'No response')
            print(f"\nAI: {ai_response}\n")

            # Reset the assistant's conversation after each interaction
            assistant.reset_conversation()

        except Exception as e:
            logger.error(f"An error occurred: {str(e)}")
            print("An error occurred. Would you like to continue? (yes/no)")
            response = input().lower()
            if response != 'yes':
                break

if __name__ == "__main__":
    asyncio.run(main())