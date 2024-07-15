# examples/manual_test.py

import logging

from smartgraph import AIActor, Edge, HumanActor, Node, SmartGraph, Task
from smartgraph.logging import SmartGraphLogger
from smartgraph.memory import MemoryManager

# Set up logging
logger = SmartGraphLogger.get_logger()
logger.set_level("DEBUG")
logger.add_file_handler("smartgraph_test.log", "DEBUG")

# Create a simple graph
memory_manager = MemoryManager()
human_actor = HumanActor(name="User", memory_manager=memory_manager)
ai_actor = AIActor(name="AI", memory_manager=memory_manager)  # No need to pass assistant=None

start_node = Node(id="start", actor=human_actor, task=Task(description="Start conversation"))
ai_response_node = Node(id="ai_response", actor=ai_actor, task=Task(description="AI response"))
human_feedback_node = Node(
    id="human_feedback", actor=human_actor, task=Task(description="Human feedback")
)

edge1 = Edge(source_id="start", target_id="ai_response")
edge2 = Edge(source_id="ai_response", target_id="human_feedback")
edge3 = Edge(source_id="human_feedback", target_id="ai_response")

graph = SmartGraph()

# Add nodes and edges
for node in [start_node, ai_response_node, human_feedback_node]:
    graph.add_node(node)

for edge in [edge1, edge2, edge3]:
    graph.add_edge(edge)

# Execute the graph
logger.info("Starting graph execution")
final_output, should_exit = graph.execute("start", {"user_input": "Hello, AI!"}, "test_thread")

logger.info(f"Execution completed. Final output: {final_output}")
logger.info(f"Should exit: {should_exit}")

# Draw the graph
graph.draw_graph("test_graph.png")

print("Manual test completed. Check smartgraph_test.log for logging output.")
