from __future__ import annotations

import asyncio
from typing import Any, Dict, Optional

from phi.assistant import Assistant
from phi.tools import Toolkit
from pydantic import BaseModel, ConfigDict, Field

from .base import BaseActor, Task
from .exceptions import ActorExecutionError
from .logging import SmartGraphLogger
from .memory import MemoryManager

logger = SmartGraphLogger.get_logger()


# Constants
MAX_RESPONSE_LENGTH = 1000  # Maximum length for response storage


class Actor(BaseModel, BaseActor):
    name: str
    memory_manager: MemoryManager = Field(default_factory=MemoryManager)

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        BaseActor.__init__(self, self.name)

    def perform_task(
        self, task: Task, input_data: Dict[str, Any], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        raise NotImplementedError


class HumanActor(BaseActor):
    def __init__(self, name: str, memory_manager: MemoryManager):
        super().__init__(name, memory_manager)

    async def perform_task(
        self, task: Task, input_data: Dict[str, Any], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        self.log.info(f"Task for {self.name}: {task.description}")
        self.log.debug(f"Input data: {input_data}")

        # Use asyncio.to_thread to run input() in a separate thread
        user_input = await asyncio.to_thread(input, "Enter your response: ")

        # Truncate user input if it exceeds the maximum length
        if len(user_input) > MAX_RESPONSE_LENGTH:
            self.log.warning(
                f"User input exceeds maximum length. Truncating to {MAX_RESPONSE_LENGTH} characters."
            )
            user_input = user_input[:MAX_RESPONSE_LENGTH]

        await self.memory_manager.update_short_term("last_input", user_input)
        await self.memory_manager.update_long_term("conversation_history", user_input)

        return {"response": user_input}


class AIActor(BaseActor):
    def __init__(
        self, name: str, memory_manager: MemoryManager, assistant: Optional[Assistant] = None
    ):
        super().__init__(name, memory_manager)
        self.assistant = assistant
        self.tools: Optional[Toolkit] = None

    async def perform_task(
        self, task: Task, input_data: Dict[str, Any], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        if self.assistant is None:
            self.log.warning("No AI assistant available. Returning mock response.")
            return {"response": "This is a mock AI response."}

        context = await self._build_context(input_data, state)

        prompt = (
            task.prompt.format(**context)
            if task.prompt
            else (f"Task: {task.description}\nContext: {context}\nPlease provide a response.")
        )

        try:
            # Simulate AI response for now
            await asyncio.sleep(1)  # Simulate some processing time
            response = f"AI response to: {prompt}"

            if len(response) > MAX_RESPONSE_LENGTH:
                self.log.warning(
                    f"AI response exceeds maximum length. Truncating to {MAX_RESPONSE_LENGTH} characters."
                )
                response = response[:MAX_RESPONSE_LENGTH]

            self.log.info(f"AI response: {response}")

            await self.memory_manager.update_short_term("last_response", response)
            await self.memory_manager.update_long_term("conversation_history", response)
            await self.memory_manager.update_long_term("max_response_length", len(response))

            return {"response": response}
        except Exception as e:
            error_message = f"Error during AI task execution: {str(e)}"
            self.log.error(error_message)
            raise ActorExecutionError(error_message, actor_name=self.name)

    async def _build_context(
        self, input_data: Dict[str, Any], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        short_term = await self.memory_manager.get_short_term("context")
        long_term = await self.memory_manager.get_long_term("conversation_history")
        return {
            "input": input_data,
            "state": state,
            "short_term_memory": short_term,
            "long_term_memory": long_term,
        }
