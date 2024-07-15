# examples/persistent_conversation.py

import os

from dotenv import load_dotenv
from phi.assistant import Assistant
from phi.llm.anthropic import Claude

from smartgraph import AIActor, Edge, HumanActor, Node, SmartGraph, Task
from smartgraph.checkpointer import Checkpointer
from smartgraph.memory import MemoryManager

load_dotenv()


def main():
    claude_model = os.getenv("CLAUDE_MODEL")
    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")

    if not claude_model or not anthropic_api_key:
        raise ValueError("CLAUDE_MODEL and ANTHROPIC_API_KEY must be set in .env file")

    memory_manager = MemoryManager()
    checkpointer = Checkpointer()

    assistant = Assistant(
        name="AI Assistant", llm=Claude(model=claude_model, api_key=anthropic_api_key)
    )

    human_actor = HumanActor(name="User", memory_manager=memory_manager)
    ai_actor = AIActor(name="AI", assistant=assistant, memory_manager=memory_manager)

    start_node = Node(actor=human_actor, task=Task(description="Start the conversation"))
    ai_response_node = Node(
        actor=ai_actor, task=Task(description="AI response", prompt="Respond to: {input[response]}")
    )
    human_feedback_node = Node(
        actor=human_actor, task=Task(description="Provide feedback on AI's response")
    )

    edge1 = Edge(source_id=start_node.id, target_id=ai_response_node.id)
    edge2 = Edge(source_id=ai_response_node.id, target_id=human_feedback_node.id)
    edge3 = Edge(
        source_id=human_feedback_node.id,
        target_id=ai_response_node.id,
        conditions=[lambda data: data.get("response", "").lower() != "exit"],
    )

    graph = SmartGraph(memory_manager=memory_manager, checkpointer=checkpointer)

    for node in [start_node, ai_response_node, human_feedback_node]:
        graph.add_node(node)

    for edge in [edge1, edge2, edge3]:
        graph.add_edge(edge)

    thread_id = "conversation_1"

    while True:
        final_output, should_exit = graph.execute(
            start_node.id, {"user_input": "Continue the conversation"}, thread_id
        )

        print("\nConversation State:")
        print(f"Short-term memory: {final_output['short_term']}")
        print(f"Long-term memory: {final_output['long_term']}")

        if should_exit:
            print("Conversation ended.")
            break

    print("\nFinal Conversation State:")
    print(f"Short-term memory: {final_output['short_term']}")
    print(f"Long-term memory: {final_output['long_term']}")


if __name__ == "__main__":
    main()
