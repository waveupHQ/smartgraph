# smartgraph/components/processing.py

import asyncio
from typing import Any, Callable, Dict, List

from ..core import ReactiveComponent


class AggregatorComponent(ReactiveComponent):
    async def process(self, input_data: List[Any]) -> Any:
        await asyncio.sleep(0.1)
        return f"Aggregated result: {' AND '.join(str(item) for item in input_data)}"


class FilterComponent(ReactiveComponent):
    def __init__(self, name: str, condition: Callable[[Any], bool]):
        super().__init__(name)
        self.condition = condition

    async def process(self, input_data: Any) -> Any:
        await asyncio.sleep(0.1)
        if self.condition(input_data):
            return input_data
        return None


class TransformerComponent(ReactiveComponent):
    def __init__(self, name: str, transform_func: Callable[[Any], Any]):
        super().__init__(name)
        self.transform_func = transform_func

    async def process(self, input_data: Any) -> Any:
        await asyncio.sleep(0.1)
        return self.transform_func(input_data)


class BranchingComponent(ReactiveComponent):
    def __init__(self, name: str, condition: Callable[[Any], bool]):
        super().__init__(name)
        self.condition = condition

    async def process(self, input_data: Any) -> Dict[str, Any]:
        await asyncio.sleep(0.1)
        if self.condition(input_data):
            return {"true_branch": input_data}
        else:
            return {"false_branch": input_data}


class AsyncAPIComponent(ReactiveComponent):
    def __init__(self, name: str, api_call: Callable[[Any], Any]):
        super().__init__(name)
        self.api_call = api_call

    async def process(self, input_data: Any) -> Any:
        return await self.api_call(input_data)


class RetryComponent(ReactiveComponent):
    def __init__(
        self, name: str, max_retries: int, retry_delay: float, component: ReactiveComponent
    ):
        super().__init__(name)
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.component = component

    async def process(self, input_data: Any) -> Any:
        for attempt in range(self.max_retries):
            try:
                return await self.component.process(input_data)
            except Exception:
                if attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(self.retry_delay)


class CacheComponent(ReactiveComponent):
    def __init__(self, name: str, component: ReactiveComponent, cache_size: int = 100):
        super().__init__(name)
        self.component = component
        self.cache = {}
        self.cache_size = cache_size

    async def process(self, input_data: Any) -> Any:
        if input_data in self.cache:
            return self.cache[input_data]

        result = await self.component.process(input_data)

        if len(self.cache) >= self.cache_size:
            self.cache.pop(next(iter(self.cache)))

        self.cache[input_data] = result
        return result


class ValidationComponent(ReactiveComponent):
    def __init__(self, name: str, schema: Dict[str, Any]):
        super().__init__(name)
        self.schema = schema

    async def process(self, input_data: Any) -> Any:
        # This is a very basic validation. In a real-world scenario,
        # you might want to use a library like Pydantic for more robust validation.
        for key, type_info in self.schema.items():
            if key not in input_data:
                raise ValueError(f"Missing required field: {key}")
            if not isinstance(input_data[key], type_info):
                raise TypeError(
                    f"Invalid type for {key}. Expected {type_info}, got {type(input_data[key])}"
                )
        return input_data
