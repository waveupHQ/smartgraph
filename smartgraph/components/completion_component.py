import asyncio
from typing import Dict, List, Optional

import litellm
from litellm.utils import trim_messages

from ..core import ReactiveComponent
from ..logging import SmartGraphLogger

logger = SmartGraphLogger.get_logger()


class CompletionComponent(ReactiveComponent):
    def __init__(
        self,
        name: str,
        model: str,
        system_context: str = "",
        max_tokens: Optional[int] = None,
        **kwargs,
    ):
        super().__init__(name)
        self.model = model
        self.system_context = system_context
        self.max_tokens = max_tokens or 5000
        self.kwargs = kwargs
        self.conversation_history: List[Dict[str, str]] = []

    async def process(self, input_data: dict) -> dict:
        logger.info(f"CompletionComponent received: {input_data}")
        try:
            content = input_data.get("content") or input_data.get("message")
            if not content:
                raise ValueError("Input data must contain either a 'content' or 'message' key")

            messages = self._prepare_messages(content)
            trimmed_messages = trim_messages(messages, self.model, self.max_tokens)

            response = await litellm.acompletion(
                model=self.model, messages=trimmed_messages, **self.kwargs
            )

            if response and response.choices and response.choices[0].message:
                result = {"ai_response": response.choices[0].message.content}
                self.conversation_history.append({"role": "user", "content": content})
                self.conversation_history.append(
                    {"role": "assistant", "content": result["ai_response"]}
                )
                return result
            else:
                return {"error": "No valid response received"}
        except Exception as e:
            logger.error(f"Error in CompletionComponent: {str(e)}", exc_info=True)
            return {"error": str(e)}

    def _prepare_messages(self, new_content: str) -> List[Dict[str, str]]:
        messages = []
        if self.system_context:
            messages.append({"role": "system", "content": self.system_context})
        messages.extend(self.conversation_history)
        messages.append({"role": "user", "content": new_content})
        return messages

    def set_system_context(self, context: str):
        self.system_context = context

    def clear_conversation_history(self):
        self.conversation_history.clear()

    def set_max_tokens(self, max_tokens: int):
        self.max_tokens = max_tokens

    def get_conversation_history(self) -> List[Dict[str, str]]:
        return self.conversation_history
