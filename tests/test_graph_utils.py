import pytest
import networkx as nx
from smartgraph.graph_utils import GraphUtils
from smartgraph.base import BaseNode, Task
from smartgraph.exceptions import GraphStructureError

class MockNode(BaseNode):
    def __init__(self, id: str):
        super().__init__(id, None, Task(description="Mock task"))

class MockEdge:
    def __init__(self, source_id: str, target_id: str, is_valid_func=None):
        self.source_id = source_id
        self.target_id = target_id
        self.is_valid_func = is_valid_func or (lambda data: True)

    def is_valid(self, data):
        return self.is_valid_func(data)

def test_add_node():
    graph = nx.DiGraph()
    node = MockNode("test_node")
    GraphUtils.add_node(graph, node)
    assert "test_node" in graph.nodes
    assert graph.nodes["test_node"]["node"] == node

def test_add_node_duplicate():
    graph = nx.DiGraph()
    node = MockNode("test_node")
    GraphUtils.add_node(graph, node)
    with pytest.raises(GraphStructureError):
        GraphUtils.add_node(graph, node)

def test_add_edge():
    graph = nx.DiGraph()
    node1 = MockNode("node1")
    node2 = MockNode("node2")
    GraphUtils.add_node(graph, node1)
    GraphUtils.add_node(graph, node2)
    edge = MockEdge("node1", "node2")
    GraphUtils.add_edge(graph, edge)
    assert graph.has_edge("node1", "node2")
    assert graph["node1"]["node2"]["edge"] == edge

def test_add_edge_invalid():
    graph = nx.DiGraph()
    node = MockNode("node1")
    GraphUtils.add_node(graph, node)
    edge = MockEdge("node1", "non_existent_node")
    with pytest.raises(GraphStructureError):
        GraphUtils.add_edge(graph, edge)

def test_find_valid_paths():
    graph = nx.DiGraph()
    nodes = [MockNode(f"node{i}") for i in range(4)]
    for node in nodes:
        GraphUtils.add_node(graph, node)
    
    edges = [
        MockEdge("node0", "node1"),
        MockEdge("node1", "node2"),
        MockEdge("node1", "node3"),
        MockEdge("node2", "node3", lambda data: data.get("condition", False)),
    ]
    for edge in edges:
        GraphUtils.add_edge(graph, edge)

    valid_paths = GraphUtils.find_valid_paths(graph, "node0", "node3", {"condition": True})
    assert set(map(tuple, valid_paths)) == {("node0", "node1", "node2", "node3"), ("node0", "node1", "node3")}

    valid_paths = GraphUtils.find_valid_paths(graph, "node0", "node3", {"condition": False})
    assert set(map(tuple, valid_paths)) == {("node0", "node1", "node3")}
