# smartgraph/components/human_in_the_loop.py

import asyncio
from typing import Any, Optional, Dict

from reactivex import Subject

from ..component import ReactiveAIComponent
from ..graph import ReactiveSmartGraph
from ..core import ReactiveNode
from ..exceptions import ExecutionError
from ..logging import SmartGraphLogger

logger = SmartGraphLogger.get_logger()

class HumanInTheLoopComponent(ReactiveAIComponent):
    def __init__(self, name: str, graph: 'HumanInTheLoopGraph'):
        super().__init__(name)
        self.graph = graph
        self.human_input_event = asyncio.Event()
        self.human_input_value = None

    async def _get_human_approval(self, data: Any) -> bool:
        logger.info(f"Requesting approval for: {data}")
        self.graph.global_output.on_next({"type": "approval_request", "data": data})
        
        self.human_input_event.clear()
        await self.human_input_event.wait()
        
        approval = self.human_input_value.lower() in ('yes', 'y', 'true', '1')
        logger.info(f"Approval {'granted' if approval else 'denied'}")
        return approval

    def submit_human_input(self, input_data: Any):
        self.human_input_value = input_data
        self.human_input_event.set()

    def get_system_output_observable(self):
        return self.graph.global_output

    def get_final_output_observable(self):
        return self.graph.global_output

    async def process(self, input_data: Any) -> Any:
        # This method is required by ReactiveAIComponent, but not used in this context
        pass

class HumanInTheLoopGraph(ReactiveSmartGraph):
    def __init__(self):
        super().__init__()
        self.hil_component = HumanInTheLoopComponent("HILComponent", self)
        self.current_node = None
        self.global_output = Subject()

    async def execute(self, start_node_id: str, input_data: Any) -> Any:
        self.current_node = self.nodes.get(start_node_id)
        
        async def process_node_with_approval(node_id: str, data: Any):
            node = self.nodes[node_id]
            if getattr(node, 'requires_approval', False):
                approval = await self.hil_component._get_human_approval(data)
                if not approval:
                    logger.info("Transaction rejected by user")
                    return {"status": "rejected", "message": "Action not approved by human"}
            result = await node.process(data)
            logger.info(f"Node {node_id} processed. Result: {result}")
            return result

        async def traverse_graph(node_id: str, data: Any):
            self.current_node = self.nodes.get(node_id)
            result = await process_node_with_approval(node_id, data)
            if isinstance(result, dict) and result.get("status") == "rejected":
                return result
            
            next_nodes = list(self.graph.successors(node_id))
            if not next_nodes:
                return result
            
            for next_node in next_nodes:
                edge_data = self.graph.get_edge_data(node_id, next_node)
                condition = edge_data.get("condition", lambda _: True)
                if condition(result):
                    result = await traverse_graph(next_node, result)
            return result

        try:
            final_result = await asyncio.wait_for(traverse_graph(start_node_id, input_data), timeout=60)
            self.current_node = None
            logger.info(f"Execution completed. Final result: {final_result}")
            return final_result
        except Exception as e:
            logger.error(f"Execution failed: {e}")
            raise ExecutionError(f"Error during execution: {str(e)}", node_id=start_node_id)

    def get_current_node(self) -> Optional[ReactiveNode]:
        return self.current_node

    def get_hil_component(self) -> HumanInTheLoopComponent:
        return self.hil_component

