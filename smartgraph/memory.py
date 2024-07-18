import asyncio
from typing import Any, Dict, List
import aiofiles
import json

class ShortTermMemory:
    def __init__(self):
        self.last_input: str = ""
        self.last_response: str = ""
        self.context: Dict[str, Any] = {}
        self.conversation_history: List[str] = []

class LongTermMemory:
    def __init__(self):
        self.facts: List[str] = []
        self.user_preferences: Dict[str, Any] = {}

class MemoryState:
    def __init__(self):
        self.short_term = ShortTermMemory()
        self.long_term = LongTermMemory()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "short_term": {
                "last_input": self.short_term.last_input,
                "last_response": self.short_term.last_response,
                "context": self.short_term.context,
                "conversation_history": self.short_term.conversation_history
            },
            "long_term": {
                "facts": self.long_term.facts,
                "user_preferences": self.long_term.user_preferences
            }
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryState':
        state = cls()
        state.short_term.last_input = data["short_term"]["last_input"]
        state.short_term.last_response = data["short_term"]["last_response"]
        state.short_term.context = data["short_term"]["context"]
        state.short_term.conversation_history = data["short_term"]["conversation_history"]
        state.long_term.facts = data["long_term"]["facts"]
        state.long_term.user_preferences = data["long_term"]["user_preferences"]
        return state

class MemoryManager:
    def __init__(self, memory_file: str = "memory.md"):
        self.state = MemoryState()
        self.memory_file = memory_file
        self.lock = asyncio.Lock()

    async def update_short_term(self, key: str, value: Any):
        async with self.lock:
            setattr(self.state.short_term, key, value)

    async def update_long_term(self, key: str, value: Any):
        async with self.lock:
            if key == "facts":
                self.state.long_term.facts.append(value)
            elif key == "user_preferences":
                self.state.long_term.user_preferences.update(value)
            await self._save_long_term_memory()

    async def get_short_term(self, key: str) -> Any:
        async with self.lock:
            return getattr(self.state.short_term, key)

    async def get_long_term(self, key: str) -> Any:
        async with self.lock:
            return getattr(self.state.long_term, key)

    async def update_conversation_history(self, message: str, is_user: bool = True):
        async with self.lock:
            prefix = "User: " if is_user else "AI: "
            self.state.short_term.conversation_history.append(f"{prefix}{message}")
            # Keep only the last 10 messages
            self.state.short_term.conversation_history = self.state.short_term.conversation_history[-10:]

    async def get_conversation_history(self) -> List[str]:
        async with self.lock:
            return self.state.short_term.conversation_history

    async def _save_long_term_memory(self):
        async with aiofiles.open(self.memory_file, "w") as f:
            await f.write("# Long-Term Memory\n\n")
            await f.write("## Facts\n\n")
            for fact in self.state.long_term.facts:
                await f.write(f"- {fact}\n")
            await f.write("\n## User Preferences\n\n")
            for key, value in self.state.long_term.user_preferences.items():
                await f.write(f"- {key}: {value}\n")

    async def load_long_term_memory(self):
        try:
            async with aiofiles.open(self.memory_file, "r") as f:
                content = await f.read()
                sections = content.split("##")
                for section in sections:
                    if section.strip().startswith("Facts"):
                        self.state.long_term.facts = [line.strip()[2:] for line in section.split("\n") if line.strip().startswith("- ")]
                    elif section.strip().startswith("User Preferences"):
                        self.state.long_term.user_preferences = dict(line.strip()[2:].split(": ") for line in section.split("\n") if line.strip().startswith("- "))
        except FileNotFoundError:
            # If the file doesn't exist, we'll start with an empty long-term memory
            pass

    async def cleanup_long_term_memory(self):
        # This method can be implemented to remove old or irrelevant memories
        # For now, we'll just keep it as a placeholder
        pass