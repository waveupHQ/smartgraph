import json
from typing import Any, Dict, List, Optional
from datetime import datetime

import duckdb

from .base_toolkit import Toolkit

class DuckMemoryToolkit(Toolkit):
    def __init__(self, db_path: str = ":memory:"):
        self.conn = duckdb.connect(db_path)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                key VARCHAR PRIMARY KEY,
                value JSON,
                created_at TIMESTAMP,
                updated_at TIMESTAMP
            )
        """)

    @property
    def name(self) -> str:
        return "DuckMemoryToolkit"

    @property
    def description(self) -> str:
        return "A memory toolkit using DuckDB for storage and retrieval of information."

    @property
    def functions(self) -> Dict[str, Any]:
        return {
            "add_memory": self.add_memory,
            "get_memory": self.get_memory,
            "search_memories": self.search_memories,
            "delete_memory": self.delete_memory,
        }

    async def add_memory(self, key: str, value: Any) -> None:
        json_value = json.dumps(value)
        current_time = datetime.now().isoformat()
        self.conn.execute("""
            INSERT INTO memories (key, value, created_at, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT (key) DO UPDATE SET
                value = excluded.value,
                updated_at = ?
        """, [key, json_value, current_time, current_time, current_time])

    async def get_memory(self, key: str) -> Optional[Any]:
        result = self.conn.execute("SELECT value FROM memories WHERE key = ?", [key]).fetchone()
        if result:
            return json.loads(result[0])
        return None

    async def search_memories(self, query: str) -> List[Dict[str, Any]]:
        # Use JSON extraction to search within the value column
        results = self.conn.execute("""
            SELECT key, value, created_at, updated_at
            FROM memories
            WHERE key LIKE ? OR json_extract(value, '$') LIKE ?
        """, [f'%{query}%', f'%{query}%']).fetchall()
        
        return [
            {
                "key": row[0],
                "value": json.loads(row[1]),
                "created_at": row[2].isoformat() if row[2] else None,
                "updated_at": row[3].isoformat() if row[3] else None
            }
            for row in results
        ]

    async def delete_memory(self, key: str) -> None:
        self.conn.execute("DELETE FROM memories WHERE key = ?", [key])

    @property
    def schemas(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "add_memory",
                    "description": "Add a new memory or update an existing one.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "key": {"type": "string", "description": "The unique identifier for the memory"},
                            "value": {"type": "object", "description": "The content of the memory"}
                        },
                        "required": ["key", "value"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_memory",
                    "description": "Retrieve a memory by its key.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "key": {"type": "string", "description": "The unique identifier for the memory to retrieve"}
                        },
                        "required": ["key"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_memories",
                    "description": "Search memories based on a query string.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "The search query to match against memory contents"}
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "delete_memory",
                    "description": "Delete a memory by its key.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "key": {"type": "string", "description": "The unique identifier for the memory to delete"}
                        },
                        "required": ["key"]
                    }
                }
            }
        ]
