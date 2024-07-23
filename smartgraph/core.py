# smartgraph/core.py

from __future__ import annotations

from typing import Any, Dict, List, Optional

import networkx as nx
from reactivex import Observable, Subject
from reactivex import operators as ops
from reactivex.subject import BehaviorSubject, Subject  # noqa: F811

from .component import ReactiveAIComponent
from .exceptions import ExecutionError, GraphStructureError
from .logging import SmartGraphLogger

logger = SmartGraphLogger.get_logger()


class StateManager:
    def __init__(self):
        self._global_state = BehaviorSubject({})
        self._node_states: Dict[str, BehaviorSubject] = {}
        self._state_change_subject = Subject()

    def get_global_state(self) -> BehaviorSubject:
        return self._global_state

    def update_global_state(self, update: Dict[str, Any]):
        current_state = self._global_state.value
        new_state = {**current_state, **update}
        self._global_state.on_next(new_state)
        self._state_change_subject.on_next(("global", update))
        logger.info(f"Global state updated: {update}")

    def get_node_state(self, node_id: str) -> BehaviorSubject:
        if node_id not in self._node_states:
            self._node_states[node_id] = BehaviorSubject({})
        return self._node_states[node_id]

    def update_node_state(self, node_id: str, update: Dict[str, Any]):
        if node_id not in self._node_states:
            self._node_states[node_id] = BehaviorSubject({})
        current_state = self._node_states[node_id].value
        new_state = {**current_state, **update}
        self._node_states[node_id].on_next(new_state)
        self._state_change_subject.on_next((node_id, update))
        logger.info(f"Node {node_id} state updated: {update}")

    def get_state_changes(self) -> Subject:
        return self._state_change_subject

    def get_combined_state(self, node_id: Optional[str] = None) -> Dict[str, Any]:
        global_state = self._global_state.value
        if node_id is None:
            return global_state
        node_state = self._node_states.get(node_id, BehaviorSubject({})).value
        return {**global_state, **node_state}


class ReactiveNode:
    def __init__(
        self,
        id: str,
        component: ReactiveAIComponent,
        requires_approval: bool = False,
        requires_input: bool = False,
        state_manager: Optional["StateManager"] = None,
    ):
        self.id = id
        self.component = component
        self.input = component.input
        self.output = component.output
        self.requires_approval = requires_approval
        self.requires_input = requires_input
        self.state_manager = state_manager
        self.state = self.state_manager.get_node_state(self.id) if self.state_manager else None

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
        if self.state_manager:
            # Update node state with input data
            self.state_manager.update_node_state(self.id, {"last_input": input_data})

        result = await self.component.process(input_data)

        if self.state_manager:
            # Update node state with output data
            self.state_manager.update_node_state(self.id, {"last_output": result})

        return result

    def get_state(self) -> Optional[Dict[str, Any]]:
        return self.state_manager.get_combined_state(self.id) if self.state_manager else None

    def update_state(self, update: Dict[str, Any]):
        if self.state_manager:
            self.state_manager.update_node_state(self.id, update)


class ReactiveEdge:
    def __init__(self, source_id: str, target_id: str, condition: Optional[callable] = None):
        self.source_id = source_id
        self.target_id = target_id
        self.condition = condition or (lambda _: True)

    def is_valid(self, data: Any) -> bool:
        return self.condition(data)
