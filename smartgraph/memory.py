# smartgraph/memory.py

from typing import Any, Callable, Dict, List

from pydantic import BaseModel, Field
from typing_extensions import TypedDict


class ShortTermMemory(TypedDict):
    last_input: str
    last_response: str
    context: Dict[str, Any]


class LongTermMemory(BaseModel):
    conversation_history: List[str] = Field(default_factory=list)
    max_response_length: int = 0
    user_preferences: Dict[str, Any] = Field(default_factory=dict)


class MemoryState(BaseModel):
    short_term: ShortTermMemory = Field(
        default_factory=lambda: ShortTermMemory(last_input="", last_response="", context={})
    )
    long_term: LongTermMemory = Field(default_factory=LongTermMemory)


class MemoryManager:
    def __init__(self):
        self.state = MemoryState()

    def update_short_term(self, key: str, value: Any):
        if key in self.state.short_term:
            reducer = self.short_term_reducers.get(key, lambda old, new: new)
            self.state.short_term[key] = reducer(self.state.short_term[key], value)
        else:
            self.state.short_term[key] = value

    def update_long_term(self, key: str, value: Any):
        if hasattr(self.state.long_term, key):
            reducer = self.long_term_reducers.get(key, lambda old, new: new)
            setattr(self.state.long_term, key, reducer(getattr(self.state.long_term, key), value))
        else:
            setattr(self.state.long_term, key, value)

    def get_short_term(self, key: str) -> Any:
        return self.state.short_term.get(key)

    def get_long_term(self, key: str) -> Any:
        return getattr(self.state.long_term, key)

    short_term_reducers: Dict[str, Callable] = {
        "last_input": lambda old, new: new,
        "last_response": lambda old, new: new,
        "context": lambda old, new: {**old, **new},
    }
    long_term_reducers: Dict[str, Callable] = {
        "conversation_history": lambda old, new: old + [new],
        "max_response_length": max,
        "user_preferences": lambda old, new: {**old, **new},
    }
