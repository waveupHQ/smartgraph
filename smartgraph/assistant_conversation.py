# smartgraph/assistant_conversation.py

import json
from typing import Any, Dict, List, Optional

import litellm
from litellm.utils import get_supported_openai_params, trim_messages
from reactivex import Observable
from reactivex import operators as ops
from reactivex.subject import Subject

from .core import ReactiveComponent
from .logging import SmartGraphLogger
from .tools.base_toolkit import Toolkit

logger = SmartGraphLogger.get_logger()

MAX_TOKENS = 4000


class ReactiveAssistantConversation(ReactiveComponent):
    def __init__(
        self,
        name: str = "AI Assistant",
        toolkits: Optional[List[Toolkit]] = None,
        model: str = "gpt-4o-mini",
        api_key: Optional[str] = None,
        tool_choice: str = "auto",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        frequency_penalty: Optional[float] = None,
        presence_penalty: Optional[float] = None,
        debug_mode: bool = False,
        json_mode: bool = False,
        response_schema: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(name)
        self.toolkits = toolkits or []
        self.model = model
        self.api_key = api_key
        self.tool_choice = tool_choice
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.top_p = top_p
        self.frequency_penalty = frequency_penalty
        self.presence_penalty = presence_penalty
        self.debug_mode = debug_mode
        self.json_mode = json_mode
        self.response_schema = response_schema

        self.messages = self.create_state("messages", [])
        self.context = self.create_state("context", {})
        self.available_functions = self._gather_functions()

        # Check if the model supports function calling
        self.supports_function_calling = litellm.supports_function_calling(self.model)
        if not self.supports_function_calling:
            litellm.add_function_to_prompt = True
            logger.warning(
                f"Model {self.model} does not support function calling. Functions will be added to the prompt."
            )

        # Check if the model supports response_format
        self.supports_response_format = "response_format" in get_supported_openai_params(
            model=self.model
        )

    def _gather_functions(self) -> Dict[str, Any]:
        functions = {}
        for toolkit in self.toolkits:
            functions.update(toolkit.functions)
        return functions

    def add_toolkit(self, toolkit: Toolkit):
        self.toolkits.append(toolkit)
        self.available_functions.update(toolkit.functions)

    async def process(self, input_data: Any) -> str:
        if isinstance(input_data, dict):
            input_message = {"role": "user", "content": json.dumps(input_data)}
        else:
            input_message = {"role": "user", "content": str(input_data)}

        messages = self.messages.value + [input_message]
        context = self.context.value
        if self.debug_mode:
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
    ) -> Optional[str]:
        try:
            if self.debug_mode:
                logger.debug(f"Generating response with messages: {messages}")
                logger.debug(f"Context: {context}")

            if context:
                context_message = {"role": "system", "content": json.dumps(context)}
                messages = [context_message] + messages

            trimmed_messages = trim_messages(messages, self.model)

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

            if self.json_mode and self.supports_response_format:
                completion_params["response_format"] = {"type": "json_object"}
                if self.response_schema:
                    completion_params["response_format"]["response_schema"] = self.response_schema
                    completion_params["response_format"]["enforce_validation"] = True

            tools = [schema for toolkit in self.toolkits for schema in toolkit.schemas]
            if tools:
                if self.supports_function_calling:
                    completion_params["tools"] = tools
                    completion_params["tool_choice"] = self.tool_choice
                else:
                    completion_params["functions"] = tools

            if self.debug_mode:
                logger.debug(f"Calling LLM with params: {completion_params}")
            response = await litellm.acompletion(**completion_params)
            if self.debug_mode:
                logger.debug(f"Received response from LLM: {response}")

            if not response.choices:
                logger.error("No choices in LLM response")
                return "I'm sorry, but I couldn't generate a response. Please try again."

            response_message = response.choices[0].message

            if response_message.get("tool_calls") or response_message.get("function_call"):
                tool_calls = response_message.get("tool_calls") or [
                    response_message.get("function_call")
                ]
                tool_call_messages = []
                for tool_call in tool_calls:
                    function_name = tool_call["function"]["name"]
                    function_to_call = self.available_functions.get(function_name)
                    if function_to_call:
                        function_args = json.loads(tool_call["function"]["arguments"])
                        if self.debug_mode:
                            logger.debug(
                                f"Calling function {function_name} with args: {function_args}"
                            )
                        function_response = await function_to_call(**function_args)
                        if self.debug_mode:
                            logger.debug(f"Function {function_name} response: {function_response}")
                        tool_call_messages.extend(
                            [
                                {
                                    "role": "assistant",
                                    "content": None,
                                    "tool_calls": [tool_call]
                                    if self.supports_function_calling
                                    else None,
                                    "function_call": None
                                    if self.supports_function_calling
                                    else tool_call,
                                },
                                {
                                    "role": "tool"
                                    if self.supports_function_calling
                                    else "function",
                                    "content": function_response,
                                    "tool_call_id": tool_call.get("id"),
                                },
                            ]
                        )

                messages.extend(tool_call_messages)

                if self.debug_mode:
                    logger.debug("Generating final response after tool calls")
                final_response = await litellm.acompletion(**completion_params)
                if self.debug_mode:
                    logger.debug(f"Final response: {final_response}")
                return final_response.choices[0].message["content"]

            return response_message.get(
                "content", "I'm sorry, but I couldn't generate a response. Please try again."
            )
        except Exception as e:
            logger.error(f"Error in _generate_response: {str(e)}", exc_info=True)
            return "I'm sorry, but an error occurred while processing your request. Please try again later."

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
        if self.debug_mode:
            logger.info(f"Context updated: {current_context}")
