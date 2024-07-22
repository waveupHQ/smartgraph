import json
import xml.etree.ElementTree as ET
from io import BytesIO, StringIO
from unittest.mock import AsyncMock, MagicMock

import pandas as pd
import pyarrow.parquet as pq
import pytest
import yaml

from smartgraph.components.input_handlers import (
    CommandLineInputHandler,
    CSVInputHandler,
    ImageUploadHandler,
    JSONInputHandler,
    ParquetInputHandler,
    SpeechInputHandler,
    StructuredDataDetector,
    TextInputHandler,
    VideoUploadHandler,
    XMLInputHandler,
    YAMLInputHandler,
)


@pytest.fixture
def text_input_handler():
    return TextInputHandler("TestTextHandler")

@pytest.fixture
def json_input_handler():
    return JSONInputHandler("TestJSONHandler")

@pytest.fixture
def xml_input_handler():
    return XMLInputHandler("TestXMLHandler")

@pytest.fixture
def csv_input_handler():
    return CSVInputHandler("TestCSVHandler")

@pytest.fixture
def yaml_input_handler():
    return YAMLInputHandler("TestYAMLHandler")

@pytest.fixture
def parquet_input_handler():
    return ParquetInputHandler("TestParquetHandler")

@pytest.fixture
def structured_data_detector():
    return StructuredDataDetector("TestStructuredDataDetector")

@pytest.mark.asyncio
async def test_text_input_handler(text_input_handler):
    input_text = "Hello, world!"
    result = await text_input_handler._handle_input(input_text)
    assert result["type"] == "text"
    assert result["content"] == "Hello, world!"
    assert result["length"] == 13
    assert result["word_count"] == 2

@pytest.mark.asyncio
async def test_json_input_handler(json_input_handler):
    input_json = '{"name": "John", "age": 30}'
    result = await json_input_handler._handle_input(input_json)
    assert result["type"] == "json"
    assert result["parsed_data"] == {"name": "John", "age": 30}

@pytest.mark.asyncio
async def test_xml_input_handler(xml_input_handler):
    input_xml = '<root><name>John</name><age>30</age></root>'
    result = await xml_input_handler._handle_input(input_xml)
    assert result["type"] == "xml"
    assert result["parsed_data"] == {"root": {"name": "John", "age": "30"}}

@pytest.mark.asyncio
async def test_csv_input_handler(csv_input_handler):
    input_csv = "name,age\nJohn,30\nJane,25"
    result = await csv_input_handler._handle_input(input_csv)
    assert result["type"] == "csv"
    assert result["parsed_data"] == [{"name": "John", "age": "30"}, {"name": "Jane", "age": "25"}]
    assert result["headers"] == ["name", "age"]

@pytest.mark.asyncio
async def test_yaml_input_handler(yaml_input_handler):
    input_yaml = "name: John\nage: 30"
    result = await yaml_input_handler._handle_input(input_yaml)
    assert result["type"] == "yaml"
    assert result["parsed_data"] == {"name": "John", "age": 30}

@pytest.mark.asyncio
async def test_parquet_input_handler(parquet_input_handler):
    df = pd.DataFrame({"name": ["John", "Jane"], "age": [30, 25]})
    parquet_buffer = BytesIO()
    df.to_parquet(parquet_buffer)
    parquet_buffer.seek(0)
    
    result = await parquet_input_handler._handle_input(parquet_buffer)
    assert result["type"] == "parquet"
    assert result["parsed_data"] == [{"name": "John", "age": 30}, {"name": "Jane", "age": 25}]
    assert result["num_rows"] == 2
    assert result["num_columns"] == 2

@pytest.mark.asyncio
async def test_structured_data_detector_json(structured_data_detector):
    input_data = '{"name": "John", "age": 30}'
    result = await structured_data_detector._handle_input(input_data)
    assert result["type"] == "json"
    assert result["parsed_data"] == {"name": "John", "age": 30}

@pytest.mark.asyncio
async def test_structured_data_detector_xml(structured_data_detector):
    input_data = '<root><name>John</name><age>30</age></root>'
    result = await structured_data_detector._handle_input(input_data)
    assert result["type"] == "xml"
    assert result["parsed_data"] == {"root": {"name": "John", "age": "30"}}

@pytest.mark.asyncio
async def test_structured_data_detector_unknown(structured_data_detector):
    input_data = "This is just plain text"
    result = await structured_data_detector._handle_input(input_data)
    assert result["type"] == "unknown"
    assert "error" in result

@pytest.fixture
def image_upload_handler():
    return ImageUploadHandler("TestImageHandler")

@pytest.mark.asyncio
async def test_image_upload_handler(image_upload_handler):
    input_data = {"filename": "test.jpg", "content": b"fake image content"}
    result = await image_upload_handler._handle_input(input_data)
    assert result["type"] == "image"
    assert result["filename"] == "test.jpg"
    assert result["content"] == b"fake image content"
    assert result["dimensions"] == "1024x768"
    assert result["format"] == "jpeg"

@pytest.fixture
def video_upload_handler():
    return VideoUploadHandler("TestVideoHandler")

@pytest.mark.asyncio
async def test_video_upload_handler(video_upload_handler):
    input_data = {"filename": "test.mp4", "content": b"fake video content"}
    result = await video_upload_handler._handle_input(input_data)
    assert result["type"] == "video"
    assert result["filename"] == "test.mp4"
    assert result["content"] == b"fake video content"
    assert result["duration"] == "00:05:30"
    assert result["resolution"] == "1920x1080"

@pytest.fixture
def speech_input_handler():
    return SpeechInputHandler("TestSpeechHandler")

@pytest.mark.asyncio
async def test_speech_input_handler(speech_input_handler):
    input_data = {
        "audio_data": "This is a transcription of speech",
        "duration": "00:00:30",
        "language": "en-US"
    }
    result = await speech_input_handler._handle_input(input_data)
    assert result["type"] == "speech"
    assert result["transcription"] == "This is a transcription of speech"
    assert result["duration"] == "00:00:30"
    assert result["language"] == "en-US"

@pytest.fixture
def command_line_input_handler():
    return CommandLineInputHandler("TestCommandLineHandler")

@pytest.mark.asyncio
async def test_command_line_input_handler(command_line_input_handler):
    input_data = "git commit -m 'Initial commit'"
    result = await command_line_input_handler._handle_input(input_data)
    assert result["type"] == "command"
    assert result["command"] == "git"
    assert result["args"] == ["commit", "-m", "'Initial commit'"]
    assert result["full_input"] == input_data

