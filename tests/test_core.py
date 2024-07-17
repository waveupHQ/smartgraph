import pytest

from smartgraph import Edge, HumanActor, MemoryManager, Node, SmartGraph, Task


@pytest.mark.asyncio
async def test_smartgraph_execution_termination():
    memory_manager = MemoryManager()
    graph = SmartGraph(memory_manager=memory_manager)

    # Create nodes
    start_node = Node(
        id="start", actor=HumanActor("User", memory_manager), task=Task(description="Start")
    )
    end_node = Node(
        id="end", actor=HumanActor("User", memory_manager), task=Task(description="End")
    )

    # Add nodes to the graph
    graph.add_node(start_node)
    graph.add_node(end_node)

    # Add an edge with a condition that always evaluates to False
    graph.add_edge(Edge(source_id="start", target_id="end", conditions=[lambda data: False]))

    # Execute the graph
    final_state, should_exit = await graph.execute("start", {}, "test_thread")

    # Assert that the execution terminates
    assert should_exit is True
