# smartgraph/core.py

import asyncio
from typing import Any, Dict, List, Optional

from reactivex import Observable
from reactivex import operators as ops
from reactivex.subject import BehaviorSubject, Subject

from .exceptions import CompilationError, ConfigurationError, ExecutionError
from .logging import SmartGraphLogger
from .utils import process_observable

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

    async def process(self, input_data: Any) -> Any:
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

    async def execute(self, input_data: Any) -> Any:
        logger.info(f"Executing pipeline {self.name} with input: {input_data}")
        current_data = input_data
        for component in self.components.values():
            try:
                current_data = await component.process(current_data)
            except Exception as e:
                logger.error(f"Error in component {component.name}: {str(e)}")
                raise
        logger.info(f"Pipeline {self.name} execution completed")
        return current_data


class ReactiveSmartGraph:
    def __init__(self):
        self.pipelines: Dict[str, Pipeline] = {}
        self.connections: Dict[str, Dict[str, List[Dict[str, str]]]] = {}
        self.is_compiled = False
        self.runtime_args: Dict[str, Any] = {}

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

    def compile(self, **runtime_args):
        logger.info("Starting graph compilation")
        self.runtime_args = runtime_args
        self._check_orphaned_components()
        self._check_cyclic_connections()
        self._check_unbounded_recursion()

        # Connect components within pipelines
        for pipeline in self.pipelines.values():
            components = list(pipeline.components.values())
            for i in range(len(components) - 1):
                components[i].output.subscribe(components[i + 1].input)

        # Connect components across pipelines
        for source_pipeline, connections in self.connections.items():
            for source_component, targets in connections.items():
                source = self.pipelines[source_pipeline].components[source_component]
                for target in targets:
                    target_component = self.pipelines[target["target_pipeline"]].components[
                        target["target_component"]
                    ]
                    source.output.subscribe(target_component.input)

        self.is_compiled = True
        logger.info("Graph compiled successfully")

    def _check_orphaned_components(self):
        all_components = set()
        pipeline_components = set()

        # Collect all components and components in pipelines
        for pipeline_name, pipeline in self.pipelines.items():
            for component_name in pipeline.components:
                all_components.add(f"{pipeline_name}.{component_name}")
                pipeline_components.add(f"{pipeline_name}.{component_name}")

        # Check for components in connections that are not in any pipeline
        for pipeline_name, connections in self.connections.items():
            for component_name, targets in connections.items():
                all_components.add(f"{pipeline_name}.{component_name}")
                for target in targets:
                    all_components.add(f"{target['target_pipeline']}.{target['target_component']}")

        # Identify orphaned components
        orphaned = all_components - pipeline_components
        if orphaned:
            raise CompilationError(f"Orphaned components detected: {orphaned}")

    def _check_cyclic_connections(self):
        def dfs(node, visited, rec_stack):
            visited.add(node)
            rec_stack.add(node)

            pipeline_name, component_name = node.split(".")
            if (
                pipeline_name in self.connections
                and component_name in self.connections[pipeline_name]
            ):
                for target in self.connections[pipeline_name][component_name]:
                    neighbor = f"{target['target_pipeline']}.{target['target_component']}"
                    if neighbor not in visited:
                        if dfs(neighbor, visited, rec_stack):
                            return True
                    elif neighbor in rec_stack:
                        return True

            rec_stack.remove(node)
            return False

        visited = set()
        rec_stack = set()

        for pipeline_name, pipeline in self.pipelines.items():
            for component_name in pipeline.components:
                node = f"{pipeline_name}.{component_name}"
                if node not in visited:
                    if dfs(node, visited, rec_stack):
                        raise CompilationError("Cyclic connections detected in the graph")

    def _check_unbounded_recursion(self):
        max_depth = self.runtime_args.get("max_depth", 100)
        for pipeline_name, pipeline in self.pipelines.items():
            for component_name in pipeline.components:
                stack = [(pipeline_name, component_name, 0)]
                while stack:
                    current_pipeline, current_component, depth = stack.pop()
                    if depth > max_depth:
                        raise CompilationError(
                            f"Potential unbounded recursion detected starting from {current_pipeline}.{current_component}"
                        )
                    if (
                        current_pipeline in self.connections
                        and current_component in self.connections[current_pipeline]
                    ):
                        for target in self.connections[current_pipeline][current_component]:
                            stack.append(
                                (target["target_pipeline"], target["target_component"], depth + 1)
                            )

    def execute(
        self, pipeline_name: str, input_data: Any, timeout: Optional[float] = None
    ) -> Observable:
        if not self.is_compiled:
            return Observable.throw(CompilationError("Graph must be compiled before execution"))

        if pipeline_name not in self.pipelines:
            return Observable.throw(ConfigurationError(f"Pipeline {pipeline_name} does not exist"))

        pipeline = self.pipelines[pipeline_name]

        def subscribe(observer, scheduler=None):
            async def process_pipeline():
                try:
                    current_data = input_data
                    for component in pipeline.components.values():
                        if asyncio.iscoroutinefunction(component.process):
                            current_data = await component.process(current_data)
                        else:
                            current_data = component.process(current_data)
                    observer.on_next(current_data)
                    observer.on_completed()
                except Exception as e:
                    observer.on_error(e)

            task = asyncio.create_task(process_pipeline())

            if timeout is not None:
                asyncio.create_task(self._cancel_after_timeout(task, timeout, observer))

        return Observable(subscribe)

    async def _cancel_after_timeout(self, task, timeout, observer):
        await asyncio.sleep(timeout)
        if not task.done():
            task.cancel()
            observer.on_error(TimeoutError(f"Execution timed out after {timeout} seconds"))

    async def execute_and_await(
        self, pipeline_name: str, input_data: Any, timeout: Optional[float] = None
    ) -> Any:
        observable = self.execute(pipeline_name, input_data, timeout)
        return await process_observable(observable)
