from typing import Any, List

import networkx as nx

from .base import BaseNode
from .exceptions import GraphStructureError


class GraphUtils:
    @staticmethod
    def add_node(graph: nx.DiGraph, node: BaseNode) -> None:
        if node.id in graph.nodes:
            raise GraphStructureError(f"Node with id '{node.id}' already exists in the graph")
        graph.add_node(node.id, node=node)

    @staticmethod
    def add_edge(graph: nx.DiGraph, edge: 'Edge') -> None:
        if edge.source_id not in graph.nodes or edge.target_id not in graph.nodes:
            raise GraphStructureError(f"Invalid edge: {edge.source_id} -> {edge.target_id}")
        graph.add_edge(edge.source_id, edge.target_id, edge=edge)

    @staticmethod
    def find_valid_paths(graph: nx.DiGraph, start_node: str, end_node: str, data: Any) -> List[List[str]]:
        all_paths = nx.all_simple_paths(graph, start_node, end_node)
        valid_paths = []
        for path in all_paths:
            if GraphUtils._is_valid_path(graph, path, data):
                valid_paths.append(path)
        return valid_paths

    @staticmethod
    def _is_valid_path(graph: nx.DiGraph, path: List[str], data: Any) -> bool:
        for i in range(len(path) - 1):
            edge = graph[path[i]][path[i+1]]['edge']
            if not edge.is_valid(data):
                return False
        return True
