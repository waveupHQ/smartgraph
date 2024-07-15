import logging

import pytest

from smartgraph.base import BaseActor, BaseNode, Task
from smartgraph.logging import SmartGraphLogger
from smartgraph.memory import MemoryManager


@pytest.fixture
def memory_manager():
    return MemoryManager()


@pytest.fixture
def mock_actor(memory_manager):
    class MockActor(BaseActor):
        async def perform_task(self, task, input_data, state):
            self.log.debug(f"Actor {self.name} performing task: {task.description}")
            return {"result": "Task performed"}

    return MockActor("TestActor", memory_manager)


@pytest.fixture
def mock_task():
    return Task(description="Test task")


@pytest.fixture(autouse=True)
def setup_logging(caplog):
    caplog.set_level(logging.DEBUG, logger="SmartGraph")
    yield


@pytest.mark.asyncio
async def test_base_actor_logging(mock_actor, mock_task, caplog):
    await mock_actor.perform_task(mock_task, {}, {})
    assert "Actor TestActor performing task: Test task" in caplog.text


@pytest.mark.asyncio
async def test_base_node(mock_actor, mock_task, caplog):
    node = BaseNode("test_node", mock_actor, mock_task)
    result = await node.execute({})
    assert result == {"result": "Task performed"}
    assert "Executing node test_node" in caplog.text


@pytest.mark.asyncio
async def test_base_node_error_logging(memory_manager, mock_task, caplog):
    class ErrorActor(BaseActor):
        async def perform_task(self, task, input_data, state):
            raise Exception("Test error")

    error_actor = ErrorActor("ErrorActor", memory_manager)
    node = BaseNode("error_node", error_actor, mock_task)

    with pytest.raises(Exception):
        await node.execute({})

    assert "Error executing node error_node: Test error" in caplog.text


@pytest.mark.asyncio
async def test_base_node_update_state(mock_actor, mock_task, caplog):
    node = BaseNode("test_node", mock_actor, mock_task)
    await node.update_state({"key": "value"})
    assert "Updating state of node test_node" in caplog.text
    assert "New state: {'key': 'value'}" in caplog.text
