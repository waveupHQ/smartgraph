# smartgraph/visualizer.py

from typing import Dict, List

from .core import Pipeline, ReactiveComponent, ReactiveSmartGraph


class GraphVisualizer:
    def __init__(self, graph: ReactiveSmartGraph):
        self.graph = graph

    def generate_mermaid_code(self) -> str:
        mermaid_code = "```mermaid\ngraph TD\n"

        # Add pipelines and their components
        for pipeline_name, pipeline in self.graph.pipelines.items():
            mermaid_code += f"subgraph {pipeline_name}\n"
            mermaid_code += self._generate_pipeline_components(pipeline)
            mermaid_code += "end\n"

        # Add connections between components
        mermaid_code += self._generate_connections()

        mermaid_code += "```\n"
        return mermaid_code

    def _generate_pipeline_components(self, pipeline: Pipeline) -> str:
        component_code = ""
        components = list(pipeline.components.values())
        for i, component in enumerate(components):
            component_id = f"{pipeline.name}_{component.name}"
            component_code += f"{component_id}[{component.name}]\n"
            if i > 0:
                prev_component_id = f"{pipeline.name}_{components[i-1].name}"
                component_code += f"{prev_component_id} --> {component_id}\n"
        return component_code

    def _generate_connections(self) -> str:
        connection_code = ""
        for source_pipeline, connections in self.graph.connections.items():
            for source_component, targets in connections.items():
                source_id = f"{source_pipeline}_{source_component}"
                for target in targets:
                    target_id = f"{target['target_pipeline']}_{target['target_component']}"
                    connection_code += f"{source_id} --> {target_id}\n"
        return connection_code

    def save_mermaid_code(self, filename: str):
        with open(filename, "w") as f:
            f.write(self.generate_mermaid_code())
