import pytest
from datetime import datetime, timedelta
from smartgraph.tools.duck_memory_toolkit import DuckMemoryToolkit

@pytest.fixture
def duck_memory_toolkit():
    return DuckMemoryToolkit(":memory:")

@pytest.mark.asyncio
async def test_duck_memory_toolkit(duck_memory_toolkit):
    # Test adding and retrieving a memory
    await duck_memory_toolkit.add_memory("test_key", {"value": "test_value"})
    result = await duck_memory_toolkit.get_memory("test_key")
    assert result == {"value": "test_value"}

    # Test searching memories
    search_results = await duck_memory_toolkit.search_memories("test")
    assert len(search_results) == 1
    assert search_results[0]["key"] == "test_key"
    assert search_results[0]["value"] == {"value": "test_value"}
    assert isinstance(search_results[0]["created_at"], str)
    assert isinstance(search_results[0]["updated_at"], str)

    # Test updating a memory
    await duck_memory_toolkit.add_memory("test_key", {"value": "updated_value"})
    updated_result = await duck_memory_toolkit.get_memory("test_key")
    assert updated_result == {"value": "updated_value"}

    # Test deleting a memory
    await duck_memory_toolkit.delete_memory("test_key")
    result = await duck_memory_toolkit.get_memory("test_key")
    assert result is None

def test_memory_toolkit_schemas(duck_memory_toolkit):
    schemas = duck_memory_toolkit.schemas
    assert len(schemas) == 4

    # Check add_memory schema
    add_memory_schema = next(s for s in schemas if s["function"]["name"] == "add_memory")
    assert add_memory_schema["type"] == "function"
    assert "key" in add_memory_schema["function"]["parameters"]["properties"]
    assert "value" in add_memory_schema["function"]["parameters"]["properties"]

    # Check get_memory schema
    get_memory_schema = next(s for s in schemas if s["function"]["name"] == "get_memory")
    assert get_memory_schema["type"] == "function"
    assert "key" in get_memory_schema["function"]["parameters"]["properties"]

    # Check search_memories schema
    search_memories_schema = next(s for s in schemas if s["function"]["name"] == "search_memories")
    assert search_memories_schema["type"] == "function"
    assert "query" in search_memories_schema["function"]["parameters"]["properties"]

    # Check delete_memory schema
    delete_memory_schema = next(s for s in schemas if s["function"]["name"] == "delete_memory")
    assert delete_memory_schema["type"] == "function"
    assert "key" in delete_memory_schema["function"]["parameters"]["properties"]

@pytest.mark.asyncio
async def test_memory_toolkit_functions(duck_memory_toolkit):
    functions = duck_memory_toolkit.functions
    assert "add_memory" in functions
    assert "get_memory" in functions
    assert "search_memories" in functions
    assert "delete_memory" in functions

    # Test function calls
    await functions["add_memory"]("test_key", {"value": "test_value"})
    result = await functions["get_memory"]("test_key")
    assert result == {"value": "test_value"}

    search_results = await functions["search_memories"]("test")
    assert len(search_results) == 1

    await functions["delete_memory"]("test_key")
    result = await functions["get_memory"]("test_key")
    assert result is None
