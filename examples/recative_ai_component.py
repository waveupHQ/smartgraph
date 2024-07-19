# examples/reactive_ai_component.py

import asyncio
import logging
from typing import Any

from smartgraph import (
    ReactiveAIComponent,
    ReactiveAssistantConversation,
    ReactiveEdge,
    ReactiveNode,
    ReactiveSmartGraph,
)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class SimpleComponent(ReactiveAIComponent):
    async def process(self, input_data: Any) -> Any:
        logger.info(f"{self.name} processing: {input_data}")
        await asyncio.sleep(1)  # Simulate some processing time
        return f"Processed by {self.name}: {input_data}"


class UppercaseComponent(ReactiveAIComponent):
    async def process(self, input_data: Any) -> Any:
        logger.info(f"{self.name} processing: {input_data}")
        await asyncio.sleep(1)  # Simulate some processing time
        return str(input_data).upper()


async def main():
    graph = ReactiveSmartGraph()

    # Create components
    simple1 = SimpleComponent("SimpleComponent1")
    simple2 = SimpleComponent("SimpleComponent2")
    uppercase = UppercaseComponent("UppercaseComponent")

    # Create a mock AI assistant component for testing
    class MockAIAssistant(ReactiveAIComponent):
        async def process(self, input_data: Any) -> Any:
            logger.info(f"{self.name} processing: {input_data}")
            await asyncio.sleep(2)  # Simulate AI processing time
            return f"AI response to: {input_data}"

    assistant = MockAIAssistant("MockAIAssistant")

    # Create nodes
    node1 = ReactiveNode("node1", simple1)
    node2 = ReactiveNode("node2", simple2)
    node3 = ReactiveNode("node3", uppercase)
    node4 = ReactiveNode("node4", assistant)

    # Add nodes to the graph
    for node in [node1, node2, node3, node4]:
        graph.add_node(node)

    # Add edges
    graph.add_edge(ReactiveEdge("node1", "node2"))
    graph.add_edge(ReactiveEdge("node2", "node3"))
    graph.add_edge(ReactiveEdge("node3", "node4"))

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
