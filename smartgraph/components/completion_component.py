import asyncio

import litellm

from ..core import ReactiveComponent
from ..logging import SmartGraphLogger

logger = SmartGraphLogger.get_logger()


class CompletionComponent(ReactiveComponent):
    def __init__(self, name: str, model: str, **kwargs):
        super().__init__(name)
        self.model = model
        self.kwargs = kwargs

    async def process(self, input_data: dict) -> dict:
        logger.info(f"CompletionComponent received: {input_data}")
        try:
            # Check for 'content' key (from TextInputHandler) or 'message' key
            content = input_data.get("content") or input_data.get("message")
            if not content:
                raise ValueError("Input data must contain either a 'content' or 'message' key")

            messages = [{"role": "user", "content": content}]
            logger.info(f"Sending request to {self.model} with messages: {messages}")

            response = await litellm.acompletion(model=self.model, messages=messages, **self.kwargs)

            logger.info(f"Received response from API: {response}")

            if response and response.choices and response.choices[0].message:
                result = {"ai_response": response.choices[0].message.content}
                logger.info(f"CompletionComponent processing: {result}")
                return result
            else:
                logger.warning("Received empty or invalid response from API")
                return {"ai_response": "No valid response received"}
        except Exception as e:
            logger.error(f"Error in CompletionComponent: {str(e)}", exc_info=True)
            return {"error": str(e)}
