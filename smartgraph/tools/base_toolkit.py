# smartgraph/tools/base_toolkit.py

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class Toolkit(ABC):
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

    @property
    def schemas(self) -> List[Dict[str, Any]]:
        """Return a list of function schemas for the toolkit."""
        return [
            {
                "type": "function",
                "function": {
                    "name": name,
                    "description": func.__doc__,
                    "parameters": getattr(func, "schema", {})
                }
            }
            for name, func in self.functions.items()
        ]