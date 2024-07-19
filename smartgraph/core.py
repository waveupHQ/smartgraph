# smartgraph/core.py

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional

import networkx as nx
from reactivex import Observable, Subject
from reactivex import operators as ops
from reactivex.subject import Subject  # noqa: F811

from .component import ReactiveAIComponent
from .components import AggregatorComponent
from .exceptions import GraphStructureError
from .logging import SmartGraphLogger

logger = SmartGraphLogger.get_logger()


class ReactiveNode:
    def __init__(self, id: str, component: ReactiveAIComponent):
        self.id = id
        self.component = component
        self.input = component.input
        self.output = component.output

        # Set up logging for input and output
        self.input.subscribe(
            on_next=lambda x: logger.debug(f"Node {self.id} received input: {x}"),
            on_error=lambda e: logger.error(f"Node {self.id} input error: {e}"),
        )
        self.output.subscribe(
            on_next=lambda x: logger.debug(f"Node {self.id} produced output: {x}"),
            on_error=lambda e: logger.error(f"Node {self.id} output error: {e}"),
        )

    async def process(self, input_data: Any) -> Any:
        return await self.component.process(input_data)


class ReactiveEdge:
    def __init__(self, source_id: str, target_id: str, condition: Optional[callable] = None):
        self.source_id = source_id
        self.target_id = target_id
        self.condition = condition or (lambda _: True)

    def is_valid(self, data: Any) -> bool:
        return self.condition(data)


class ReactiveSmartGraph:
    def __init__(self):
        self.graph = nx.DiGraph()
        self.nodes: Dict[str, ReactiveNode] = {}
        self.global_input = Subject()
        self.global_output = Subject()

    def add_node(self, node: "ReactiveNode") -> None:
        if node.id in self.nodes:
            raise GraphStructureError(f"Node with id '{node.id}' already exists in the graph")
        self.nodes[node.id] = node
        self.graph.add_node(node.id)
        node.output.subscribe(self.global_output)
        logger.debug(f"Added node: {node.id}")

    def add_edge(self, edge: "ReactiveEdge") -> None:
        if edge.source_id not in self.nodes or edge.target_id not in self.nodes:
            raise GraphStructureError(f"Invalid edge: {edge.source_id} -> {edge.target_id}")
        self.graph.add_edge(edge.source_id, edge.target_id, condition=edge.condition)
        logger.debug(f"Added edge: {edge.source_id} -> {edge.target_id}")

    async def execute(self, start_node_id: str, input_data: Any) -> Any:
        if start_node_id not in self.nodes:
            raise GraphStructureError(f"Start node '{start_node_id}' not found in the graph")

        logger.info(f"Starting execution from node: {start_node_id}")

        async def process_node(node_id: str, data: Any):
            node = self.nodes[node_id]
            logger.debug(f"Processing node: {node_id}")
            if isinstance(node.component, AggregatorComponent) and not isinstance(data, list):
                data = [data]
            result = await node.process(data)
            logger.debug(f"Node {node_id} processed. Result: {result}")
            return result

        async def traverse_graph(node_id: str, data: Any):
            result = await process_node(node_id, data)
            next_nodes = list(self.graph.successors(node_id))
            if not next_nodes:
                return result
            tasks = []
            for next_node in next_nodes:
                edge_data = self.graph.get_edge_data(node_id, next_node)
                condition = edge_data.get("condition", lambda _: True)
                if condition(result):
                    tasks.append(traverse_graph(next_node, result))
            if tasks:
                results = await asyncio.gather(*tasks)
                return results[-1] if results else result
            return result

        try:
            final_result = await asyncio.wait_for(
                traverse_graph(start_node_id, input_data), timeout=30
            )
            logger.info(f"Execution completed. Final result: {final_result}")
            return final_result
        except asyncio.TimeoutError:
            logger.error("Execution timed out")
            raise
        except Exception as e:
            logger.error(f"Execution failed: {e}")
            raise
