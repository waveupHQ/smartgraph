import asyncio
from typing import Any, List

from .component import ReactiveAIComponent
from .logging import SmartGraphLogger

logger = SmartGraphLogger.get_logger()


class AggregatorComponent(ReactiveAIComponent):
    async def process(self, input_data: List[Any]) -> Any:
        logger.info(f"{self.name} aggregating: {input_data}")
        await asyncio.sleep(1)
        return f"Aggregated result: {' AND '.join(str(item) for item in input_data)}"