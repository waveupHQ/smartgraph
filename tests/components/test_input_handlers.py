# tests/test_data_input_handlers_example.py

import asyncio
import json
from io import BytesIO
from unittest.mock import AsyncMock, MagicMock, patch

import pandas as pd
import pytest
import yaml

from smartgraph import ReactiveSmartGraph
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


@pytest.fixture
def mock_graph():
    graph = ReactiveSmartGraph()
    graph.add_node = MagicMock()
    graph.add_edge = MagicMock()
    graph.execute = AsyncMock()
    return graph


@pytest.fixture
def mock_assistant():
    return AsyncMock()


@pytest.mark.asyncio
async def test_text_input_handler(mock_graph):
    text_input = TextInputHandler("TextInput")
    mock_graph.execute.return_value = {
        "type": "text",
        "content": "Analyze the impact of artificial intelligence on job markets.",
        "length": 61,
        "word_count": 9,
    }

    result = await mock_graph.execute(
        "text_input", "Analyze the impact of artificial intelligence on job markets."
    )
    assert result["type"] == "text"
    assert result["content"] == "Analyze the impact of artificial intelligence on job markets."
    assert result["length"] == 61
    assert result["word_count"] == 9


@pytest.mark.asyncio
async def test_image_upload_handler(mock_graph):
    image_input = ImageUploadHandler("ImageInput")
    mock_graph.execute.return_value = {
        "type": "image",
        "filename": "ai_impact.jpg",
        "content": "base64_encoded_image_data",
        "dimensions": "1024x768",
        "format": "jpeg",
    }

    result = await mock_graph.execute(
        "image_input", {"filename": "ai_impact.jpg", "content": "base64_encoded_image_data"}
    )
    assert result["type"] == "image"
    assert result["filename"] == "ai_impact.jpg"
    assert result["content"] == "base64_encoded_image_data"


@pytest.mark.asyncio
async def test_command_line_input_handler(mock_graph):
    cli_input = CommandLineInputHandler("CLIInput")
    mock_graph.execute.return_value = {
        "type": "command",
        "command": "git",
        "args": ["commit", "-m", "Initial AI job market analysis"],
        "full_input": "git commit -m 'Initial AI job market analysis'",
    }

    result = await mock_graph.execute("cli_input", "git commit -m 'Initial AI job market analysis'")
    assert result["type"] == "command"
    assert result["command"] == "git"
    assert result["args"] == ["commit", "-m", "Initial AI job market analysis"]


@pytest.mark.asyncio
async def test_json_input_handler(mock_graph):
    json_input = JSONInputHandler("JSONInput")
    input_data = json.dumps({"ai_impact": {"job_creation": 500000, "job_displacement": 300000}})
    mock_graph.execute.return_value = {
        "type": "json",
        "parsed_data": {"ai_impact": {"job_creation": 500000, "job_displacement": 300000}},
    }

    result = await mock_graph.execute("json_input", input_data)
    assert result["type"] == "json"
    assert result["parsed_data"]["ai_impact"]["job_creation"] == 500000


@pytest.mark.asyncio
async def test_xml_input_handler(mock_graph):
    xml_input = XMLInputHandler("XMLInput")
    input_data = """
    <ai_skills>
        <skill>machine_learning</skill>
        <skill>data_analysis</skill>
        <skill>natural_language_processing</skill>
    </ai_skills>
    """
    mock_graph.execute.return_value = {
        "type": "xml",
        "parsed_data": {
            "ai_skills": {
                "skill": ["machine_learning", "data_analysis", "natural_language_processing"]
            }
        },
    }

    result = await mock_graph.execute("xml_input", input_data)
    assert result["type"] == "xml"
    assert "machine_learning" in result["parsed_data"]["ai_skills"]["skill"]


@pytest.mark.asyncio
async def test_csv_input_handler(mock_graph):
    csv_input = CSVInputHandler("CSVInput")
    input_data = "skill,demand\nmachine_learning,high\ndata_analysis,medium\nnatural_language_processing,high"
    mock_graph.execute.return_value = {
        "type": "csv",
        "parsed_data": [
            {"skill": "machine_learning", "demand": "high"},
            {"skill": "data_analysis", "demand": "medium"},
            {"skill": "natural_language_processing", "demand": "high"},
        ],
        "headers": ["skill", "demand"],
    }

    result = await mock_graph.execute("csv_input", input_data)
    assert result["type"] == "csv"
    assert result["parsed_data"][0]["skill"] == "machine_learning"
    assert result["headers"] == ["skill", "demand"]


@pytest.mark.asyncio
async def test_yaml_input_handler(mock_graph):
    yaml_input = YAMLInputHandler("YAMLInput")
    input_data = yaml.dump(
        {"ai_skills": ["machine_learning", "data_analysis", "natural_language_processing"]}
    )
    mock_graph.execute.return_value = {
        "type": "yaml",
        "parsed_data": {
            "ai_skills": ["machine_learning", "data_analysis", "natural_language_processing"]
        },
    }

    result = await mock_graph.execute("yaml_input", input_data)
    assert result["type"] == "yaml"
    assert "machine_learning" in result["parsed_data"]["ai_skills"]


@pytest.mark.asyncio
async def test_parquet_input_handler(mock_graph):
    parquet_input = ParquetInputHandler("ParquetInput")
    df = pd.DataFrame(
        {
            "skill": ["machine_learning", "data_analysis", "natural_language_processing"],
            "demand": ["high", "medium", "high"],
        }
    )
    parquet_buffer = BytesIO()
    df.to_parquet(parquet_buffer)
    parquet_buffer.seek(0)

    mock_graph.execute.return_value = {
        "type": "parquet",
        "parsed_data": [
            {"skill": "machine_learning", "demand": "high"},
            {"skill": "data_analysis", "demand": "medium"},
            {"skill": "natural_language_processing", "demand": "high"},
        ],
        "num_rows": 3,
        "num_columns": 2,
    }

    result = await mock_graph.execute("parquet_input", parquet_buffer.getvalue())
    assert result["type"] == "parquet"
    assert result["parsed_data"][0]["skill"] == "machine_learning"
    assert result["num_rows"] == 3
    assert result["num_columns"] == 2


@pytest.mark.asyncio
async def test_structured_data_detector(mock_graph):
    detector = StructuredDataDetector("StructuredDataDetector")
    json_data = json.dumps({"ai_impact": {"job_creation": 500000, "job_displacement": 300000}})

    mock_graph.execute.return_value = {
        "type": "json",
        "parsed_data": {"ai_impact": {"job_creation": 500000, "job_displacement": 300000}},
    }

    result = await mock_graph.execute("structured_data_detector", json_data)
    assert result["type"] == "json"
    assert result["parsed_data"]["ai_impact"]["job_creation"] == 500000


@pytest.mark.asyncio
async def test_assistant_processing(mock_graph, mock_assistant):
    mock_graph.execute.return_value = "AI analysis result"

    result = await mock_graph.execute(
        "assistant", "Analyze the impact of AI on job markets based on all inputs"
    )
    assert result == "AI analysis result"


if __name__ == "__main__":
    pytest.main(["-v", __file__])
