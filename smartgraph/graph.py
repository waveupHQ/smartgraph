import asyncio
from typing import Any, Dict, Optional

import networkx as nx
from reactivex import Observable, Subject

from .core import ReactiveEdge, ReactiveNode, StateManager
from .exceptions import ExecutionError, GraphStructureError
from .logging import SmartGraphLogger

logger = SmartGraphLogger.get_logger()


class ReactiveSmartGraph:
    def __init__(self):
        self.graph = nx.DiGraph()
        self.nodes: Dict[str, ReactiveNode] = {}
        self.global_input = Subject()
        self.global_output = Subject()
        self.state_manager = StateManager()

        # Subscribe to state changes
        self.state_manager.get_state_changes().subscribe(
            on_next=lambda change: logger.debug(f"State change: {change}")
        )

    def add_node(self, node: ReactiveNode) -> None:
        if node.id in self.nodes:
            raise GraphStructureError(f"Node with id '{node.id}' already exists in the graph")
        if node.state_manager is None:
            node.state_manager = self.state_manager
        self.nodes[node.id] = node
        self.graph.add_node(node.id)
        node.output.subscribe(self.global_output)
        logger.debug(f"Added node: {node.id}")

    def add_edge(self, edge: ReactiveEdge) -> None:
        if edge.source_id not in self.nodes or edge.target_id not in self.nodes:
            raise GraphStructureError(f"Invalid edge: {edge.source_id} -> {edge.target_id}")
        self.graph.add_edge(edge.source_id, edge.target_id, condition=edge.condition)
        logger.debug(f"Added edge: {edge.source_id} -> {edge.target_id}")

    async def execute(self, start_node_id: str, input_data: Any) -> Any:
        if start_node_id not in self.nodes:
            raise GraphStructureError(f"Start node '{start_node_id}' not found in the graph")

        logger.info(f"Starting execution from node: {start_node_id}")

        # Update global state with input data
        self.state_manager.update_global_state({"execution_input": input_data})

        async def process_node(node_id: str, data: Any):
            node = self.nodes[node_id]
            logger.debug(f"Processing node: {node_id}")
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
                traverse_graph(start_node_id, input_data), timeout=60
            )
            logger.info(f"Execution completed. Final result: {final_result}")

            # Update global state with execution result
            self.state_manager.update_global_state({"execution_result": final_result})

            return final_result
        except ValueError as e:
            logger.error(f"Execution failed: {str(e)}")
            raise ExecutionError(  # noqa: B904
                f"Error during execution: {str(e)}", node_id=start_node_id
            )  # noqa: B904
        except asyncio.TimeoutError:
            logger.error("Execution timed out")
            raise
        except Exception as e:
            logger.error(f"Execution failed: {e}")
            raise

    def aggregate_results(self, results):
        # This method can be overridden in subclasses if needed
        return results[-1] if results else None

    def update_global_state(self, update: Dict[str, Any]):
        self.state_manager.update_global_state(update)

    def get_node(self, node_id: str) -> Optional[ReactiveNode]:
        return self.nodes.get(node_id)

    def get_global_state(self) -> Dict[str, Any]:
        return self.state_manager.get_global_state().value
