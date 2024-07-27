import pytest
import json
import yaml
from io import BytesIO
import pandas as pd

from smartgraph.components.input_handlers import (
    TextInputHandler,
    JSONInputHandler,
    XMLInputHandler,
    YAMLInputHandler,
    ParquetInputHandler,
    CSVInputHandler,
    FileUploadHandler,
    ImageUploadHandler,
    CommandLineInputHandler
)

@pytest.mark.asyncio
async def test_text_input_handler():
    handler = TextInputHandler("TextInput")
    result = await handler.process("Hello, world!")
    
    assert result == {
        "type": "text",
        "content": "Hello, world!",
        "length": 13,
        "word_count": 2,
    }

@pytest.mark.asyncio
async def test_json_input_handler():
    handler = JSONInputHandler("JSONInput")
    input_data = json.dumps({"key": "value", "number": 42})
    result = await handler.process(input_data)
    
    assert result == {
        "type": "json",
        "parsed_data": {"key": "value", "number": 42},
    }

@pytest.mark.asyncio
async def test_json_input_handler_error():
    handler = JSONInputHandler("JSONInput")
    input_data = "This is not valid JSON"
    result = await handler.process(input_data)
    
    assert result["type"] == "json"
    assert "error" in result
    assert "Failed to parse JSON" in result["error"]

@pytest.mark.asyncio
async def test_command_line_input_handler():
    handler = CommandLineInputHandler("CLIInput")
    input_data = 'echo "Hello, world!"'
    result = await handler.process(input_data)
    
    assert result == {
        "type": "command",
        "command": "echo",
        "args": ['"Hello, world!"'],
        "full_input": 'echo "Hello, world!"',
    }

@pytest.mark.asyncio
async def test_xml_input_handler():
    handler = XMLInputHandler("XMLInput")
    input_data = "<root><key>value</key></root>"
    result = await handler.process(input_data)
    
    assert result == {
        "type": "xml",
        "parsed_data": {"root": {"key": "value"}},
    }

@pytest.mark.asyncio
async def test_yaml_input_handler():
    handler = YAMLInputHandler("YAMLInput")
    input_data = yaml.dump({"key": "value", "nested": {"item": "data"}})
    result = await handler.process(input_data)
    
    assert result == {
        "type": "yaml",
        "parsed_data": {"key": "value", "nested": {"item": "data"}},
    }

@pytest.mark.asyncio
async def test_parquet_input_handler():
    handler = ParquetInputHandler("ParquetInput")
    df = pd.DataFrame({"A": [1, 2, 3], "B": ["a", "b", "c"]})
    parquet_buffer = BytesIO()
    df.to_parquet(parquet_buffer)
    parquet_buffer.seek(0)
    
    result = await handler.process(parquet_buffer.getvalue())
    
    assert result["type"] == "parquet"
    assert "parsed_data" in result
    assert len(result["parsed_data"]) == 3
    assert "num_rows" in result
    assert "num_columns" in result

@pytest.mark.asyncio
async def test_csv_input_handler():
    handler = CSVInputHandler("CSVInput")
    input_data = "A,B\n1,a\n2,b\n3,c"
    result = await handler.process(input_data)
    
    assert result == {
        "type": "csv",
        "parsed_data": [{"A": "1", "B": "a"}, {"A": "2", "B": "b"}, {"A": "3", "B": "c"}],
        "headers": ["A", "B"],
    }

@pytest.mark.asyncio
async def test_file_upload_handler():
    handler = FileUploadHandler("FileUpload", allowed_extensions=[".txt"])
    input_data = {"filename": "test.txt", "content": b"This is a test file content"}
    result = await handler.process(input_data)
    
    assert result == {
        "type": "file",
        "filename": "test.txt",
        "content": b"This is a test file content",
        "size": len(b"This is a test file content"),
    }

@pytest.mark.asyncio
async def test_image_upload_handler():
    handler = ImageUploadHandler("ImageUpload")
    input_data = {"filename": "test.jpg", "content": b"fake image data"}
    result = await handler.process(input_data)
    
    assert result["type"] == "image"
    assert result["filename"] == "test.jpg"
    assert result["content"] == b"fake image data"
    assert "dimensions" in result
    assert "format" in result

