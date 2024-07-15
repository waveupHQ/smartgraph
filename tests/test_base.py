import logging

import pytest

from smartgraph.base import BaseActor, BaseNode, Task
from smartgraph.logging import SmartGraphLogger


@pytest.fixture
def mock_actor():
    class MockActor(BaseActor):
        def perform_task(self, task, input_data, state):
            self.log.debug(f"Actor {self.name} performing task: {task.description}")
            return {"result": "Task performed"}

    return MockActor("TestActor")


@pytest.fixture
def mock_task():
    return Task(description="Test task")


def test_base_actor_logging(mock_actor, mock_task, caplog):
    with caplog.at_level(logging.DEBUG):
        mock_actor.perform_task(mock_task, {}, {})
    assert "Actor TestActor performing task: Test task" in caplog.text


def test_base_node(mock_actor, mock_task, caplog):
    node = BaseNode("test_node", mock_actor, mock_task)
    with caplog.at_level(logging.INFO):
        result = node.execute({})
    assert result == {"result": "Task performed"}
    assert "Executing node test_node" in caplog.text


def test_base_node_error_logging(mock_actor, mock_task, caplog):
    class ErrorActor(BaseActor):
        def perform_task(self, task, input_data, state):
            raise Exception("Test error")

    error_actor = ErrorActor("ErrorActor")
    node = BaseNode("error_node", error_actor, mock_task)

    with pytest.raises(Exception):
        with caplog.at_level(logging.ERROR):
            node.execute({})

    assert "Error executing node error_node: Test error" in caplog.text


def test_base_node_update_state(mock_actor, mock_task, caplog):
    node = BaseNode("test_node", mock_actor, mock_task)
    with caplog.at_level(logging.DEBUG):
        node.update_state({"key": "value"})
    assert "Updating state of node test_node" in caplog.text
    assert "New state: {'key': 'value'}" in caplog.text
