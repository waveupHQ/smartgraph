import pytest

from smartgraph.exceptions import (
    ConfigurationError,
    ExecutionError,
    GraphStructureError,
    MemoryError,
    SmartGraphException,
    ValidationError,
)


def test_smartgraph_exception():
    with pytest.raises(SmartGraphException) as excinfo:
        raise SmartGraphException("Test exception")
    assert str(excinfo.value) == "Test exception"


def test_execution_error():
    with pytest.raises(ExecutionError) as excinfo:
        raise ExecutionError("Test execution error", node_id="test_node")
    assert "Execution error" in str(excinfo.value)
    assert "test_node" in str(excinfo.value)


def test_configuration_error():
    with pytest.raises(ConfigurationError) as excinfo:
        raise ConfigurationError("Test config error", component="test_component")
    assert "Configuration error" in str(excinfo.value)
    assert "test_component" in str(excinfo.value)


def test_validation_error():
    with pytest.raises(ValidationError) as excinfo:
        raise ValidationError("Test validation error", field="test_field")
    assert "Validation error" in str(excinfo.value)
    assert "test_field" in str(excinfo.value)


def test_memory_error():
    with pytest.raises(MemoryError) as excinfo:
        raise MemoryError("Test memory error", memory_type="short_term")
    assert "Memory error" in str(excinfo.value)
    assert "short_term" in str(excinfo.value)


def test_graph_structure_error():
    with pytest.raises(GraphStructureError) as excinfo:
        raise GraphStructureError("Test graph structure error")
    assert "Graph structure error" in str(excinfo.value)
