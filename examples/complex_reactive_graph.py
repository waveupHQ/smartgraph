# examples/complex_reactive_graph.py

import asyncio
from typing import Any, List
import logging

from smartgraph import ReactiveAIComponent, ReactiveEdge, ReactiveNode, ReactiveSmartGraph
from smartgraph.components import AggregatorComponent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleComponent(ReactiveAIComponent):
    async def process(self, input_data: Any) -> Any:
        logger.info(f"{self.name} processing: {input_data}")
        await asyncio.sleep(1)
        return f"Processed by {self.name}: {input_data}"

class UppercaseComponent(ReactiveAIComponent):
    async def process(self, input_data: Any) -> Any:
        logger.info(f"{self.name} processing: {input_data}")
        await asyncio.sleep(1)
        return str(input_data).upper()


class DecisionComponent(ReactiveAIComponent):
    async def process(self, input_data: Any) -> Any:
        logger.info(f"{self.name} deciding on: {input_data}")
        await asyncio.sleep(1)
        decision = "path_a" if "UPPERCASE" in input_data else "path_b"
        return f"Decision: {decision} for input: {input_data}"

class MockAIAssistant(ReactiveAIComponent):
    async def process(self, input_data: Any) -> Any:
        logger.info(f"{self.name} processing: {input_data}")
        await asyncio.sleep(2)
        return f"AI analysis: The input contains a decision ({input_data.split(':')[1].split()[0]}) based on aggregated data."

class SummaryComponent(ReactiveAIComponent):
    async def process(self, input_data: Any) -> Any:
        logger.info(f"{self.name} summarizing: {input_data}")
        await asyncio.sleep(1)
        decision = input_data.split(':')[1].split()[0]
        original_input = input_data.split('Aggregated result:')[-1].strip()
        return f"Summary: Decision '{decision}' was made based on input containing '{original_input}'"

async def main():
    graph = ReactiveSmartGraph()

    # Create components
    simple1 = SimpleComponent("SimpleComponent1")
    simple2 = SimpleComponent("SimpleComponent2")
    uppercase = UppercaseComponent("UppercaseComponent")
    aggregator = AggregatorComponent("AggregatorComponent")
    decision = DecisionComponent("DecisionComponent")
    ai_assistant = MockAIAssistant("MockAIAssistant")
    summary = SummaryComponent("SummaryComponent")

    # Create nodes
    node1 = ReactiveNode("node1", simple1)
    node2a = ReactiveNode("node2a", simple2)
    node2b = ReactiveNode("node2b", uppercase)
    node3 = ReactiveNode("node3", aggregator)
    node4 = ReactiveNode("node4", decision)
    node5a = ReactiveNode("node5a", ai_assistant)
    node5b = ReactiveNode("node5b", summary)

    # Add nodes to the graph
    for node in [node1, node2a, node2b, node3, node4, node5a, node5b]:
        graph.add_node(node)

    # Add edges
    graph.add_edge(ReactiveEdge("node1", "node2a"))
    graph.add_edge(ReactiveEdge("node1", "node2b"))
    graph.add_edge(ReactiveEdge("node2a", "node3"))
    graph.add_edge(ReactiveEdge("node2b", "node3"))
    graph.add_edge(ReactiveEdge("node3", "node4"))
    graph.add_edge(ReactiveEdge("node4", "node5a", lambda data: "path_a" in data))
    graph.add_edge(ReactiveEdge("node4", "node5b", lambda data: "path_b" in data))

    # Execute the graph
    logger.info("Executing graph...")
    try:
        result = await graph.execute("node1", "Hello, Reactive SmartGraph!")
        logger.info(f"Execution result: {result}")
    except asyncio.TimeoutError:
        logger.error("Execution timed out")
    except Exception as e:
        logger.error(f"Execution failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
