# smartgraph/core.py

import logging
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Callable, Dict, List, Optional, TypeAlias

import matplotlib.pyplot as plt
import networkx as nx
from pydantic import BaseModel, ConfigDict, Field

from .base import BaseActor, BaseNode, Task
from .checkpointer import Checkpoint, Checkpointer
from .exceptions import ConfigurationError, ExecutionError, GraphStructureError
from .logging import SmartGraphLogger
from .memory import MemoryManager, MemoryState

ReducerFunction: TypeAlias = Callable[[Any, Any], Any]


def default_reducer(old_value: Any, new_value: Any) -> Any:
    return new_value


class Node(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    actor: BaseActor
    task: Task
    state: Dict[str, Any] = Field(default_factory=dict)
    pre_execute: Optional[Callable] = None
    post_execute: Optional[Callable] = None

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        if self.pre_execute:
            input_data = self.pre_execute(input_data, self.state)

        try:
            output = self.actor.perform_task(self.task, input_data, self.state)
        except Exception as e:
            raise ExecutionError(f"Error executing node {self.id}: {str(e)}", node_id=self.id) from e

        if self.post_execute:
            output = self.post_execute(output, self.state)

        return output

    def update_state(self, new_state: Dict[str, Any]):
        self.state.update(new_state)


class Edge(BaseModel):
    source_id: str
    target_id: str
    conditions: List[Callable[[Dict[str, Any]], bool]] = Field(default_factory=list)
    weight: float = 1.0

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def is_valid(self, data: Dict[str, Any]) -> bool:
        return all(condition(data) for condition in self.conditions) if self.conditions else True

    def __hash__(self):
        return hash((self.source_id, self.target_id))

    def __eq__(self, other):
        if isinstance(other, Edge):
            return self.source_id == other.source_id and self.target_id == other.target_id
        return False


logger = SmartGraphLogger.get_logger()


class SmartGraph(BaseModel):
    graph: nx.DiGraph = Field(default_factory=nx.DiGraph)
    memory_manager: MemoryManager = Field(default_factory=MemoryManager)
    checkpointer: Checkpointer = Field(default_factory=Checkpointer)

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def execute(
        self, start_node_id: str, input_data: Dict[str, Any], thread_id: str
    ) -> Dict[str, Any]:
        if start_node_id not in self.graph.nodes:
            raise GraphStructureError(f"Start node '{start_node_id}' not found in the graph")

        latest_checkpoint = self.checkpointer.get_latest_checkpoint(thread_id)
        if latest_checkpoint:
            current_node_id = latest_checkpoint.next_nodes[0]
            self.memory_manager.state = MemoryState(**latest_checkpoint.state)
        else:
            current_node_id = start_node_id

        should_exit = False
        while not should_exit:
            try:
                current_node = self.graph.nodes[current_node_id]["node"]
                node_output = current_node.execute(input_data)

                # Update the state using reducer functions
                for key, value in node_output.items():
                    self.memory_manager.update_short_term(key, value)

                # Check for exit condition
                if node_output.get("response", "").lower() == "exit":
                    logger.info("Exit command received. Ending conversation.")
                    should_exit = True
                    break

                next_node_ids = list(self.graph.successors(current_node_id))
                if not next_node_ids:
                    break

                valid_edges = [
                    self.graph[current_node_id][next_node_id]["edge"]
                    for next_node_id in next_node_ids
                    if self.graph[current_node_id][next_node_id]["edge"].is_valid(node_output)
                ]

                if not valid_edges:
                    break

                # Save checkpoint
                checkpoint = Checkpoint(
                    node_id=current_node_id,
                    state=self.memory_manager.state.dict(),
                    next_nodes=[edge.target_id for edge in valid_edges],
                )
                self.checkpointer.save_checkpoint(thread_id, checkpoint)

                if len(valid_edges) == 1:
                    current_node_id = valid_edges[0].target_id
                else:
                    # For simplicity, we'll just choose the first valid edge in case of multiple valid edges
                    current_node_id = valid_edges[0].target_id

                # Update input_data for the next iteration
                input_data = node_output

            except ExecutionError as e:
                logger.error(f"Execution error: {str(e)}")
                break
            except Exception as e:
                logger.error(f"Unexpected error: {str(e)}")
                break

        return self.memory_manager.state.dict(), should_exit

    def add_node(self, node: Node):
        if node.id in self.graph.nodes:
            raise ConfigurationError(f"Node with id '{node.id}' already exists in the graph")
        self.graph.add_node(node.id, node=node)

    def add_edge(self, edge: Edge):
        if edge.source_id not in self.graph.nodes or edge.target_id not in self.graph.nodes:
            logger.error(f"Attempted to add invalid edge: {edge.source_id} -> {edge.target_id}")
            raise GraphStructureError(f"Invalid edge: {edge.source_id} -> {edge.target_id}")
        self.graph.add_edge(edge.source_id, edge.target_id, edge=edge)
        logger.info(f"Added edge: {edge.source_id} -> {edge.target_id}")

    def _execute_path(self, start_node_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        logger.debug(f"Executing path starting from node {start_node_id}")
        result, _ = self.execute(start_node_id, input_data, thread_id=str(uuid.uuid4()))
        return result

    def _combine_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        logger.debug("Combining results from multiple paths")
        combined = {}
        for result in results:
            for key, value in result.items():
                if key in combined:
                    reducer = self.memory_manager.short_term_reducers.get(key, default_reducer)
                    combined[key] = reducer(combined[key], value)
                else:
                    combined[key] = value
        logger.debug("Results combined successfully")
        return combined

    def draw_graph(self, output_file: Optional[str] = None):
        logger.info("Drawing graph visualization")
        pos = nx.spring_layout(self.graph)
        plt.figure(figsize=(12, 8))
        nx.draw(
            self.graph,
            pos,
            with_labels=False,
            node_color="lightblue",
            node_size=3000,
            font_size=10,
            font_weight="bold",
        )

        # Add edge labels
        edge_labels = {}
        for u, v, d in self.graph.edges(data=True):
            if d["edge"].conditions:
                condition_name = d["edge"].conditions[0].__name__
                if condition_name == "<lambda>":
                    condition_name = "condition"
                edge_labels[(u, v)] = condition_name
            else:
                edge_labels[(u, v)] = ""
        nx.draw_networkx_edge_labels(self.graph, pos, edge_labels=edge_labels, font_size=8)

        # Add node labels
        node_labels = {}
        for node, data in self.graph.nodes(data=True):
            actor_name = data["node"].actor.name
            task_desc = data["node"].task.description
            node_labels[node] = f"{actor_name}\n{task_desc}"

        nx.draw_networkx_labels(self.graph, pos, labels=node_labels, font_size=8)

        plt.title("SmartGraph Conversation Flow")
        plt.axis("off")

        if output_file:
            plt.savefig(output_file, format="png", dpi=300, bbox_inches="tight")
            plt.close()
            logger.info(f"Graph visualization saved to {output_file}")
        else:
            plt.show()
            logger.info("Graph visualization displayed")
