import asyncio
from typing import Any, Dict

import litellm
from reactivex import Observable
from reactivex.subject import Subject

from ..core import ReactiveComponent
from ..logging import SmartGraphLogger


class CompletionComponent(ReactiveComponent):
    def __init__(self, name: str, model: str, **kwargs):
        super().__init__(name)
        self.model = model
        self.kwargs = kwargs
        self.logger = SmartGraphLogger.get_logger()

    def process(self, input_data: Dict[str, Any]) -> Observable:
        subject = Subject()

        async def run_completion():
            try:
                messages = [{"role": "user", "content": input_data["message"]}]
                self.logger.info(f"Sending request to {self.model} with message: {messages}")

                response = await litellm.acompletion(
                    model=self.model, messages=messages, **self.kwargs
                )

                if self.kwargs.get("stream", False):
                    async for chunk in response:
                        if chunk and chunk.choices and chunk.choices[0].delta.content:
                            subject.on_next({"ai_response": chunk.choices[0].delta.content})
                else:
                    if response and response.choices and response.choices[0].message:
                        subject.on_next({"ai_response": response.choices[0].message.content})
                    else:
                        subject.on_next({"ai_response": "No response generated"})

                subject.on_completed()
            except Exception as e:
                self.logger.error(f"Error in CompletionComponent: {str(e)}")
                subject.on_error(e)

        asyncio.create_task(run_completion())
        return subject
