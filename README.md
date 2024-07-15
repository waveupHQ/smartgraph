# SmartGraph

SmartGraph is a Python library for building stateful, multi-actor applications with Large Language Models (LLMs). Built on top of the phidata framework, it offers core benefits such as cycles, controllability, and persistence.

## Features

- **Cycles**: Define flows that involve cycles, essential for most agentic architectures.
- **Controllability**: Fine-grained control over both the flow and state of your application.
- **Persistence**: Built-in persistence for advanced human-in-the-loop and memory features.
- **Error Handling**: Robust exception hierarchy for precise error management.
- **Logging**: Comprehensive logging system for debugging and monitoring.

## Installation

```bash
pip install smartgraph
```

## Quick Start

Here's a simple example of how to use SmartGraph:

```python
from smartgraph import SmartGraph, Node, Edge, HumanActor, AIActor
from phi.assistant import Assistant

# Create actors
human_actor = HumanActor("User")
ai_actor = AIActor("AI", Assistant(name="AI Assistant"))

# Create nodes
start_node = Node("start", human_actor, {"description": "Start the conversation"})
ai_response_node = Node("ai_response", ai_actor, {"prompt": "Respond to: {user_input}"})
human_feedback_node = Node("human_feedback", human_actor, {"description": "Provide feedback on AI's response"})

# Create edges
edge1 = Edge(start_node, ai_response_node)
edge2 = Edge(ai_response_node, human_feedback_node)
edge3 = Edge(human_feedback_node, ai_response_node, condition=lambda data: data['response'].lower() != 'exit')

# Create and execute SmartGraph
graph = SmartGraph()
for node in [start_node, ai_response_node, human_feedback_node]:
    graph.add_node(node)
for edge in [edge1, edge2, edge3]:
    graph.add_edge(edge)

final_output = graph.execute("start", {"user_input": "Hello, AI!"})
print("Final output:", final_output)
```

## Error Handling and Logging

SmartGraph provides a robust error handling system and comprehensive logging capabilities to help you debug and monitor your applications.

### Exception Hierarchy

SmartGraph defines a set of custom exceptions to handle various error scenarios:

- `SmartGraphException`: Base exception for all SmartGraph-related errors.
- `ExecutionError`: Raised when there's an error during the execution of a node or workflow.
- `ConfigurationError`: Raised when there's an error in the configuration of SmartGraph components.
- `ValidationError`: Raised when there's a validation error in inputs or outputs.
- `MemoryError`: Raised when there's an error related to memory management.
- `GraphStructureError`: Raised when there's an error in the structure of the SmartGraph.

Example usage:

```python
from smartgraph.exceptions import ExecutionError

try:
    # Some SmartGraph operation
    pass
except ExecutionError as e:
    print(f"An error occurred during execution: {e}")
```

### Logging

SmartGraph uses a centralized logging system through the `SmartGraphLogger` class. This logger is automatically used by SmartGraph components, but you can also use it in your own code:

```python
from smartgraph.logging import SmartGraphLogger

logger = SmartGraphLogger.get_logger()

logger.info("Starting the application")
logger.debug("Detailed debug information")
logger.warning("A warning occurred")
logger.error("An error occurred")
```

You can configure the logging level and add additional file handlers:

```python
logger.set_level("DEBUG")
logger.add_file_handler("app.log", "INFO")
```

## Documentation

For more detailed information on how to use SmartGraph, please refer to our [documentation](link-to-your-documentation).

## Contributing

We welcome contributions! Please see our [contributing guide](link-to-contributing-guide) for details on how to get started.

## License

SmartGraph is released under the MIT License. See the LICENSE file for more details.
