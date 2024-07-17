import json
from typing import Any, Dict, List, Optional, Union

import litellm
from litellm.utils import trim_messages

from smartgraph.logging import SmartGraphLogger

logger = SmartGraphLogger.get_logger()

MAX_TOKENS = 4000


class AssistantConversation:
    def __init__(
        self,
        name: str = "AI Assistant",
        tools: Optional[List[Dict[str, Any]]] = None,
        model: str = "gpt-3.5-turbo-1106",
        api_key: Optional[str] = None,
        tool_choice: Union[str, Dict[str, Any]] = "auto",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        frequency_penalty: Optional[float] = None,
        presence_penalty: Optional[float] = None,
    ):
        self.name = name
        self.tools = tools or []
        self.model = model
        self.api_key = api_key
        self.tool_choice = tool_choice
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.top_p = top_p
        self.frequency_penalty = frequency_penalty
        self.presence_penalty = presence_penalty
        self.messages = []
        self.available_functions = {}

    def add_function(self, function_name: str, function):
        self.available_functions[function_name] = function

    async def run(self, prompt: str) -> str:
        self.messages.append({"role": "user", "content": prompt})

        try:
            trimmed_messages = trim_messages(self.messages, self.model, max_tokens=MAX_TOKENS)

            response = litellm.completion(
                model=self.model,
                messages=trimmed_messages,
                tools=self.tools,
                tool_choice=self.tool_choice,
                api_key=self.api_key,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                top_p=self.top_p,
                frequency_penalty=self.frequency_penalty,
                presence_penalty=self.presence_penalty,
            )

            response_message = response.choices[0].message
            self.messages.append(response_message)

            tool_calls = response_message.get("tool_calls", [])

            if tool_calls:
                for tool_call in tool_calls:
                    function_name = tool_call["function"]["name"]
                    function_to_call = self.available_functions.get(function_name)
                    if function_to_call:
                        function_args = json.loads(tool_call["function"]["arguments"])
                        function_response = function_to_call(**function_args)
                        self.messages.append(
                            {
                                "tool_call_id": tool_call["id"],
                                "role": "tool",
                                "name": function_name,
                                "content": function_response,
                            }
                        )

                trimmed_messages = trim_messages(self.messages, self.model, max_tokens=MAX_TOKENS)

                final_response = litellm.completion(
                    model=self.model,
                    messages=trimmed_messages,
                    api_key=self.api_key,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                    top_p=self.top_p,
                    frequency_penalty=self.frequency_penalty,
                    presence_penalty=self.presence_penalty,
                )
                final_content = final_response.choices[0].message["content"]
                self.messages.append({"role": "assistant", "content": final_content})
                return final_content

            return response_message["content"]

        except Exception as e:
            logger.error(f"Error during LLM interaction: {str(e)}")
            return f"I'm sorry, but an error occurred: {str(e)}"

    def reset_conversation(self):
        self.messages = []
