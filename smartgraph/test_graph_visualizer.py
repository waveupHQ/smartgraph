import os

import networkx as nx
import pytest

from smartgraph.base import BaseActor, Task
from smartgraph.core import Edge, Node
from smartgraph.graph_visualizer import GraphVisualizer


class MockActor(BaseActor):
    def __init__(self, name):
        super().__init__(name, None)  # Passing None as memory_manager for this mock

    async def perform_task(self, task, input_data, state):
        return {"result": f"Performed task: {task.description}"}


def create_mock_graph():
    G = nx.DiGraph()
    actor1 = MockActor("Actor1")
    actor2 = MockActor("Actor2")
    node1 = Node(id="1", actor=actor1, task=Task(description="Task 1"))
    node2 = Node(id="2", actor=actor2, task=Task(description="Task 2"))
    G.add_node("1", node=node1)
    G.add_node("2", node=node2)
    edge = Edge(source_id="1", target_id="2", conditions=[lambda x: True])
    G.add_edge("1", "2", edge=edge)
    return G


def test_draw_graph():
    G = create_mock_graph()
    output_file = "test_graph.png"
    GraphVisualizer.draw_graph(G, output_file)
    assert os.path.exists(output_file)
    os.remove(output_file)


def test_generate_mermaid_diagram():
    G = create_mock_graph()
    mermaid = GraphVisualizer.generate_mermaid_diagram(G)
    assert "graph TD;" in mermaid
    assert '1["Actor1_1"];' in mermaid
    assert '2["Actor2_2"];' in mermaid
    assert "1 -->|condition| 2;" in mermaid


# Add more tests as needed
