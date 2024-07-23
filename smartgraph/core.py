# smartgraph/core.py

import asyncio
from typing import Any, Dict, List, Optional

from reactivex import Observable
from reactivex.subject import BehaviorSubject, Subject

from .exceptions import ConfigurationError, ExecutionError
from .logging import SmartGraphLogger

logger = SmartGraphLogger.get_logger()


class ReactiveComponent:
    def __init__(self, name: str):
        self.name = name
        self._states: Dict[str, BehaviorSubject] = {}
        self.input: Subject = Subject()
        self.output: Subject = Subject()
        self.error: Subject = Subject()

        self.input.subscribe(self._process_input)

    def _process_input(self, input_data: Any):
        logger.debug(f"{self.name} received input: {input_data}")
        try:
            result = self.process(input_data)
            logger.debug(f"{self.name} processed input. Result: {result}")
            self.output.on_next(result)
        except Exception as e:
            logger.error(f"{self.name} failed to process input: {e}")
            self.error.on_next(e)

    def create_state(self, key: str, initial_value: Any) -> BehaviorSubject:
        if key not in self._states:
            self._states[key] = BehaviorSubject(initial_value)
        return self._states[key]

    def get_state(self, key: str) -> Optional[BehaviorSubject]:
        return self._states.get(key)

    def update_state(self, key: str, value: Any) -> None:
        if key in self._states:
            self._states[key].on_next(value)

    def process(self, input_data: Any) -> Any:
        raise NotImplementedError("Subclasses must implement process method")


class Pipeline:
    def __init__(self, name: str):
        self.name = name
        self.components: Dict[str, ReactiveComponent] = {}
        self.connections: Dict[str, List[str]] = {}
        self.input = Subject()
        self.output = Subject()
        self.error = Subject()

    def add_component(self, component: ReactiveComponent):
        if component.name in self.components:
            raise ConfigurationError(
                f"Component {component.name} already exists in pipeline {self.name}"
            )
        self.components[component.name] = component
        self.connections[component.name] = []
        logger.info(f"Added component {component.name} to pipeline {self.name}")

    def connect_components(self, source: str, target: str):
        if source not in self.components or target not in self.components:
            raise ConfigurationError(
                f"Invalid connection: {source} -> {target} in pipeline {self.name}"
            )
        self.connections[source].append(target)
        logger.info(f"Connected {source} to {target} in pipeline {self.name}")

    def compile(self):
        for source, targets in self.connections.items():
            source_component = self.components[source]
            for target in targets:
                target_component = self.components[target]
                source_component.output.subscribe(
                    target_component.input, lambda error: self.error.on_next(error)
                )

        first_component = next(iter(self.components.values()))
        self.input.subscribe(first_component.input)

        last_component = list(self.components.values())[-1]
        last_component.output.subscribe(self.output)

        logger.info(f"Compiled pipeline {self.name}")

    def execute(self, input_data: Any) -> Observable:
        result_subject = Subject()

        def on_next(x):
            result_subject.on_next(x)

        def on_error(error):
            result_subject.on_error(error)

        def on_completed():
            result_subject.on_completed()

        self.output.subscribe(on_next, on_error, on_completed)
        self.input.on_next(input_data)

        return result_subject


class ReactiveSmartGraph:
    def __init__(self):
        self.pipelines: Dict[str, Pipeline] = {}
        self.connections: Dict[str, Dict[str, List[Dict[str, str]]]] = {}

    def create_pipeline(self, name: str) -> Pipeline:
        if name in self.pipelines:
            raise ConfigurationError(f"Pipeline {name} already exists")
        pipeline = Pipeline(name)
        self.pipelines[name] = pipeline
        self.connections[name] = {}
        logger.info(f"Created pipeline {name}")
        return pipeline

    def connect_components(
        self,
        source_pipeline: str,
        source_component: str,
        target_pipeline: str,
        target_component: str,
    ):
        if source_pipeline not in self.pipelines or target_pipeline not in self.pipelines:
            raise ConfigurationError(
                f"Invalid pipeline connection: {source_pipeline} -> {target_pipeline}"
            )

        if source_pipeline not in self.connections:
            self.connections[source_pipeline] = {}

        if source_component not in self.connections[source_pipeline]:
            self.connections[source_pipeline][source_component] = []

        self.connections[source_pipeline][source_component].append(
            {"target_pipeline": target_pipeline, "target_component": target_component}
        )
        logger.info(
            f"Connected {source_pipeline}.{source_component} to {target_pipeline}.{target_component}"
        )

    def compile(self):
        for pipeline in self.pipelines.values():
            pipeline.compile()

        for source_pipeline, source_connections in self.connections.items():
            for source_component, targets in source_connections.items():
                source = self.pipelines[source_pipeline].components[source_component]
                for target in targets:
                    target_pipeline = self.pipelines[target["target_pipeline"]]
                    target_component = target_pipeline.components[target["target_component"]]
                    source.output.subscribe(
                        target_component.input,
                        lambda error: logger.error(
                            f"Error in connection {source_pipeline}.{source_component} -> {target['target_pipeline']}.{target['target_component']}: {error}"
                        ),
                    )

        logger.info("Compiled ReactiveSmartGraph")

    def execute(self, pipeline_name: str, input_data: Any) -> Observable:
        if pipeline_name not in self.pipelines:
            raise ConfigurationError(f"Pipeline {pipeline_name} does not exist")

        return self.pipelines[pipeline_name].execute(input_data)
