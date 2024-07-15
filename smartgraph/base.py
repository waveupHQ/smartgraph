# base.py
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional

from .logging import SmartGraphLogger
from .memory import MemoryManager


@dataclass
class Task:
    description: str
    prompt: Optional[str] = None


class BaseActor(ABC):
    def __init__(self, name: str, memory_manager: MemoryManager):
        self.name = name
        self.memory_manager = memory_manager
        self._log = SmartGraphLogger.get_logger()

    @property
    def log(self) -> SmartGraphLogger:
        return self._log

    @abstractmethod
    async def perform_task(
        self, task: "Task", input_data: Dict[str, Any], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        pass


class BaseNode:
    def __init__(self, id: str, actor: BaseActor, task: Task) -> None:
        self.id = id
        self.actor = actor
        self.task = task
        self.state: Dict[str, Any] = {}
        self._log = SmartGraphLogger.get_logger()

    @property
    def log(self) -> SmartGraphLogger:
        return self._log

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        self.log.info(f"Executing node {self.id}")
        self.log.debug(f"Input data: {input_data}")

        try:
            result = await self.actor.perform_task(self.task, input_data, self.state)
            self.log.debug(f"Node {self.id} execution result: {result}")
            return result
        except Exception as e:
            self.log.error(f"Error executing node {self.id}: {str(e)}")
            raise

    async def update_state(self, new_state: Dict[str, Any]) -> None:
        self.log.debug(f"Updating state of node {self.id}")
        self.state.update(new_state)
        self.log.debug(f"New state: {self.state}")
