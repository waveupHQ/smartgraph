# smartgraph/__init__.py  # noqa: D104

from .actors import Actor, AIActor, HumanActor
from .core import Edge, Node, SmartGraph, Task
from .memory import MemoryManager
from .reducers import dict_update_reducer, list_append_reducer, max_reducer

__all__ = [
    "SmartGraph",
    "Node",
    "Edge",
    "Task",
    "Actor",
    "HumanActor",
    "AIActor",
    "MemoryManager",
    "dict_update_reducer",
    "list_append_reducer",
    "max_reducer",
]

__version__ = "0.1.0"
