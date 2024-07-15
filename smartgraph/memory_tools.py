# smartgraph/memory_tools.py

from typing import Any, Dict, List


class MemoryTools:
    def __init__(self, memory_manager):
        self.memory_manager = memory_manager

    def add_to_long_term_memory(self, key: str, value: str) -> str:
        self.memory_manager.add_long_term(key, value)
        return f"Successfully added to long-term memory: {key}: {value}"

    def retrieve_from_long_term_memory(self, key: str) -> str:
        value = self.memory_manager.get_long_term(key)
        return (
            f"Retrieved from long-term memory: {key}: {value}"
            if value
            else f"No memory found for key: {key}"
        )

    def list_long_term_memories(self) -> str:
        memories = self.memory_manager.get_long_term()
        return "\n".join([f"{k}: {v['value']}" for k, v in memories.items()])

    def get_tools_list(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "add_to_long_term_memory",
                    "description": "Add a new item to long-term memory",
                    "parameters": {
                        "type": "object",
                        "properties": {"key": {"type": "string"}, "value": {"type": "string"}},
                        "required": ["key", "value"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "retrieve_from_long_term_memory",
                    "description": "Retrieve an item from long-term memory",
                    "parameters": {
                        "type": "object",
                        "properties": {"key": {"type": "string"}},
                        "required": ["key"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "list_long_term_memories",
                    "description": "List all items in long-term memory",
                    "parameters": {"type": "object", "properties": {}},
                },
            },
        ]
