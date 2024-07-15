# smartgraph/base.py

from typing import Any, Dict, Optional

from .logging import SmartGraphLogger


class Task:
    def __init__(self, description: str, prompt: Optional[str] = None):
        self.description = description
        self.prompt = prompt


class BaseActor:
    def __init__(self, name: str):
        self.name = name
        self._log = SmartGraphLogger.get_logger()

    @property
    def log(self):
        return self._log

    def perform_task(
        self, task: "Task", input_data: Dict[str, Any], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        self.log.debug(f"Actor {self.name} performing task: {task.description}")
        raise NotImplementedError


class BaseNode:
    def __init__(self, id: str, actor: BaseActor, task: "Task"):
        self.id = id
        self.actor = actor
        self.task = task
        self.state: Dict[str, Any] = {}
        self._log = SmartGraphLogger.get_logger()

    @property
    def log(self):
        return self._log

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        self.log.info(f"Executing node {self.id}")
        self.log.debug(f"Input data: {input_data}")
        try:
            result = self.actor.perform_task(self.task, input_data, self.state)
            self.log.debug(f"Node {self.id} execution result: {result}")
            return result
        except Exception as e:
            self.log.error(f"Error executing node {self.id}: {str(e)}")
            raise

    def update_state(self, new_state: Dict[str, Any]):
        self.log.debug(f"Updating state of node {self.id}")
        self.state.update(new_state)
        self.log.debug(f"New state: {self.state}")
