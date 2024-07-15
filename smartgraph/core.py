from __future__ import annotations

import asyncio
import logging
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Callable, Dict, List, Optional, Tuple, TypeAlias

import matplotlib.pyplot as plt
import networkx as nx
from pydantic import BaseModel, ConfigDict, Field

from .base import BaseActor, BaseNode, Task
from .checkpointer import Checkpoint, Checkpointer
from .exceptions import ConfigurationError, ExecutionError, GraphStructureError
from .graph_utils import GraphUtils
from .logging import SmartGraphLogger
from .memory import MemoryManager, MemoryState
from .state_manager import StateManager
from .task_executor import TaskExecutor

# Constants
DEFAULT_EDGE_WEIGHT = 1.0
MAX_RESPONSE_LENGTH = 1000  # Maximum length for response storage

# Type aliases
ReducerFunction: TypeAlias = Callable[[Any, Any], Any]


def default_reducer(old_value: Any, new_value: Any) -> Any:
    return new_value


class Node(BaseModel):
    id: str
    actor: BaseActor
    task: Task
    state_manager: StateManager = Field(default_factory=StateManager)
    pre_execute: Optional[Callable] = None
    post_execute: Optional[Callable] = None
    input_data: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(arbitrary_types_allowed=True)

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        self.input_data = input_data
        try:
            output = await TaskExecutor.execute_node_task(self)
            return output
        except ExecutionError as e:
            raise ExecutionError(f"Error executing node {self.id}: {str(e)}", node_id=self.id)

    async def update_state(self, new_state: Dict[str, Any]) -> None:
        for key, value in new_state.items():
            self.state_manager.update_state(key, value)


class Edge(BaseModel):
    source_id: str
    target_id: str
    conditions: List[Callable[[Dict[str, Any]], bool]] = Field(default_factory=list)
    weight: float = DEFAULT_EDGE_WEIGHT

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def is_valid(self, data: Dict[str, Any]) -> bool:
        return all(condition(data) for condition in self.conditions) if self.conditions else True

    def __hash__(self) -> int:
        return hash((self.source_id, self.target_id))

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Edge):
            return self.source_id == other.source_id and self.target_id == other.target_id
        return False


logger = SmartGraphLogger.get_logger()


class SmartGraph(BaseModel):
    graph: nx.DiGraph = Field(default_factory=nx.DiGraph)
    memory_manager: MemoryManager = Field(default_factory=MemoryManager)
    checkpointer: Checkpointer = Field(default_factory=Checkpointer)
    checkpoint_frequency: int = 5

    model_config = ConfigDict(arbitrary_types_allowed=True)

    async def execute(
        self, start_node_id: str, input_data: Dict[str, Any], thread_id: str
    ) -> Tuple[Dict[str, Any], bool]:
        if start_node_id not in self.graph.nodes:
            raise GraphStructureError(f"Start node '{start_node_id}' not found in the graph")

        latest_checkpoint = self.checkpointer.get_latest_checkpoint(thread_id)
        if latest_checkpoint:
            current_node_id = latest_checkpoint.next_nodes[0]
            self.memory_manager.state = MemoryState(**latest_checkpoint.state)
        else:
            current_node_id = start_node_id

        should_exit = False
        node_count = 0
        while not should_exit:
            try:
                current_node = self.graph.nodes[current_node_id]["node"]
                node_output = await TaskExecutor.execute_node_task(current_node)

                # Update the state using reducer functions
                for key, value in node_output.items():
                    await self.memory_manager.update_short_term(key, value)

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

                # Save checkpoint (now less frequent)
                node_count += 1
                if self._should_save_checkpoint(node_count):
                    checkpoint = Checkpoint(
                        node_id=current_node_id,
                        state=self.memory_manager.state.dict(),
                        next_nodes=[edge.target_id for edge in valid_edges],
                    )
                    await self.checkpointer.save_checkpoint(thread_id, checkpoint)

                # Choose the next node (simplified for now)
                current_node_id = valid_edges[0].target_id

                # Update input_data for the next iteration
                input_data = node_output  # noqa: F841

            except ExecutionError as e:
                logger.error(f"Execution error: {str(e)}")
                break
            except Exception as e:
                logger.error(f"Unexpected error: {str(e)}")
                break

        # Cleanup long-term memory
        await self.memory_manager.cleanup_long_term_memory()

        return self.memory_manager.state.dict(), should_exit

    def _should_save_checkpoint(self, node_count: int) -> bool:
        return node_count % self.checkpoint_frequency == 0

    def add_node(self, node: BaseNode) -> None:
        GraphUtils.add_node(self.graph, node)

    def add_edge(self, edge: "Edge") -> None:
        GraphUtils.add_edge(self.graph, edge)

    def draw_graph(self, output_file: str | None = None) -> None:
        import matplotlib.pyplot as plt

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
        else:
            plt.show()
