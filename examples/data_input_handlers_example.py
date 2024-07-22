# examples/data_input_handlers_example.py

import asyncio
import csv
import json
import xml.etree.ElementTree as ET
from io import BytesIO, StringIO

import pandas as pd
import pyarrow.parquet as pq
import yaml

from smartgraph import ReactiveAssistantConversation, ReactiveEdge, ReactiveNode, ReactiveSmartGraph
from smartgraph.components.human_in_the_loop import (
    BasicApprovalComponent,
    CorrectionRefinementComponent,
)
from smartgraph.components.input_handlers import (
    CommandLineInputHandler,
    CSVInputHandler,
    ImageUploadHandler,
    JSONInputHandler,
    ParquetInputHandler,
    StructuredDataDetector,
    TextInputHandler,
    XMLInputHandler,
    YAMLInputHandler,
)
from smartgraph.tools.duckduckgo_toolkit import DuckDuckGoToolkit


async def main():
    graph = ReactiveSmartGraph()

    # Create components
    text_input = TextInputHandler("TextInput")
    image_input = ImageUploadHandler("ImageInput")
    cli_input = CommandLineInputHandler("CLIInput")
    json_input = JSONInputHandler("JSONInput")
    xml_input = XMLInputHandler("XMLInput")
    csv_input = CSVInputHandler("CSVInput")
    yaml_input = YAMLInputHandler("YAMLInput")
    parquet_input = ParquetInputHandler("ParquetInput")
    structured_data_detector = StructuredDataDetector("StructuredDataDetector")
    approval = BasicApprovalComponent("ApprovalComponent")
    correction = CorrectionRefinementComponent("CorrectionComponent")

    duckduckgo_toolkit = DuckDuckGoToolkit(max_results=3)
    assistant = ReactiveAssistantConversation(
        name="Interactive Assistant",
        toolkits=[duckduckgo_toolkit],
        model="gpt-4-0613",
        api_key="your-api-key-here",
    )

    # Create nodes
    text_node = ReactiveNode("text_input", text_input)
    image_node = ReactiveNode("image_input", image_input)
    cli_node = ReactiveNode("cli_input", cli_input)
    json_node = ReactiveNode("json_input", json_input)
    xml_node = ReactiveNode("xml_input", xml_input)
    csv_node = ReactiveNode("csv_input", csv_input)
    yaml_node = ReactiveNode("yaml_input", yaml_input)
    parquet_node = ReactiveNode("parquet_input", parquet_input)
    detector_node = ReactiveNode("structured_data_detector", structured_data_detector)
    approval_node = ReactiveNode("approval", approval)
    correction_node = ReactiveNode("correction", correction)
    assistant_node = ReactiveNode("assistant", assistant)

    # Add nodes to the graph
    for node in [
        text_node,
        image_node,
        cli_node,
        json_node,
        xml_node,
        csv_node,
        yaml_node,
        parquet_node,
        detector_node,
        approval_node,
        correction_node,
        assistant_node,
    ]:
        graph.add_node(node)

    # Add edges
    for node in [
        text_node,
        image_node,
        cli_node,
        json_node,
        xml_node,
        csv_node,
        yaml_node,
        parquet_node,
        detector_node,
    ]:
        graph.add_edge(ReactiveEdge(node.id, "assistant"))
    graph.add_edge(ReactiveEdge("assistant", "approval"))
    graph.add_edge(ReactiveEdge("assistant", "correction"))

    # Simulated workflow
    # Unstructured data inputs
    text_result = await graph.execute(
        "text_input", "Analyze the impact of artificial intelligence on job markets."
    )
    print("Text input result:", text_result)

    image_result = await graph.execute(
        "image_input", {"filename": "ai_impact.jpg", "content": "base64_encoded_image_data"}
    )
    print("Image input result:", image_result)

    cli_result = await graph.execute("cli_input", "search AI job market trends")
    print("CLI input result:", cli_result)

    # Structured data inputs
    json_data = json.dumps({"ai_impact": {"job_creation": 500000, "job_displacement": 300000}})
    json_result = await graph.execute("json_input", json_data)
    print("JSON input result:", json_result)

    xml_data = """
    <ai_skills>
        <skill>machine_learning</skill>
        <skill>data_analysis</skill>
        <skill>natural_language_processing</skill>
    </ai_skills>
    """
    xml_result = await graph.execute("xml_input", xml_data)
    print("XML input result:", xml_result)

    csv_data = "skill,demand\nmachine_learning,high\ndata_analysis,medium\nnatural_language_processing,high"
    csv_result = await graph.execute("csv_input", csv_data)
    print("CSV input result:", csv_result)

    yaml_data = yaml.dump(
        {"ai_skills": ["machine_learning", "data_analysis", "natural_language_processing"]}
    )
    yaml_result = await graph.execute("yaml_input", yaml_data)
    print("YAML input result:", yaml_result)

    # Create a sample Parquet file
    df = pd.DataFrame(
        {
            "skill": ["machine_learning", "data_analysis", "natural_language_processing"],
            "demand": ["high", "medium", "high"],
        }
    )
    parquet_buffer = BytesIO()
    df.to_parquet(parquet_buffer)
    parquet_result = await graph.execute("parquet_input", parquet_buffer.getvalue())
    print("Parquet input result:", parquet_result)

    # Test the StructuredDataDetector
    detector_result = await graph.execute("structured_data_detector", json_data)
    print("Structured Data Detector result (JSON):", detector_result)

    detector_result = await graph.execute("structured_data_detector", xml_data)
    print("Structured Data Detector result (XML):", detector_result)

    # Assistant processing all inputs
    assistant_output = await graph.execute(
        "assistant", "Analyze the impact of AI on job markets based on all inputs"
    )

    # Approval workflow
    approval_result = await graph.execute("approval", assistant_output)
    approval.submit_human_input(True)  # Simulate human approval
    print("Approval result:", await approval_result)

    # Correction workflow
    correction_result = await graph.execute("correction", assistant_output)
    correction.submit_human_input(
        "Include more data on regional variations in AI job market impact"
    )  # Simulate human correction
    print("Correction result:", await correction_result)


if __name__ == "__main__":
    asyncio.run(main())
