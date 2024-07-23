# examples/reactive_ai_component.py

import asyncio
from typing import Any, Dict

from reactivex import operators as ops

from smartgraph import ReactiveComponent, ReactiveSmartGraph
from smartgraph.logging import SmartGraphLogger

logger = SmartGraphLogger.get_logger()
logger.set_level("DEBUG")


class SimpleComponent(ReactiveComponent):
    def process(self, input_data: Any) -> Dict[str, Any]:
        logger.info(f"{self.name} processing: {input_data}")
        return {"result": f"{self.name}: {input_data}"}


class UppercaseComponent(ReactiveComponent):
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"{self.name} processing: {input_data}")
        return {"result": input_data["result"].upper()}


class MockAIAssistant(ReactiveComponent):
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"{self.name} processing: {input_data}")
        return {
            "ai_response": f"AI analysis of '{input_data['result']}': This is an uppercase message."
        }


def create_ai_graph() -> ReactiveSmartGraph:
    graph = ReactiveSmartGraph()

    # Create pipelines
    main_pipeline = graph.create_pipeline("main")
    ai_pipeline = graph.create_pipeline("ai")

    # Create components
    simple1 = SimpleComponent("SimpleComponent1")
    simple2 = SimpleComponent("SimpleComponent2")
    uppercase = UppercaseComponent("UppercaseComponent")
    ai_assistant = MockAIAssistant("MockAIAssistant")

    # Add components to pipelines
    main_pipeline.add_component(simple1)
    main_pipeline.add_component(simple2)
    main_pipeline.add_component(uppercase)
    ai_pipeline.add_component(ai_assistant)

    # Connect components within pipelines
    main_pipeline.connect_components("SimpleComponent1", "SimpleComponent2")
    main_pipeline.connect_components("SimpleComponent2", "UppercaseComponent")

    # Connect components across pipelines
    graph.connect_components("main", "SimpleComponent1", "ai", "MockAIAssistant")

    return graph


async def main():
    # Usage
    graph = create_ai_graph()
    graph.compile()

    def on_next(value):
        logger.info(f"Final result: {value}")

    def on_error(error):
        logger.error(f"An error occurred: {error}")

    def on_completed():
        logger.info("Processing completed.")

    # Example input
    input_data = "Hello, Reactive SmartGraph!"

    # Process the graph
    logger.info("Executing graph...")
    try:
        graph.execute("main", input_data).subscribe(
            on_next=on_next, on_error=on_error, on_completed=on_completed
        )

        # Wait for the execution to complete
        await asyncio.sleep(1)  # Adjust this value based on your graph's execution time
    except Exception as e:
        logger.error(f"Execution failed: {e}")

    logger.info("Execution completed")


if __name__ == "__main__":
    asyncio.run(main())
