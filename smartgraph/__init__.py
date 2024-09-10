# smartgraph/__init__.py

# Import all components
from .components import *
from .core import Pipeline, ReactiveComponent, ReactiveSmartGraph
from .exceptions import (
    ConfigurationError,
    ExecutionError,
    GraphStructureError,
    MemoryError,
    SmartGraphException,
    ValidationError,
)
from .graph_visualizer import GraphVisualizer
from .logging import SmartGraphLogger

# Import all toolkits
from .tools import *
from .tools.memory_toolkit import MemoryToolkit
from .utils import process_observable

# List of core classes
__core_classes__ = [
    "ReactiveComponent",
    "Pipeline",
    "ReactiveSmartGraph",
    "SmartGraphLogger",
    "GraphVisualizer",
    "SmartGraphException",
    "ExecutionError",
    "ConfigurationError",
    "ValidationError",
    "MemoryError",
    "GraphStructureError",
    "GraphVisualizer",
]

# Combine core classes, components, and toolkits
__all__ = __core_classes__ + [
    "AggregatorComponent",
    "FilterComponent",
    "TransformerComponent",
    "BranchingComponent",
    "AsyncAPIComponent",
    "RetryComponent",
    "CacheComponent",
    "ValidationComponent",
    "BaseInputHandler",
    "UnstructuredDataInputHandler",
    "StructuredDataInputHandler",
    "TextInputHandler",
    "FileUploadHandler",
    "ImageUploadHandler",
    "VideoUploadHandler",
    "SpeechInputHandler",
    "CommandLineInputHandler",
    "JSONInputHandler",
    "XMLInputHandler",
    "CSVInputHandler",
    "YAMLInputHandler",
    "ParquetInputHandler",
    "StructuredDataDetector",
    "HumanInTheLoopComponent",
    "MemoryToolkit",
    "DuckDuckGoToolkit",
    "TavilyToolkit",
    "process_observable",
]

__version__ = "0.2.0"
