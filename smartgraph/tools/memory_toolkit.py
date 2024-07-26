from typing import Any, Dict, List, Optional, abstractmethod

from .base_toolkit import Toolkit


class MemoryToolkit(Toolkit):
    @property
    @abstractmethod
    def name(self) -> str:
        """Return the name of the toolkit."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Return a description of the toolkit."""
        pass

    @property
    @abstractmethod
    def functions(self) -> Dict[str, Any]:
        """Return a dictionary of functions provided by the toolkit."""
        pass

    async def add_memory(self, key: str, value: Any) -> None:
        """Add a new memory or update an existing one."""
        pass

    async def get_memory(self, key: str) -> Optional[Any]:
        """Retrieve a memory by its key."""
        pass

    async def search_memories(self, query: str) -> List[Dict[str, Any]]:
        """Search memories based on a query."""
        pass

    async def delete_memory(self, key: str) -> None:
        """Delete a memory by its key."""
        pass
