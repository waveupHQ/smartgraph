# smartgraph/__init__.py

from .actors import Actor, AIActor, HumanActor
from .base import BaseActor, BaseNode, Task
from .core import Edge, Node, SmartGraph
from .memory import MemoryManager
from .reducers import dict_update_reducer, list_append_reducer, max_reducer

__all__ = [
    "SmartGraph",
    "Node",
    "Edge",
    "Task",
    "BaseActor",
    "BaseNode",
    "Actor",
    "HumanActor",
    "AIActor",
    "MemoryManager",
    "dict_update_reducer",
    "list_append_reducer",
    "max_reducer",
]

__version__ = "0.1.0"
