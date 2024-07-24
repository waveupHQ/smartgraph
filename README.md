# SmartGraph

SmartGraph is a Python library for building stateful, multi-actor applications with Large Language Models (LLMs). It is built on top of the ReactiveX for Python (reactivex) framework and aims to provide a reactive, flexible, and maintainable system for creating complex data processing pipelines.

## Features

Key features of SmartGraph include:

- Declarative and reactive framework for defining workflows
- Support for both simple linear and complex branching workflows
- Powerful state management capabilities
- Multi-component support with easy integration of LLMs and pre-built toolkits
- Compilation step for graph validation and runtime configuration

## Principles

1. Declarative and reactive framework design
2. Simplicity in design and usage
3. Powerful and flexible state management
4. Multi-component support with easy extensibility
5. Seamless integration with LLMs and pre-built toolkits
6. Comprehensive error handling and logging
7. Graph validation and safety through compilation step
8. Support for both simple and complex workflow structures

## Installation

```bash
pip install smartgraph
```

## Quick Start

Here's a simple example of how to use SmartGraph:

```python

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
