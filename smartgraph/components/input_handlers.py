# smartgraph/components/input_handlers.py

import csv
import json
import xml.etree.ElementTree as ET  # noqa: N817
from io import BytesIO, StringIO
from typing import Any, Dict, List, Optional, Union

import pandas as pd
import pyarrow.parquet as pq
import yaml
from bs4 import BeautifulSoup
from reactivex import Observable, Subject

from smartgraph import ReactiveAIComponent


class BaseInputHandler(ReactiveAIComponent):
    def __init__(self, name: str):
        super().__init__(name)
        self.input_subject = Subject()
        self.output = self.input_subject.pipe()  # You can add operators here if needed

    async def process(self, input_data: Any) -> Any:
        # This method will be called when the component receives input
        return await self._handle_input(input_data)

    async def _handle_input(self, input_data: Any) -> Any:
        # This method should be overridden by subclasses to implement specific input handling logic
        raise NotImplementedError("Subclasses must implement _handle_input method")

    def submit_input(self, input_data: Any):
        # This method is called to submit input
        self.input_subject.on_next(input_data)

    def get_input_observable(self) -> Observable:
        return self.input_subject.asObservable()


class UnstructuredDataInputHandler(BaseInputHandler):
    async def _handle_input(self, input_data: Any) -> Dict[str, Any]:
        # Base implementation for unstructured data
        return {"type": "unstructured", "content": input_data}


class StructuredDataInputHandler(BaseInputHandler):
    async def _handle_input(self, input_data: Any) -> Dict[str, Any]:
        # Base implementation for structured data
        return {"type": "structured", "content": input_data}


# Specific Unstructured Data Handlers


class TextInputHandler(UnstructuredDataInputHandler):
    async def _handle_input(self, input_data: str) -> Dict[str, Any]:
        result = await super()._handle_input(input_data)
        result.update(
            {
                "type": "text",
                "content": input_data.strip(),
                "length": len(input_data.strip()),
                "word_count": len(input_data.split()),
            }
        )
        return result


class FileUploadHandler(UnstructuredDataInputHandler):
    def __init__(self, name: str, allowed_extensions: Optional[List[str]] = None):
        super().__init__(name)
        self.allowed_extensions = allowed_extensions or []

    async def _handle_input(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        result = await super()._handle_input(input_data)
        filename = input_data.get("filename", "")
        if self.allowed_extensions and not any(
            filename.endswith(ext) for ext in self.allowed_extensions
        ):
            raise ValueError(
                f"Unsupported file type. Allowed types: {', '.join(self.allowed_extensions)}"
            )
        result.update(
            {
                "type": "file",
                "filename": filename,
                "content": input_data.get("content"),
                "size": len(input_data.get("content", "")),
            }
        )
        return result


class ImageUploadHandler(FileUploadHandler):
    def __init__(self, name: str):
        super().__init__(name, allowed_extensions=[".jpg", ".jpeg", ".png", ".gif"])

    async def _handle_input(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        result = await super()._handle_input(input_data)
        result.update(
            {
                "type": "image",
                "dimensions": "1024x768",  # Placeholder, replace with actual image processing
                "format": "jpeg",
            }
        )
        return result


class VideoUploadHandler(FileUploadHandler):
    def __init__(self, name: str):
        super().__init__(name, allowed_extensions=[".mp4", ".avi", ".mov"])

    async def _handle_input(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        # Call the parent method first
        result = await super()._handle_input(input_data)
        # Add video-specific processing here (e.g., duration, resolution)
        result["type"] = "video"
        # Here you would typically use a video processing library to get more details
        # For this example, we'll just add placeholder values
        result["duration"] = "00:05:30"
        result["resolution"] = "1920x1080"
        return result


class SpeechInputHandler(UnstructuredDataInputHandler):
    async def _handle_input(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        # Here you could add speech-to-text conversion
        # For now, we'll assume the input is already transcribed
        return {
            "type": "speech",
            "transcription": input_data.get("audio_data", ""),
            "duration": input_data.get("duration", "00:00:00"),
            "language": input_data.get("language", "en-US"),
        }


class CommandLineInputHandler(UnstructuredDataInputHandler):
    async def _handle_input(self, input_data: str) -> Dict[str, Any]:
        # Parse command-line style input
        parts = input_data.split()
        command = parts[0] if parts else ""
        args = parts[1:] if len(parts) > 1 else []
        return {"type": "command", "command": command, "args": args, "full_input": input_data}


# Specific Structured Data Handler


class JSONInputHandler(StructuredDataInputHandler):
    async def _handle_input(self, input_data: str) -> Dict[str, Any]:
        result = await super()._handle_input(input_data)
        try:
            parsed_data = json.loads(input_data)
            result.update({"type": "json", "parsed_data": parsed_data})
        except json.JSONDecodeError as e:
            result.update({"type": "json", "error": f"Failed to parse JSON: {str(e)}"})
        return result


class XMLInputHandler(StructuredDataInputHandler):
    async def _handle_input(self, input_data: str) -> Dict[str, Any]:
        result = await super()._handle_input(input_data)
        try:
            root = ET.fromstring(input_data)
            parsed_data = self._element_to_dict(root)
            result.update({"type": "xml", "parsed_data": parsed_data})
        except ET.ParseError as e:
            result.update({"type": "xml", "error": f"Failed to parse XML: {str(e)}"})
        return result

    def _element_to_dict(self, element: ET.Element) -> Dict[str, Any]:
        result = {}
        for child in element:
            if len(child) == 0:
                result[child.tag] = child.text
            else:
                result[child.tag] = self._element_to_dict(child)
        return result


class CSVInputHandler(StructuredDataInputHandler):
    async def _handle_input(self, input_data: str) -> Dict[str, Any]:
        result = await super()._handle_input(input_data)
        try:
            csv_data = csv.DictReader(StringIO(input_data))
            parsed_data = [row for row in csv_data]
            result.update(
                {"type": "csv", "parsed_data": parsed_data, "headers": csv_data.fieldnames}
            )
        except csv.Error as e:
            result.update({"type": "csv", "error": f"Failed to parse CSV: {str(e)}"})
        return result


class YAMLInputHandler(StructuredDataInputHandler):
    async def _handle_input(self, input_data: str) -> Dict[str, Any]:
        result = await super()._handle_input(input_data)
        try:
            parsed_data = yaml.safe_load(input_data)
            result.update({"type": "yaml", "parsed_data": parsed_data})
        except yaml.YAMLError as e:
            result.update({"type": "yaml", "error": f"Failed to parse YAML: {str(e)}"})
        return result


class ParquetInputHandler(StructuredDataInputHandler):
    async def _handle_input(self, input_data: Union[bytes, BytesIO]) -> Dict[str, Any]:
        result = await super()._handle_input(input_data)
        try:
            if isinstance(input_data, bytes):
                input_data = BytesIO(input_data)
            table = pq.read_table(input_data)
            df = table.to_pandas()
            parsed_data = df.to_dict(orient="records")
            result.update(
                {
                    "type": "parquet",
                    "parsed_data": parsed_data,
                    "schema": table.schema.to_string(),
                    "num_rows": len(parsed_data),
                    "num_columns": len(df.columns),
                }
            )
        except Exception as e:
            result.update({"type": "parquet", "error": f"Failed to parse Parquet: {str(e)}"})
        return result


class StructuredDataDetector(StructuredDataInputHandler):
    def __init__(self, name: str):
        super().__init__(name)
        self.handlers = {
            "json": JSONInputHandler("JSONDetector"),
            "xml": XMLInputHandler("XMLDetector"),
            "csv": CSVInputHandler("CSVDetector"),
            "yaml": YAMLInputHandler("YAMLDetector"),
            "parquet": ParquetInputHandler("ParquetDetector"),
        }

    async def _handle_input(self, input_data: Any) -> Dict[str, Any]:
        result = await super()._handle_input(input_data)
        detected_type = self._detect_type(input_data)
        if detected_type:
            handler = self.handlers[detected_type]
            result = await handler._handle_input(input_data)
        else:
            result.update({"type": "unknown", "error": "Unable to detect structured data type"})
        return result

    def _detect_type(self, input_data: Any) -> Optional[str]:
        # Simple type detection based on content
        if isinstance(input_data, bytes):
            try:
                pq.read_table(BytesIO(input_data))
                return "parquet"
            except:
                pass

        if isinstance(input_data, str):
            input_data = input_data.strip()
            if input_data.startswith("{") and input_data.endswith("}"):
                return "json"
            elif input_data.startswith("<") and input_data.endswith(">"):
                return "xml"
            elif "," in input_data and "\n" in input_data:
                return "csv"
            elif ":" in input_data and ("-" in input_data or input_data.count("\n") > 1):
                return "yaml"

        return None
