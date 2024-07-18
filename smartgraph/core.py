from __future__ import annotations

import asyncio
import json
import logging
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Callable, Dict, List, Optional, Tuple, TypeAlias

import jsonpickle
import matplotlib.pyplot as plt
import networkx as nx
from pydantic import BaseModel, ConfigDict, Field

from .base import BaseActor, BaseNode, Task
from .checkpoint_manager import Checkpoint, CheckpointManager
from .checkpointer import Checkpointer
from .condition_evaluator import ConditionEvaluator
from .exceptions import ConfigurationError, ExecutionError, GraphStructureError
from .graph_utils import GraphUtils
from .graph_visualizer import GraphVisualizer
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
            raise ExecutionError(
                f"Error executing node {self.id}: {str(e)}", node_id=self.id
            )  # noqa: B904

    async def update_state(self, new_state: Dict[str, Any]) -> None:
        for key, value in new_state.items():
            self.state_manager.update_state(key, value)


class Edge(BaseModel):
    source_id: str
    target_id: str
    conditions: List[Callable[[Dict[str, Any]], bool]] = Field(default_factory=list)
    weight: float = 1.0

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def is_valid(self, data: Dict[str, Any]) -> bool:
        return ConditionEvaluator.evaluate(self.conditions, data)

    def __hash__(self):  # noqa: D105
        return hash((self.source_id, self.target_id))

    def __eq__(self, other):  # noqa: D105
        if isinstance(other, Edge):
            return self.source_id == other.source_id and self.target_id == other.target_id
        return False

    @classmethod
    def with_condition(cls, source_id: str, target_id: str, key: str, value: Any):
        condition = ConditionEvaluator.create_condition(key, value)
        return cls(source_id=source_id, target_id=target_id, conditions=[condition])

    @classmethod
    def with_range_condition(  # noqa: PLR0913
        cls, source_id: str, target_id: str, key: str, min_value: float, max_value: float
    ):
        condition = ConditionEvaluator.create_range_condition(key, min_value, max_value)
        return cls(source_id=source_id, target_id=target_id, conditions=[condition])


logger = SmartGraphLogger.get_logger()


class SmartGraph(BaseModel):
    graph: nx.DiGraph = Field(default_factory=nx.DiGraph)
    memory_manager: MemoryManager = Field(default_factory=MemoryManager)
    checkpoint_manager: CheckpointManager = Field(default_factory=CheckpointManager)
    checkpoint_frequency: int = 2  # Save checkpoint every 5 nodes

    model_config = ConfigDict(arbitrary_types_allowed=True)

    async def execute(
            self, start_node_id: str, input_data: Dict[str, Any], thread_id: str
        ) -> Tuple[Dict[str, Any], bool]:
            if start_node_id not in self.graph.nodes:
                raise GraphStructureError(f"Start node '{start_node_id}' not found in the graph")

            # Load the latest checkpoint if available
            latest_checkpoint = await self.checkpoint_manager.get_latest_checkpoint(thread_id)
            if latest_checkpoint:
                current_node_id = latest_checkpoint.next_nodes[0]
                self.memory_manager.state = MemoryState(**json.loads(latest_checkpoint.state))
            else:
                current_node_id = start_node_id

            should_exit = False
            node_count = 0
            while not should_exit:
                try:
                    # Execute the current node
                    current_node = self.graph.nodes[current_node_id]["node"]
                    node_output = await current_node.execute(input_data)

                    # Update the state
                    for key, value in node_output.items():
                        await self.memory_manager.update_short_term(key, value)

                    # Check for exit condition
                    if node_output.get("response", "").lower() == "exit":
                        logger.info("Exit command received. Ending execution.")
                        should_exit = True
                        break

                    # Find valid edges and next nodes
                    next_node_ids = list(self.graph.successors(current_node_id))
                    if not next_node_ids:
                        logger.info("No next nodes found. Ending execution.")
                        should_exit = True
                        break

                    valid_edges = [
                        self.graph[current_node_id][next_node_id]["edge"]
                        for next_node_id in next_node_ids
                        if self.graph[current_node_id][next_node_id]["edge"].is_valid(node_output)
                    ]

                    if not valid_edges:
                        logger.info("No valid edges found. Ending execution.")
                        should_exit = True
                        break

                    # Save checkpoint if necessary
                    node_count += 1
                    if node_count % self.checkpoint_frequency == 0:
                        checkpoint = Checkpoint(
                            node_id=current_node_id,
                            state=json.dumps(self.memory_manager.state.dict()),
                            next_nodes=[edge.target_id for edge in valid_edges],
                        )
                        await self.checkpoint_manager.save_checkpoint(thread_id, checkpoint)

                    # Move to the next node
                    current_node_id = valid_edges[0].target_id

                    # Update input_data for the next iteration
                    input_data = node_output

                except Exception as e:
                    logger.error(f"Error during execution: {str(e)}")
                    should_exit = True
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

    def draw_graph(self, output_file: Optional[str] = None, **kwargs: Any) -> None:
        """Draw the graph using the GraphVisualizer.

        Args:
            output_file (Optional[str]): If provided, save the visualization to this file.
            **kwargs: Additional keyword arguments for customization.
        """
        GraphVisualizer.draw_graph(self.graph, output_file, **kwargs)

    def generate_mermaid_diagram(self) -> str:
        """Generate a Mermaid diagram representation of the graph.

        Returns:
            str: Mermaid diagram representation of the graph.
        """
        return GraphVisualizer.generate_mermaid_diagram(self.graph)

