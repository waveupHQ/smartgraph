import pytest

from smartgraph.base import BaseActor, Task
from smartgraph.exceptions import ExecutionError
from smartgraph.memory import MemoryManager
from smartgraph.state_manager import StateManager
from smartgraph.task_executor import TaskExecutor


class MockActor(BaseActor):
    async def perform_task(self, task, input_data, state):
        return {"result": f"Performed task: {task.description}"}


@pytest.fixture
def memory_manager():
    return MemoryManager()


@pytest.fixture
def mock_actor(memory_manager):
    return MockActor("MockActor", memory_manager)


@pytest.fixture
def mock_task():
    return Task(description="Test task")


@pytest.mark.asyncio
async def test_execute_task(mock_actor, mock_task):
    result = await TaskExecutor.execute_task(mock_actor, mock_task, {}, {})
    assert result == {"result": "Performed task: Test task"}


@pytest.mark.asyncio
async def test_execute_task_with_pre_post_execute(mock_actor, mock_task):
    async def pre_execute(input_data, state):
        input_data["pre"] = "pre_executed"
        return input_data

    async def post_execute(output, state):
        output["post"] = "post_executed"
        return output

    result = await TaskExecutor.execute_task(
        mock_actor, mock_task, {}, {}, pre_execute, post_execute
    )
    assert result == {"result": "Performed task: Test task", "post": "post_executed"}


@pytest.mark.asyncio
async def test_execute_task_error(memory_manager, mock_task):
    class ErrorActor(BaseActor):
        async def perform_task(self, task, input_data, state):
            raise ValueError("Test error")

    error_actor = ErrorActor("ErrorActor", memory_manager)
    with pytest.raises(ExecutionError):
        await TaskExecutor.execute_task(error_actor, mock_task, {}, {})


@pytest.mark.asyncio
async def test_execute_node_task(mock_actor, mock_task):
    class MockNode:
        def __init__(self):
            self.actor = mock_actor
            self.task = mock_task
            self.input_data = {}
            self.state_manager = StateManager()
            self.pre_execute = None
            self.post_execute = None

    mock_node = MockNode()
    result = await TaskExecutor.execute_node_task(mock_node)
    assert result == {"result": "Performed task: Test task"}
