# smartgraph/component.py

import logging
from typing import Any, Dict, Optional

from reactivex import Observable, Subject
from reactivex import operators as ops
from reactivex.subject import BehaviorSubject

from .logging import SmartGraphLogger

logger = SmartGraphLogger.get_logger()


class ReactiveAIComponent:
    def __init__(self, name: str):
        self.name = name
        self._states: Dict[str, BehaviorSubject] = {}
        self.input: Subject = Subject()
        self.output: Subject = Subject()

        # Set up the processing pipeline
        self.input.subscribe(
            on_next=self._process_input,
            on_error=lambda e: logger.error(f"{self.name} encountered an error: {e}"),
        )

    async def _process_input(self, input_data: Any):
        logger.debug(f"{self.name} received input: {input_data}")
        try:
            result = await self.process(input_data)
            logger.debug(f"{self.name} processed input. Result: {result}")
            self.output.on_next(result)
        except Exception as e:
            logger.error(f"{self.name} failed to process input: {e}")
            self.output.on_error(e)

    def create_state(self, key: str, initial_value: Any) -> BehaviorSubject:
        """Create a new state Observable or return an existing one."""
        if key not in self._states:
            self._states[key] = BehaviorSubject(initial_value)
        return self._states[key]

    def get_state(self, key: str) -> Optional[BehaviorSubject]:
        """Get an existing state Observable."""
        return self._states.get(key)

    def update_state(self, key: str, value: Any) -> None:
        """Update the value of a state Observable."""
        if key in self._states:
            self._states[key].on_next(value)

    def map(self, observable: Observable, mapper: callable) -> Observable:
        """Apply a map operation to an Observable."""
        return observable.pipe(ops.map(mapper))

    def flat_map(self, observable: Observable, mapper: callable) -> Observable:
        """Apply a flat_map operation to an Observable."""
        return observable.pipe(ops.flat_map(mapper))

    def filter(self, observable: Observable, predicate: callable) -> Observable:
        """Apply a filter operation to an Observable."""
        return observable.pipe(ops.filter(predicate))

    async def process(self, input_data: Any) -> Any:
        """Process input data and produce output.

        This method should be overridden by subclasses.
        """
        raise NotImplementedError("Subclasses must implement process method")

    def run(self) -> None:
        """Main execution method for the component.

        Sets up the data flow from input to output.
        """
        self.input.pipe(ops.flat_map(lambda x: Observable.from_async(self.process(x)))).subscribe(
            self.output
        )
