import asyncio
from collections import deque
from time import time
from typing import Any, Dict

from pydantic import BaseModel, Field
from typing_extensions import TypedDict

from .state_manager import StateManager

# Constants
MAX_CONVERSATION_HISTORY = 1000
LONG_TERM_MEMORY_TTL = 3600


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
        self.short_term_manager = StateManager()
        self.long_term_manager = StateManager()

        # Set up reducers
        self.short_term_manager.set_reducer("last_input", lambda old, new: new)
        self.short_term_manager.set_reducer("last_response", lambda old, new: new)
        self.short_term_manager.set_reducer("context", lambda old, new: {**old, **new})

        self.long_term_manager.set_reducer("max_response_length", max)
        self.long_term_manager.set_reducer("user_preferences", lambda old, new: {**old, **new})

    async def update_short_term(self, key: str, value: Any):
        async with self.lock:
            self.short_term_manager.update_state(key, value)
            self.state.short_term[key] = self.short_term_manager.get_state(key)

    async def update_long_term(self, key: str, value: Any):
        async with self.lock:
            if key == "conversation_history":
                self.state.long_term.conversation_history.append(value)
            else:
                self.long_term_manager.update_state(key, value)
                setattr(self.state.long_term, key, self.long_term_manager.get_state(key))

            self.state.long_term.last_accessed[key] = time()

    async def get_short_term(self, key: str) -> Any:
        async with self.lock:
            return self.short_term_manager.get_state(key)

    async def get_long_term(self, key: str) -> Any:
        async with self.lock:
            if key == "conversation_history":
                return list(self.state.long_term.conversation_history)
            return self.long_term_manager.get_state(key)

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
                self.long_term_manager.update_state(key, None)
                del self.state.long_term.last_accessed[key]
