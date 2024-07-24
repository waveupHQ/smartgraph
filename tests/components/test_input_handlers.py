# components/test_input_handlers.py
import asyncio
import json
import xml.etree.ElementTree as ET  # noqa: N817
from io import BytesIO, StringIO

import pandas as pd
import pytest
import yaml
from reactivex import operators as ops
from reactivex.testing import ReactiveTest, TestScheduler

from smartgraph.components.input_handlers import (
    CSVInputHandler,
    FileUploadHandler,
    ImageUploadHandler,
    JSONInputHandler,
    ParquetInputHandler,
    TextInputHandler,
    XMLInputHandler,
    YAMLInputHandler,
)
from smartgraph.core import ReactiveSmartGraph

on_next = ReactiveTest.on_next
on_completed = ReactiveTest.on_completed
on_error = ReactiveTest.on_error


@pytest.fixture
def graph():
    return ReactiveSmartGraph()


def test_text_input_handler(graph):
    scheduler = TestScheduler()
    text_input = TextInputHandler("TextInput")
    pipeline = graph.create_pipeline("TestPipeline")
    pipeline.add_component(text_input)
    graph.compile()

    def create():
        return graph.execute("TestPipeline", "Hello, world!").pipe(
            ops.map(lambda x: asyncio.get_event_loop().run_until_complete(x))
        )

    results = scheduler.start(create)

    assert len(results.messages) == 1
    assert results.messages[0].value.kind == "N"  # 'N' for "OnNext"
    assert results.messages[0].time == 200
    assert results.messages[0].value.value == {
        "type": "text",
        "content": "Hello, world!",
        "length": 13,
        "word_count": 2,
    }


def test_json_input_handler(graph):
    scheduler = TestScheduler()
    json_input = JSONInputHandler("JSONInput")
    pipeline = graph.create_pipeline("TestPipeline")
    pipeline.add_component(json_input)
    graph.compile()

    input_data = json.dumps({"key": "value", "number": 42})

    def create():
        return graph.execute("TestPipeline", input_data).pipe(
            ops.map(lambda x: asyncio.get_event_loop().run_until_complete(x))
        )

    results = scheduler.start(create)

    assert len(results.messages) == 1
    assert results.messages[0].value.kind == "N"
    assert results.messages[0].time == 200
    assert results.messages[0].value.value == {
        "type": "json",
        "parsed_data": {"key": "value", "number": 42},
    }


def test_json_input_handler_error(graph):
    scheduler = TestScheduler()
    json_input = JSONInputHandler("JSONInput")
    pipeline = graph.create_pipeline("TestPipeline")
    pipeline.add_component(json_input)
    graph.compile()

    input_data = "This is not valid JSON"

    def create():
        return graph.execute("TestPipeline", input_data).pipe(
            ops.map(lambda x: asyncio.get_event_loop().run_until_complete(x))
        )

    results = scheduler.start(create)

    assert len(results.messages) == 1
    assert results.messages[0].value.kind == "N"  # 'N' for "OnNext"
    assert results.messages[0].time == 200
    assert results.messages[0].value.value["type"] == "json"
    assert "error" in results.messages[0].value.value
    assert "Failed to parse JSON" in results.messages[0].value.value["error"]


def test_xml_input_handler(graph):
    scheduler = TestScheduler()
    xml_input = XMLInputHandler("XMLInput")
    pipeline = graph.create_pipeline("TestPipeline")
    pipeline.add_component(xml_input)
    graph.compile()

    input_data = "<root><key>value</key></root>"

    def create():
        return graph.execute("TestPipeline", input_data).pipe(
            ops.map(lambda x: asyncio.get_event_loop().run_until_complete(x))
        )

    results = scheduler.start(create)

    assert len(results.messages) == 1
    assert results.messages[0].value.kind == "N"
    assert results.messages[0].time == 200
    assert results.messages[0].value.value == {
        "type": "xml",
        "parsed_data": {"root": {"key": "value"}},
    }


def test_yaml_input_handler(graph):
    scheduler = TestScheduler()
    yaml_input = YAMLInputHandler("YAMLInput")
    pipeline = graph.create_pipeline("TestPipeline")
    pipeline.add_component(yaml_input)
    graph.compile()

    input_data = yaml.dump({"key": "value", "nested": {"item": "data"}})

    def create():
        return graph.execute("TestPipeline", input_data).pipe(
            ops.map(lambda x: asyncio.get_event_loop().run_until_complete(x))
        )

    results = scheduler.start(create)

    assert len(results.messages) == 1
    assert results.messages[0].value.kind == "N"
    assert results.messages[0].time == 200
    assert results.messages[0].value.value == {
        "type": "yaml",
        "parsed_data": {"key": "value", "nested": {"item": "data"}},
    }


def test_parquet_input_handler(graph):
    scheduler = TestScheduler()
    parquet_input = ParquetInputHandler("ParquetInput")
    pipeline = graph.create_pipeline("TestPipeline")
    pipeline.add_component(parquet_input)
    graph.compile()

    # Create a sample parquet file
    df = pd.DataFrame({"A": [1, 2, 3], "B": ["a", "b", "c"]})
    parquet_buffer = BytesIO()
    df.to_parquet(parquet_buffer)
    parquet_buffer.seek(0)

    def create():
        return graph.execute("TestPipeline", parquet_buffer.getvalue()).pipe(
            ops.map(lambda x: asyncio.get_event_loop().run_until_complete(x))
        )

    results = scheduler.start(create)

    assert len(results.messages) == 1
    assert results.messages[0].value.kind == "N"
    assert results.messages[0].time == 200
    assert results.messages[0].value.value["type"] == "parquet"
    assert "parsed_data" in results.messages[0].value.value
    assert len(results.messages[0].value.value["parsed_data"]) == 3
    assert "num_rows" in results.messages[0].value.value
    assert "num_columns" in results.messages[0].value.value


def test_csv_input_handler(graph):
    scheduler = TestScheduler()
    csv_input = CSVInputHandler("CSVInput")
    pipeline = graph.create_pipeline("TestPipeline")
    pipeline.add_component(csv_input)
    graph.compile()

    input_data = "A,B\n1,a\n2,b\n3,c"

    def create():
        return graph.execute("TestPipeline", input_data).pipe(
            ops.map(lambda x: asyncio.get_event_loop().run_until_complete(x))
        )

    results = scheduler.start(create)

    assert len(results.messages) == 1
    assert results.messages[0].value.kind == "N"
    assert results.messages[0].time == 200
    assert results.messages[0].value.value == {
        "type": "csv",
        "parsed_data": [{"A": "1", "B": "a"}, {"A": "2", "B": "b"}, {"A": "3", "B": "c"}],
        "headers": ["A", "B"],
    }


def test_file_upload_handler(graph):
    scheduler = TestScheduler()
    file_upload = FileUploadHandler("FileUpload", allowed_extensions=[".txt"])
    pipeline = graph.create_pipeline("TestPipeline")
    pipeline.add_component(file_upload)
    graph.compile()

    input_data = {"filename": "test.txt", "content": b"This is a test file content"}

    def create():
        return graph.execute("TestPipeline", input_data).pipe(
            ops.map(lambda x: asyncio.get_event_loop().run_until_complete(x))
        )

    results = scheduler.start(create)

    assert len(results.messages) == 1
    assert results.messages[0].value.kind == "N"
    assert results.messages[0].time == 200
    assert results.messages[0].value.value == {
        "type": "file",
        "filename": "test.txt",
        "content": b"This is a test file content",
        "size": len(b"This is a test file content"),
    }


def test_image_upload_handler(graph):
    scheduler = TestScheduler()
    image_upload = ImageUploadHandler("ImageUpload")
    pipeline = graph.create_pipeline("TestPipeline")
    pipeline.add_component(image_upload)
    graph.compile()

    input_data = {"filename": "test.jpg", "content": b"fake image data"}

    def create():
        return graph.execute("TestPipeline", input_data).pipe(
            ops.map(lambda x: asyncio.get_event_loop().run_until_complete(x))
        )

    results = scheduler.start(create)

    assert len(results.messages) == 1
    assert results.messages[0].value.kind == "N"
    assert results.messages[0].time == 200
    assert results.messages[0].value.value["type"] == "image"
    assert results.messages[0].value.value["filename"] == "test.jpg"
    assert results.messages[0].value.value["content"] == b"fake image data"
    assert "dimensions" in results.messages[0].value.value
    assert "format" in results.messages[0].value.value
