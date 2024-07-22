# tests/test_core.py

import logging
from unittest.mock import AsyncMock, MagicMock

import pytest
from reactivex.subject import BehaviorSubject, Subject

from smartgraph.component import ReactiveAIComponent
from smartgraph.core import ReactiveEdge, ReactiveNode, ReactiveSmartGraph, StateManager
from smartgraph.exceptions import ExecutionError, GraphStructureError


# Utility class for testing
class SimpleComponent(ReactiveAIComponent):
    async def process(self, input_data):
        return f"Processed: {input_data}"


@pytest.fixture
def simple_component():
    return SimpleComponent("SimpleComponent")


@pytest.fixture
def mock_component():
    component = MagicMock(spec=ReactiveAIComponent)
    component.process = AsyncMock()
    component.input = Subject()
    component.output = Subject()
    return component


class TestStateManager:
    @pytest.fixture
    def state_manager(self):
        return StateManager()

    def test_global_state(self, state_manager):
        state_manager.update_global_state({"key": "value"})
        assert state_manager.get_global_state().value == {"key": "value"}

    def test_node_state(self, state_manager):
        state_manager.update_node_state("node1", {"key": "value"})
        assert state_manager.get_node_state("node1").value == {"key": "value"}

    def test_combined_state(self, state_manager):
        state_manager.update_global_state({"global_key": "global_value"})
        state_manager.update_node_state("node1", {"node_key": "node_value"})
        combined_state = state_manager.get_combined_state("node1")
        assert combined_state == {"global_key": "global_value", "node_key": "node_value"}


class TestReactiveNode:
    @pytest.fixture
    def simple_component(self):
        class SimpleComponent(ReactiveAIComponent):
            async def process(self, input_data):
                return f"Processed: {input_data}"

        return SimpleComponent("SimpleComponent")

    @pytest.fixture
    def state_manager(self):
        return StateManager()

    @pytest.fixture
    def node_with_state(self, simple_component, state_manager):
        return ReactiveNode("test_node", simple_component, state_manager)

    @pytest.fixture
    def node_without_state(self, simple_component):
        return ReactiveNode("test_node", simple_component)

    def test_node_initialization(self, node_with_state, node_without_state):
        assert node_with_state.id == "test_node"
        assert isinstance(node_with_state.component, ReactiveAIComponent)
        assert node_with_state.state_manager is not None

        assert node_without_state.id == "test_node"
        assert isinstance(node_without_state.component, ReactiveAIComponent)
        assert node_without_state.state_manager is None

    @pytest.mark.asyncio
    async def test_node_processing_with_state(self, node_with_state):
        result = await node_with_state.process("test_input")
        assert result == "Processed: test_input"
        state = node_with_state.get_state()
        assert state is not None
        assert state.get("last_input") == "test_input"
        assert state.get("last_output") == "Processed: test_input"

    @pytest.mark.asyncio
    async def test_node_processing_without_state(self, node_without_state):
        result = await node_without_state.process("test_input")
        assert result == "Processed: test_input"
        assert node_without_state.get_state() is None

    def test_update_state(self, node_with_state, node_without_state):
        node_with_state.update_state({"test_key": "test_value"})
        state = node_with_state.get_state()
        assert state is not None
        assert state.get("test_key") == "test_value"

        node_without_state.update_state({"test_key": "test_value"})
        assert node_without_state.get_state() is None


class TestReactiveSmartGraph:
    @pytest.fixture
    def graph(self):
        return ReactiveSmartGraph()

    @pytest.fixture
    def simple_component(self):
        class SimpleComponent(ReactiveAIComponent):
            async def process(self, input_data):
                return f"Processed: {input_data}"

        return SimpleComponent("SimpleComponent")

    def test_add_node(self, graph, simple_component):
        node = ReactiveNode("test_node", simple_component)
        graph.add_node(node)
        assert "test_node" in graph.nodes

    def test_add_duplicate_node(self, graph, simple_component):
        node = ReactiveNode("test_node", simple_component)
        graph.add_node(node)
        with pytest.raises(GraphStructureError):
            graph.add_node(node)

    def test_add_edge(self, graph, simple_component):
        node1 = ReactiveNode("node1", simple_component)
        node2 = ReactiveNode("node2", simple_component)
        graph.add_node(node1)
        graph.add_node(node2)
        edge = ReactiveEdge("node1", "node2")
        graph.add_edge(edge)
        assert graph.graph.has_edge("node1", "node2")

    @pytest.mark.asyncio
    async def test_graph_execution(self, graph, simple_component):
        node1 = ReactiveNode("node1", simple_component)
        node2 = ReactiveNode("node2", simple_component)
        graph.add_node(node1)
        graph.add_node(node2)
        graph.add_edge(ReactiveEdge("node1", "node2"))

        result = await graph.execute("node1", "test_input")
        assert result == "Processed: Processed: test_input"

        # Check if global state was updated
        global_state = graph.get_global_state()
        assert global_state.get("execution_input") == "test_input"
        assert "execution_result" in global_state

    @pytest.mark.asyncio
    async def test_graph_execution_error(self, graph):
        mock_component = MagicMock(spec=ReactiveAIComponent)
        mock_component.input = Subject()
        mock_component.output = Subject()
        mock_component.process = AsyncMock(side_effect=ValueError("Test error"))

        node = ReactiveNode("error_node", mock_component)
        graph.add_node(node)

        with pytest.raises(ExecutionError) as excinfo:
            await graph.execute("error_node", "test_input")
        assert "Error during execution: Test error" in str(excinfo.value)

    def test_graph_state_management(self, graph, simple_component, caplog):
        caplog.set_level(logging.DEBUG)

        node1 = ReactiveNode("node1", simple_component)
        node2 = ReactiveNode("node2", simple_component)
        graph.add_node(node1)
        graph.add_node(node2)

        graph.update_global_state({"global_key": "global_value"})
        assert graph.get_global_state().get("global_key") == "global_value"

        node1_state = graph.get_node("node1").get_state()
        assert node1_state is not None
        assert "global_key" in node1_state
        assert node1_state["global_key"] == "global_value"

        # Test node-specific state
        graph.get_node("node1").update_state({"node_key": "node_value"})
        updated_node1_state = graph.get_node("node1").get_state()
        assert updated_node1_state is not None
        assert updated_node1_state["node_key"] == "node_value"
        assert updated_node1_state["global_key"] == "global_value"

        # Ensure node2 doesn't have node1's specific state
        node2_state = graph.get_node("node2").get_state()
        assert node2_state is not None
        assert "global_key" in node2_state
        assert "node_key" not in node2_state

        # Check that state changes were logged
        assert any(
            "State change: ('global', {'global_key': 'global_value'})" in record.message
            for record in caplog.records
        )
        assert any(
            "State change: ('node1', {'node_key': 'node_value'})" in record.message
            for record in caplog.records
        )


class TestReactiveEdge:
    def test_edge_condition_true(self):
        edge = ReactiveEdge("source", "target", condition=lambda x: x > 0)
        assert edge.is_valid(5) == True

    def test_edge_condition_false(self):
        edge = ReactiveEdge("source", "target", condition=lambda x: x > 0)
        assert edge.is_valid(-5) == False

    def test_edge_default_condition(self):
        edge = ReactiveEdge("source", "target")
        assert edge.is_valid(None) == True


class TestReactiveAIComponent:
    @pytest.fixture
    def component(self):
        class TestComponent(ReactiveAIComponent):
            async def process(self, input_data):
                return f"Processed: {input_data}"

        return TestComponent("TestComponent")

    @pytest.mark.asyncio
    async def test_component_processing(self, component):
        result = await component.process("test_input")
        assert result == "Processed: test_input"

    def test_component_state_management(self, component):
        component.create_state("test_key", "initial_value")
        component.update_state("test_key", "test_value")
        state = component.get_state("test_key")
        assert state is not None
        assert state.value == "test_value"

    @pytest.mark.asyncio
    async def test_component_input_output_stream(self, component):
        output_results = []
        component.output.subscribe(lambda x: output_results.append(x))

        await component._process_input("test_input")
        assert output_results == ["Processed: test_input"]


if __name__ == "__main__":
    pytest.main([__file__])
