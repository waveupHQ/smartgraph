# smartgraph/assistant_conversation.py

import json
from typing import Any, Dict, List, Optional

import litellm
from litellm.utils import trim_messages
from reactivex import Observable
from reactivex import operators as ops
from reactivex.subject import Subject

from .component import ReactiveAIComponent
from .logging import SmartGraphLogger

logger = SmartGraphLogger.get_logger()

MAX_TOKENS = 4000


class ReactiveAssistantConversation(ReactiveAIComponent):
    def __init__(
        self,
        name: str = "AI Assistant",
        tools: Optional[List[Dict[str, Any]]] = None,
        model: str = "gpt-4o-mini",
        api_key: Optional[str] = None,
        tool_choice: str = "auto",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        frequency_penalty: Optional[float] = None,
        presence_penalty: Optional[float] = None,
    ):
        super().__init__(name)
        self.tools = tools or []
        self.model = model
        self.api_key = api_key
        self.tool_choice = tool_choice
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.top_p = top_p
        self.frequency_penalty = frequency_penalty
        self.presence_penalty = presence_penalty

        self.messages = self.create_state("messages", [])
        self.context = self.create_state("context", {})
        self.available_functions = {}

    def add_function(self, function_name: str, function):
        self.available_functions[function_name] = function

    async def process(self, input_data: str) -> str:
        messages = self.messages.value + [{"role": "user", "content": input_data}]
        context = self.context.value
        logger.info(f"Processing with context: {context}")

        try:
            response = await self._generate_response(messages, context)
            self.update_state("messages", messages + [{"role": "assistant", "content": response}])
            return response
        except Exception as e:
            logger.error(f"Error during LLM interaction: {str(e)}")
            return f"I'm sorry, but an error occurred: {str(e)}"

    async def _generate_response(
        self, messages: List[Dict[str, str]], context: Dict[str, Any]
    ) -> str:
        if context:
            context_message = {"role": "system", "content": self._format_context(context)}
            messages = [context_message] + messages

        trimmed_messages = trim_messages(messages, self.model, max_tokens=MAX_TOKENS)

        completion_params = {
            "model": self.model,
            "messages": trimmed_messages,
            "api_key": self.api_key,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
            "frequency_penalty": self.frequency_penalty,
            "presence_penalty": self.presence_penalty,
        }

        if self.tools:
            completion_params["tools"] = self.tools
            completion_params["tool_choice"] = self.tool_choice

        response = await litellm.acompletion(**completion_params)
        response_message = response.choices[0].message

        if "tool_calls" in response_message:
            tool_calls = response_message["tool_calls"]
            for tool_call in tool_calls:
                function_name = tool_call["function"]["name"]
                function_to_call = self.available_functions.get(function_name)
                if function_to_call:
                    function_args = json.loads(tool_call["function"]["arguments"])
                    function_response = await function_to_call(**function_args)
                    messages.append(
                        {
                            "tool_call_id": tool_call["id"],
                            "role": "tool",
                            "name": function_name,
                            "content": function_response,
                        }
                    )

            # Generate a final response after tool calls
            final_response = await litellm.acompletion(
                model=self.model,
                messages=trim_messages(messages, self.model, max_tokens=MAX_TOKENS),
                api_key=self.api_key,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                top_p=self.top_p,
                frequency_penalty=self.frequency_penalty,
                presence_penalty=self.presence_penalty,
            )
            return final_response.choices[0].message["content"]

        return response_message["content"]

    def _format_context(self, context: Dict[str, Any]) -> str:
        formatted_context = "You are an AI assistant with the following context:\n"
        for key, value in context.items():
            formatted_context += f"- {key.capitalize()}: {value}\n"
        formatted_context += "\nUse this context to inform your responses when appropriate."
        return formatted_context.strip()

    def reset_conversation(self):
        self.update_state("messages", [])

    def update_context(self, new_context: Dict[str, Any]):
        current_context = self.context.value
        current_context.update(new_context)
        self.update_state("context", current_context)
        logger.info(f"Context updated: {current_context}")
