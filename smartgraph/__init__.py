# smartgraph/__init__.py

from smartgraph.components import AggregatorComponent

from .assistant_conversation import ReactiveAssistantConversation
from .components import (
    AggregatorComponent,
    AsyncAPIComponent,
    BranchingComponent,
    CacheComponent,
    FilterComponent,
    RetryComponent,
    TransformerComponent,
    ValidationComponent,
)
from .core import ReactiveEdge, ReactiveNode, ReactiveSmartGraph
from .exceptions import (
    ConfigurationError,
    ExecutionError,
    GraphStructureError,
    MemoryError,
    SmartGraphException,
    ValidationError,
)
from .logging import SmartGraphLogger

# You can also include any utility functions or constants if you've defined any

__all__ = [
    "ReactiveAIComponent",
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
    "AggregatorComponent",
    "FilterComponent",
    "TransformerComponent",
    "BranchingComponent",
    "AsyncAPIComponent",
    "RetryComponent",
    "CacheComponent",
    "ValidationComponent",
]

__version__ = "0.2.0"  # Update this to reflect the new reactive version
