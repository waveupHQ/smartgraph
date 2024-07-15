# smartgraph/base.py

from typing import Any, Dict, Optional


class Task:
    def __init__(self, description: str, prompt: Optional[str] = None):
        self.description = description
        self.prompt = prompt


class BaseActor:
    def __init__(self, name: str):
        self.name = name

    def perform_task(
        self, task: Task, input_data: Dict[str, Any], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        raise NotImplementedError


class BaseNode:
    def __init__(self, id: str, actor: BaseActor, task: Task):
        self.id = id
        self.actor = actor
        self.task = task
        self.state: Dict[str, Any] = {}

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        return self.actor.perform_task(self.task, input_data, self.state)

    def update_state(self, new_state: Dict[str, Any]):
        self.state.update(new_state)
