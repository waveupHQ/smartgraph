from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional

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
        
        # Check if the user wants to update preferences
        if user_input.lower().startswith("set preference:"):
            try:
                _, pref = user_input.split(":", 1)
                key, value = pref.strip().split(":", 1)
                user_preference = {key.strip(): value.strip()}
                await self.memory_manager.update_long_term("user_preferences", user_preference)
                self.log.info(f"Updated user preference: {user_preference}")
            except ValueError:
                self.log.warning("Invalid preference format. Use 'set preference:key:value'")

        # Optionally access long-term memory
        facts = await self.memory_manager.get_long_term("facts")
        user_preferences = await self.memory_manager.get_long_term("user_preferences")
        self.log.debug(f"Current facts: {facts}")
        self.log.debug(f"Current user preferences: {user_preferences}")

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

            # Extract and store important facts
            facts = self._extract_facts(response)
            for fact in facts:
                await self.memory_manager.update_long_term("facts", fact)
                self.log.info(f"Added new fact to long-term memory: {fact}")

            return {"response": response}
        except Exception as e:
            error_message = f"Error during AI task execution: {str(e)}"
            self.log.error(error_message)
            raise ActorExecutionError(error_message, actor_name=self.name)  # noqa: B904

    async def _build_context(
        self, input_data: Dict[str, Any], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        short_term = await self.memory_manager.get_short_term("context")
        facts = await self.memory_manager.get_long_term("facts")
        user_preferences = await self.memory_manager.get_long_term("user_preferences")
        return {
            "input": input_data if isinstance(input_data, str) else str(input_data),
            "state": state,
            "short_term_memory": short_term,
            "long_term_facts": facts,
            "user_preferences": user_preferences,
        }

    def _extract_facts(self, response: str) -> List[str]:
        # This is a simple implementation. You might want to use more sophisticated NLP techniques
        # or integrate with your AI model to extract important facts.
        sentences = response.split('.')
        facts = [s.strip() for s in sentences if len(s.split()) > 5 and not s.strip().endswith('?')]
        return facts[:3]  # Limit to 3 facts per response to avoid overwhelming the memory
