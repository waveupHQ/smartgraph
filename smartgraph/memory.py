import asyncio
from collections import deque
from time import time
from typing import Any, Callable, Dict, List

from pydantic import BaseModel, Field
from typing_extensions import TypedDict

# Constants
MAX_CONVERSATION_HISTORY = 1000  # Maximum number of entries in conversation history
LONG_TERM_MEMORY_TTL = 3600  # Time-to-live for long-term memory items (in seconds)


class ShortTermMemory(TypedDict):
    last_input: str
    last_response: str
    context: Dict[str, Any]


class LongTermMemory(BaseModel):
    conversation_history: deque = Field(
        default_factory=lambda: deque(maxlen=MAX_CONVERSATION_HISTORY)
    )
    max_response_length: int = 0
    user_preferences: Dict[str, Any] = Field(default_factory=dict)
    last_accessed: Dict[str, float] = Field(default_factory=dict)


class MemoryState(BaseModel):
    short_term: ShortTermMemory = Field(
        default_factory=lambda: ShortTermMemory(last_input="", last_response="", context={})
    )
    long_term: LongTermMemory = Field(default_factory=LongTermMemory)


class MemoryManager:
    def __init__(self):
        self.state = MemoryState()
        self.lock = asyncio.Lock()

    async def update_short_term(self, key: str, value: Any):
        async with self.lock:
            if key in self.state.short_term:
                reducer = self.short_term_reducers.get(key, lambda old, new: new)
                self.state.short_term[key] = reducer(self.state.short_term[key], value)
            else:
                self.state.short_term[key] = value

    async def update_long_term(self, key: str, value: Any):
        async with self.lock:
            if key == "conversation_history":
                self.state.long_term.conversation_history.append(value)
            elif hasattr(self.state.long_term, key):
                reducer = self.long_term_reducers.get(key, lambda old, new: new)
                setattr(
                    self.state.long_term, key, reducer(getattr(self.state.long_term, key), value)
                )
            else:
                setattr(self.state.long_term, key, value)

            self.state.long_term.last_accessed[key] = time()

    async def get_short_term(self, key: str) -> Any:
        async with self.lock:
            return self.state.short_term.get(key)

    async def get_long_term(self, key: str) -> Any:
        async with self.lock:
            if key == "conversation_history":
                return list(self.state.long_term.conversation_history)
            return getattr(self.state.long_term, key)

    async def cleanup_long_term_memory(self):
        async with self.lock:
            current_time = time()
            keys_to_remove = []
            for key, last_accessed in self.state.long_term.last_accessed.items():
                if current_time - last_accessed > LONG_TERM_MEMORY_TTL:
                    keys_to_remove.append(key)

            for key in keys_to_remove:
                if hasattr(self.state.long_term, key):
                    delattr(self.state.long_term, key)
                del self.state.long_term.last_accessed[key]

    short_term_reducers: Dict[str, Callable] = {
        "last_input": lambda old, new: new,
        "last_response": lambda old, new: new,
        "context": lambda old, new: {**old, **new},
    }
    long_term_reducers: Dict[str, Callable] = {
        "max_response_length": max,
        "user_preferences": lambda old, new: {**old, **new},
    }
