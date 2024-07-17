from __future__ import annotations

import asyncio
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field

from .assistant_conversation import AssistantConversation
from .base import BaseActor, Task
from .exceptions import ActorExecutionError
from .logging import SmartGraphLogger
from .memory import MemoryManager

logger = SmartGraphLogger.get_logger()


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

        await self.memory_manager.update_short_term("last_input", user_input)
        await self.memory_manager.update_long_term("conversation_history", user_input)

        return {"response": user_input}


class AIActor(BaseActor):
    def __init__(
        self,
        name: str,
        memory_manager: MemoryManager,
        assistant: Optional[AssistantConversation] = None,
    ):
        super().__init__(name, memory_manager)
        self.assistant = assistant

    async def perform_task(
        self, task: Task, input_data: Dict[str, Any], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        if self.assistant is None:
            self.log.warning("No AI assistant available. Returning mock response.")
            return {"response": "This is a mock AI response."}

        context = await self._build_context(input_data, state)

        prompt = (
            task.prompt.format(input=context["input"])
            if task.prompt
            else (f"Task: {task.description}\nContext: {context}\nPlease provide a response.")
        )

        try:
            response = await self.assistant.run(prompt)

            if response is None:
                self.log.warning("Received None response from assistant")
                return {"response": "I'm sorry, but I couldn't generate a response at this time."}

            self.log.info(f"AI response: {response}")

            await self.memory_manager.update_short_term("last_response", response)
            await self.memory_manager.update_long_term("conversation_history", response)

            return {"response": response}
        except Exception as e:
            error_message = f"Error during AI task execution: {str(e)}"
            self.log.error(error_message)
            raise ActorExecutionError(error_message, actor_name=self.name)  # noqa: B904

    async def _build_context(
        self, input_data: Dict[str, Any], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        short_term = await self.memory_manager.get_short_term("context")
        long_term = await self.memory_manager.get_long_term("conversation_history")
        return {
            "input": input_data if isinstance(input_data, str) else str(input_data),
            "state": state,
            "short_term_memory": short_term,
            "long_term_memory": long_term,
        }
