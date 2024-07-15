from __future__ import annotations

from typing import Any, Dict, Optional

from phi.assistant import Assistant
from phi.tools import Toolkit
from pydantic import BaseModel, ConfigDict, Field

from .base import BaseActor, Task
from .exceptions import ActorExecutionError
from .logging import SmartGraphLogger
from .memory import MemoryManager

# Constants
MAX_RESPONSE_LENGTH = 1000  # Maximum length for response storage

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


class HumanActor(Actor):
    def perform_task(
        self, task: Task, input_data: Dict[str, Any], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        logger.info(f"Task for {self.name}: {task.description}")
        logger.debug(f"Input data: {input_data}")

        user_input = input("Enter your response: ")

        # Truncate user input if it exceeds the maximum length
        if len(user_input) > MAX_RESPONSE_LENGTH:
            logger.warning(
                f"User input exceeds maximum length. Truncating to {MAX_RESPONSE_LENGTH} characters."
            )
            user_input = user_input[:MAX_RESPONSE_LENGTH]

        self.memory_manager.update_short_term("last_input", user_input)
        self.memory_manager.update_long_term("conversation_history", user_input)

        return {"response": user_input}


class AIActor(Actor):
    assistant: Optional[Assistant] = None
    tools: Optional[Toolkit] = None

    def perform_task(
        self, task: Task, input_data: Dict[str, Any], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        if self.assistant is None:
            logger.warning("No AI assistant available. Returning mock response.")
            return {"response": "This is a mock AI response."}

        context = self._build_context(input_data, state)

        prompt = (
            task.prompt.format(**context)
            if task.prompt
            else (f"Task: {task.description}\nContext: {context}\nPlease provide a response.")
        )

        try:
            response_generator = self.assistant.chat(prompt)

            response_chunks = []
            for chunk in response_generator:
                response_chunks.append(chunk)

            response = "".join(response_chunks)

            # Truncate response if it exceeds the maximum length
            if len(response) > MAX_RESPONSE_LENGTH:
                logger.warning(
                    f"AI response exceeds maximum length. Truncating to {MAX_RESPONSE_LENGTH} characters."
                )
                response = response[:MAX_RESPONSE_LENGTH]

            logger.info(f"AI response: {response}")

            self.memory_manager.update_short_term("last_response", response)
            self.memory_manager.update_long_term("conversation_history", response)
            self.memory_manager.update_long_term("max_response_length", len(response))

            return {"response": response}
        except Exception as e:
            error_message = f"Error during AI task execution: {str(e)}"
            logger.error(error_message)
            raise ActorExecutionError(error_message, actor_name=self.name)

    def _build_context(self, input_data: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "input": input_data,
            "state": state,
            "short_term_memory": self.memory_manager.state.short_term,
            "long_term_memory": self.memory_manager.state.long_term.dict(),
        }
