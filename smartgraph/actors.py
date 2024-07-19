from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict

from .assistant_conversation import AssistantConversation
from .base import BaseActor, Task
from .exceptions import ActorExecutionError
from .logging import SmartGraphLogger
from .memory import MemoryManager

logger = SmartGraphLogger.get_logger()


class Actor(BaseModel, BaseActor):
    name: str
    memory_manager: Optional[MemoryManager] = None

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        BaseActor.__init__(self, self.name)

    def perform_task(
        self, task: Task, input_data: Dict[str, Any], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        raise NotImplementedError


class HumanActor(BaseActor):
    def __init__(self, name: str, memory_manager: Optional[MemoryManager] = None):
        super().__init__(name, memory_manager)

    async def perform_task(
        self, task: Task, input_data: Dict[str, Any], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        self.log.info(f"Task for {self.name}: {task.description}")
        self.log.debug(f"Input data: {input_data}")

        user_input = await asyncio.to_thread(input, "Enter your response: ")

        if self.memory_manager:
            await self.memory_manager.update_short_term("last_input", user_input)
            await self.memory_manager.update_conversation_history(user_input, is_user=True)

            if user_input.lower().startswith("set preference:"):
                try:
                    _, pref = user_input.split(":", 1)
                    key, value = pref.strip().split(":", 1)
                    user_preference = {key.strip(): value.strip()}
                    await self.memory_manager.update_long_term("user_preferences", user_preference)
                    self.log.info(f"Updated user preference: {user_preference}")
                except ValueError:
                    self.log.warning("Invalid preference format. Use 'set preference:key:value'")

        return {"response": user_input}


class AIActor(BaseActor):
    def __init__(
        self,
        name: str,
        assistant: Optional[AssistantConversation] = None,
        memory_manager: Optional[MemoryManager] = None,
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
            task.prompt.format(input=input_data.get("response", ""))
            if task.prompt
            else f"Task: {task.description}\nPlease provide a response."
        )

        try:
            response = await self.assistant.run(prompt, context)

            if response is None:
                self.log.warning("Received None response from assistant")
                return {"response": "I'm sorry, but I couldn't generate a response at this time."}

            self.log.info(f"AI response: {response}")

            if self.memory_manager:
                await self.memory_manager.update_short_term("last_response", response)
                await self.memory_manager.update_conversation_history(response, is_user=False)

                facts = self._extract_facts(response)
                for fact in facts:
                    await self.memory_manager.update_long_term("facts", fact)
                    self.log.info(f"Added new fact to long-term memory: {fact}")

            return {"response": response}
        except Exception as e:
            error_message = f"Error during AI task execution: {str(e)}"
            self.log.error(error_message)
            raise ActorExecutionError(error_message, actor_name=self.name)

    async def _build_context(
        self, input_data: Dict[str, Any], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        context = {
            "current_input": input_data.get("response", ""),
            "state": state,
        }

        if self.memory_manager:
            context["conversation_history"] = await self.memory_manager.get_conversation_history()
            context["facts"] = await self.memory_manager.get_long_term("facts")
            context["user_preferences"] = await self.memory_manager.get_long_term(
                "user_preferences"
            )

        return context

    def _extract_facts(self, response: str) -> List[str]:
        sentences = response.split(".")
        facts = [s.strip() for s in sentences if len(s.split()) > 5 and not s.strip().endswith("?")]
        return facts[:3]  # Limit to 3 facts per response
