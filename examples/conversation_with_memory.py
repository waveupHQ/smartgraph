import asyncio
import os
from dotenv import load_dotenv

from smartgraph import AIActor, Edge, HumanActor, Node, SmartGraph, Task
from smartgraph.assistant_conversation import AssistantConversation
from smartgraph.memory import MemoryManager
from smartgraph.logging import SmartGraphLogger

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

    # Initialize AssistantConversation
    assistant = AssistantConversation(
        name="Memory-Aware Assistant",
        model=model,
        api_key=api_key,
    )

    # Create actors
    human_actor = HumanActor("User", memory_manager=memory_manager)
    ai_actor = AIActor("AI", assistant=assistant, memory_manager=memory_manager)

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
            description="Provide a response based on user input and memory",
            prompt="Respond to the following input, using relevant facts and user preferences from memory if applicable: {input}"
        )
    )
    memory_summary_node = Node(
        id="memory_summary",
        actor=ai_actor,
        task=Task(
            description="Summarize current memory state",
            prompt="Provide a brief summary of the current memory state, including key facts and user preferences."
        )
    )

    # Create edges
    edge1 = Edge(source_id="user_input", target_id="ai_response")
    edge2 = Edge(source_id="ai_response", target_id="memory_summary")
    edge3 = Edge(source_id="memory_summary", target_id="user_input")

    # Create SmartGraph
    graph = SmartGraph(memory_manager=memory_manager)

    # Add nodes and edges
    for node in [user_input_node, ai_response_node, memory_summary_node]:
        graph.add_node(node)
    for edge in [edge1, edge2, edge3]:
        graph.add_edge(edge)

    # Run the conversation
    print("Welcome to the Memory-Aware Conversation System!")
    print("You can set preferences by typing 'set preference:key:value'")
    print("For example: set preference:mode:dark")
    print("Type 'exit' to end the conversation.")

    while True:
        try:
            result, should_exit = await graph.execute("user_input", {}, "memory_conversation")
            
            if should_exit:
                print("Conversation ended.")
                break

            # Display the memory summary
            memory_summary = result['short_term'].get('response', '')
            print("\nMemory Summary:")
            print(memory_summary)
            print("\n---")
        except Exception as e:
            logger.error(f"An error occurred: {str(e)}")
            print("An error occurred. Would you like to continue? (yes/no)")
            response = input().lower()
            if response != 'yes':
                break

    # After the conversation, display the final memory state
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