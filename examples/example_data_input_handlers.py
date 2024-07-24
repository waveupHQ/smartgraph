# example_data_input_handlers.py

import json
from io import StringIO

import pandas as pd
import yaml
from reactivex import operators as ops

from smartgraph.core import Pipeline, ReactiveComponent, ReactiveSmartGraph


class TextInputHandler(ReactiveComponent):
    def process(self, input_data: str) -> dict:
        result = {
            "type": "text",
            "content": input_data,
            "length": len(input_data),
            "word_count": len(input_data.split()),
        }
        print(f"TextInputHandler processed: {result}")
        return result


class JSONInputHandler(ReactiveComponent):
    def process(self, input_data: str) -> dict:
        result = {"type": "json", "parsed_data": json.loads(input_data)}
        print(f"JSONInputHandler processed: {result}")
        return result


class CSVInputHandler(ReactiveComponent):
    def process(self, input_data: str) -> dict:
        df = pd.read_csv(StringIO(input_data))
        result = {
            "type": "csv",
            "parsed_data": df.to_dict(orient="records"),
            "headers": df.columns.tolist(),
        }
        print(f"CSVInputHandler processed: {result}")
        return result


class YAMLInputHandler(ReactiveComponent):
    def process(self, input_data: str) -> dict:
        result = {"type": "yaml", "parsed_data": yaml.safe_load(input_data)}
        print(f"YAMLInputHandler processed: {result}")
        return result


class DataAggregator(ReactiveComponent):
    def __init__(self, name: str):
        super().__init__(name)
        self.create_state("all_data", [])

    def process(self, input_data: dict) -> dict:
        all_data = self.get_state("all_data").value
        all_data.append(input_data)
        self.update_state("all_data", all_data)
        result = {"aggregated_data": all_data}
        print(f"DataAggregator processed: {result}")
        return result


def main():
    # Initialize the ReactiveSmartGraph
    graph = ReactiveSmartGraph()

    # Create pipelines
    text_pipeline = graph.create_pipeline("TextPipeline")
    json_pipeline = graph.create_pipeline("JSONPipeline")
    csv_pipeline = graph.create_pipeline("CSVPipeline")
    yaml_pipeline = graph.create_pipeline("YAMLPipeline")
    aggregator_pipeline = graph.create_pipeline("AggregatorPipeline")

    # Create input handler components
    text_input = TextInputHandler("TextInput")
    json_input = JSONInputHandler("JSONInput")
    csv_input = CSVInputHandler("CSVInput")
    yaml_input = YAMLInputHandler("YAMLInput")
    data_aggregator = DataAggregator("DataAggregator")

    # Add components to pipelines
    text_pipeline.add_component(text_input)
    json_pipeline.add_component(json_input)
    csv_pipeline.add_component(csv_input)
    yaml_pipeline.add_component(yaml_input)
    aggregator_pipeline.add_component(data_aggregator)

    # Connect pipelines
    graph.connect_components("TextPipeline", "TextInput", "AggregatorPipeline", "DataAggregator")
    graph.connect_components("JSONPipeline", "JSONInput", "AggregatorPipeline", "DataAggregator")
    graph.connect_components("CSVPipeline", "CSVInput", "AggregatorPipeline", "DataAggregator")
    graph.connect_components("YAMLPipeline", "YAMLInput", "AggregatorPipeline", "DataAggregator")

    # Compile the graph
    graph.compile()

    # Prepare input data
    text_data = "Analyze the impact of artificial intelligence on job markets."
    json_data = json.dumps({"ai_impact": {"job_creation": 500000, "job_displacement": 300000}})
    csv_data = """skill,demand
machine_learning,high
data_analysis,medium
natural_language_processing,high"""
    yaml_data = yaml.dump(
        {"ai_skills": ["machine_learning", "data_analysis", "natural_language_processing"]}
    )

    # Process inputs
    print("Processing Text Data:")
    graph.execute("TextPipeline", text_data).subscribe(lambda x: print(f"Text Result: {x}"))

    print("\nProcessing JSON Data:")
    graph.execute("JSONPipeline", json_data).subscribe(lambda x: print(f"JSON Result: {x}"))

    print("\nProcessing CSV Data:")
    graph.execute("CSVPipeline", csv_data).subscribe(lambda x: print(f"CSV Result: {x}"))

    print("\nProcessing YAML Data:")
    graph.execute("YAMLPipeline", yaml_data).subscribe(lambda x: print(f"YAML Result: {x}"))

    print("\nGetting Aggregated Results:")
    graph.execute("AggregatorPipeline", None).subscribe(
        lambda x: print(f"Aggregated Result: {x}"),
        lambda e: print(f"Error: {e}"),
        lambda: print("Aggregation completed"),
    )


if __name__ == "__main__":
    main()
