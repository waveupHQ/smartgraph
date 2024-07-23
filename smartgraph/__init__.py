# smartgraph/__init__.py

from .assistant_conversation import ReactiveAssistantConversation
from .component import ReactiveAIComponent

# Import all components
from .components import *  # noqa: F403
from .components.human_in_the_loop import HumanInTheLoopComponent, HumanInTheLoopGraph
from .core import ReactiveEdge, ReactiveNode, StateManager
from .exceptions import (
    ConfigurationError,
    ExecutionError,
    GraphStructureError,
    MemoryError,
    SmartGraphException,
    ValidationError,
)
from .graph import ReactiveSmartGraph
from .logging import SmartGraphLogger

# List of core classes
__core_classes__ = [
    "ReactiveAIComponent",
    "StateManager",
    "ReactiveNode",
    "ReactiveEdge",
    "ReactiveSmartGraph",
    "ReactiveAssistantConversation",
    "SmartGraphLogger",
    "SmartGraphException",
    "ExecutionError",
    "ConfigurationError",
    "ValidationError",
    "MemoryError",
    "GraphStructureError",
]

# Combine core classes and components
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
    "HumanInTheLoopGraph",
]

__version__ = "0.2.0"
