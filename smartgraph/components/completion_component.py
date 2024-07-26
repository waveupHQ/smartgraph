# smartgraph/components/completion_component.py

import asyncio
import json
from typing import Any, AsyncGenerator, Dict, List, Optional, Union

import litellm
from litellm.utils import trim_messages

from ..core import ReactiveComponent
from ..logging import SmartGraphLogger
from ..tools.base_toolkit import Toolkit

logger = SmartGraphLogger.get_logger()


class CompletionComponent(ReactiveComponent):
    def __init__(
        self,
        name: str,
        model: str,
        system_context: str = "",
        max_tokens: Optional[int] = None,
        toolkits: Optional[List[Toolkit]] = None,
        stream: bool = False,
        **kwargs,
    ):
        super().__init__(name)
        self.model = model
        self.system_context = system_context
        self.max_tokens = max_tokens or 5000
        self.kwargs = kwargs
        self.conversation_history: List[Dict[str, str]] = []
        self.toolkits = toolkits or []
        self.stream = stream

    async def process(
        self, input_data: dict
    ) -> Union[Dict[str, Any], AsyncGenerator[Dict[str, Any], None]]:
        logger.info(f"CompletionComponent received: {input_data}")
        try:
            content = input_data.get("content") or input_data.get("message")
            if not content:
                raise ValueError("Input data must contain either a 'content' or 'message' key")

            messages = self._prepare_messages(content)
            trimmed_messages = trim_messages(messages, self.model, self.max_tokens)

            if self.stream:
                return self._stream_llm_call(trimmed_messages)
            else:
                response = await self._llm_call(trimmed_messages)
                return await self._handle_llm_response(response.choices[0].message, messages)
        except Exception as e:
            logger.error(f"Error in CompletionComponent: {str(e)}", exc_info=True)
            return {"error": str(e)}

    async def _llm_call(self, messages: List[Dict[str, str]]) -> Any:
        tools = [schema for toolkit in self.toolkits for schema in toolkit.schemas]

        completion_params = {
            "model": self.model,
            "messages": messages,
            "tools": tools if tools else None,
            "tool_choice": "auto" if tools else None,
            **self.kwargs,
        }

        return await litellm.acompletion(**completion_params)

    async def _stream_llm_call(
        self, messages: List[Dict[str, str]]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        tools = [schema for toolkit in self.toolkits for schema in toolkit.schemas]

        completion_params = {
            "model": self.model,
            "messages": messages,
            "tools": tools if tools else None,
            "tool_choice": "auto" if tools else None,
            "stream": True,
            **self.kwargs,
        }

        async for chunk in await litellm.acompletion(**completion_params):
            yield chunk

    async def _handle_llm_response(
        self, message: Dict[str, Any], messages: List[Dict[str, str]]
    ) -> Dict[str, str]:
        if message.get("tool_calls"):
            tool_calls = message["tool_calls"]
            messages.append({"role": "assistant", "content": None, "tool_calls": tool_calls})

            for tool_call in tool_calls:
                function_name = tool_call["function"]["name"]
                function_args = json.loads(tool_call["function"]["arguments"])
                tool_response = await self._execute_tool(function_name, function_args)
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "name": function_name,
                        "content": json.dumps(tool_response),
                    }
                )

            final_response = await self._llm_call(messages)
            return {"ai_response": final_response.choices[0].message["content"]}
        else:
            return {"ai_response": message["content"]}

    async def _execute_tool(self, function_name: str, function_args: Dict[str, Any]) -> Any:
        for toolkit in self.toolkits:
            if function_name in toolkit.functions:
                return await toolkit.functions[function_name](**function_args)
        raise ValueError(f"Tool {function_name} not found in any toolkit")

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

    def add_toolkit(self, toolkit: Toolkit):
        self.toolkits.append(toolkit)
