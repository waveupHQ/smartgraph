import csv
import json
import xml.etree.ElementTree as ET
from io import BytesIO, StringIO
from typing import Any, Dict, List, Optional, Union

import pandas as pd
import pyarrow.parquet as pq
import yaml
from reactivex import Observable, Subject

from ..core import ReactiveComponent
from ..logging import SmartGraphLogger

logger = SmartGraphLogger.get_logger()

class BaseInputHandler(ReactiveComponent):
    async def process(self, input_data: Any) -> Dict[str, Any]:
        try:
            return await self._handle_input(input_data)
        except Exception as e:
            logger.error(f"Error in {self.__class__.__name__}: {str(e)}")
            return {"type": self._get_type(), "error": str(e)}

    async def _handle_input(self, input_data: Any) -> Dict[str, Any]:
        raise NotImplementedError("Subclasses must implement _handle_input method")

    def _get_type(self) -> str:
        return self.__class__.__name__.lower().replace("inputhandler", "")

class TextInputHandler(BaseInputHandler):
    async def _handle_input(self, input_data: str) -> Dict[str, Any]:
        return {
            "type": "text",
            "content": input_data.strip(),
            "length": len(input_data.strip()),
            "word_count": len(input_data.split()),
        }

class FileUploadHandler(BaseInputHandler):
    def __init__(self, name: str, allowed_extensions: Optional[List[str]] = None):
        super().__init__(name)
        self.allowed_extensions = allowed_extensions or []

    async def _handle_input(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        filename = input_data.get("filename", "")
        if self.allowed_extensions and not any(filename.endswith(ext) for ext in self.allowed_extensions):
            raise ValueError(f"Unsupported file type. Allowed types: {', '.join(self.allowed_extensions)}")
        return {
            "type": "file",
            "filename": filename,
            "content": input_data.get("content"),
            "size": len(input_data.get("content", "")),
        }

class ImageUploadHandler(FileUploadHandler):
    def __init__(self, name: str):
        super().__init__(name, allowed_extensions=[".jpg", ".jpeg", ".png", ".gif"])

    async def _handle_input(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        result = await super()._handle_input(input_data)
        result.update({
            "type": "image",
            "dimensions": "1024x768",  # Placeholder
            "format": "jpeg",
        })
        return result

class VideoUploadHandler(FileUploadHandler):
    def __init__(self, name: str):
        super().__init__(name, allowed_extensions=[".mp4", ".avi", ".mov"])

    async def _handle_input(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        result = await super()._handle_input(input_data)
        result.update({
            "type": "video",
            "duration": "00:05:30",  # Placeholder
            "resolution": "1920x1080",
        })
        return result

class SpeechInputHandler(BaseInputHandler):
    async def _handle_input(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "type": "speech",
            "transcription": input_data.get("audio_data", ""),
            "duration": input_data.get("duration", "00:00:00"),
            "language": input_data.get("language", "en-US"),
        }

class CommandLineInputHandler(BaseInputHandler):
    async def _handle_input(self, input_data: str) -> Dict[str, Any]:
        parts = []
        current_part = []
        in_quotes = False
        quote_char = None

        for char in input_data:
            if char in ["'", '"']:
                if not in_quotes:
                    in_quotes = True
                    quote_char = char
                    current_part.append(char)
                elif char == quote_char:
                    in_quotes = False
                    quote_char = None
                    current_part.append(char)
                    parts.append("".join(current_part))
                    current_part = []
                else:
                    current_part.append(char)
            elif char.isspace() and not in_quotes:
                if current_part:
                    parts.append("".join(current_part))
                    current_part = []
            else:
                current_part.append(char)

        if current_part:
            parts.append("".join(current_part))

        return {
            "type": "command",
            "command": parts[0] if parts else "",
            "args": parts[1:],
            "full_input": input_data
        }

class JSONInputHandler(BaseInputHandler):
    async def _handle_input(self, input_data: str) -> Dict[str, Any]:
        try:
            return {"type": "json", "parsed_data": json.loads(input_data)}
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON: {str(e)}")

class XMLInputHandler(BaseInputHandler):
    async def _handle_input(self, input_data: str) -> Dict[str, Any]:
        root = ET.fromstring(input_data)
        return {"type": "xml", "parsed_data": {"root": self._element_to_dict(root)}}

    def _element_to_dict(self, element: ET.Element) -> Dict[str, Any]:
        result = {}
        for child in element:
            if len(child) == 0:
                result[child.tag] = child.text
            else:
                result[child.tag] = self._element_to_dict(child)
        return result

class CSVInputHandler(BaseInputHandler):
    async def _handle_input(self, input_data: str) -> Dict[str, Any]:
        csv_data = csv.DictReader(StringIO(input_data))
        return {
            "type": "csv",
            "parsed_data": list(csv_data),
            "headers": csv_data.fieldnames
        }

class YAMLInputHandler(BaseInputHandler):
    async def _handle_input(self, input_data: str) -> Dict[str, Any]:
        return {"type": "yaml", "parsed_data": yaml.safe_load(input_data)}

class ParquetInputHandler(BaseInputHandler):
    async def _handle_input(self, input_data: Union[bytes, BytesIO]) -> Dict[str, Any]:
        if isinstance(input_data, bytes):
            input_data = BytesIO(input_data)
        table = pq.read_table(input_data)
        df = table.to_pandas()
        return {
            "type": "parquet",
            "parsed_data": df.to_dict(orient="records"),
            "schema": table.schema.to_string(),
            "num_rows": len(df),
            "num_columns": len(df.columns),
        }

class StructuredDataDetector(BaseInputHandler):
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
        detected_type = self._detect_type(input_data)
        if detected_type:
            handler = self.handlers[detected_type]
            return await handler.process(input_data)
        return {"type": "unknown", "error": "Unable to detect structured data type"}

    def _detect_type(self, input_data: Any) -> Optional[str]:
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
