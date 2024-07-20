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
        debug_mode: bool = False
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
        self.debug_mode = debug_mode

        self.messages = self.create_state("messages", [])
        self.context = self.create_state("context", {})
        self.available_functions = {}

    def add_function(self, function_name: str, function):
        self.available_functions[function_name] = function

    async def process(self, input_data: str) -> str:
        messages = self.messages.value + [{"role": "user", "content": input_data}]
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

    async def _generate_response(self, messages: List[Dict[str, str]], context: Dict[str, Any]) -> Optional[str]:
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

            if self.tools:
                completion_params["tools"] = self.tools
                completion_params["tool_choice"] = self.tool_choice

            if self.debug_mode:
                logger.debug(f"Calling LLM with params: {completion_params}")
            response = await litellm.acompletion(**completion_params)
            if self.debug_mode:
                logger.debug(f"Received response from LLM: {response}")

            if not response.choices:
                logger.error("No choices in LLM response")
                return "I'm sorry, but I couldn't generate a response. Please try again."

            response_message = response.choices[0].message

            if response_message.get("tool_calls"):
                tool_calls = response_message["tool_calls"]
                tool_call_messages = []
                for tool_call in tool_calls:
                    function_name = tool_call["function"]["name"]
                    function_to_call = self.available_functions.get(function_name)
                    if function_to_call:
                        function_args = json.loads(tool_call["function"]["arguments"])
                        if self.debug_mode:
                            logger.debug(f"Calling function {function_name} with args: {function_args}")
                        function_response = await function_to_call(**function_args)
                        if self.debug_mode:
                            logger.debug(f"Function {function_name} response: {function_response}")
                        tool_call_messages.extend([
                            {
                                "role": "assistant",
                                "content": None,
                                "tool_calls": [tool_call]
                            },
                            {
                                "role": "tool",
                                "content": function_response,
                                "tool_call_id": tool_call["id"]
                            }
                        ])

                messages.extend(tool_call_messages)

                if self.debug_mode:
                    logger.debug("Generating final response after tool calls")
                final_response = await litellm.acompletion(
                    model=self.model,
                    messages=trim_messages(messages, self.model),
                    api_key=self.api_key,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                    top_p=self.top_p,
                    frequency_penalty=self.frequency_penalty,
                    presence_penalty=self.presence_penalty,
                )
                if self.debug_mode:
                    logger.debug(f"Final response: {final_response}")
                return final_response.choices[0].message["content"]

            return response_message.get("content", "I'm sorry, but I couldn't generate a response. Please try again.")
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

    # Additional methods from ReactiveAIComponent can be overridden or added here if needed
