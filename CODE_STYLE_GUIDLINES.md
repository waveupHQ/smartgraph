# SmartGraph Code Style Guidelines

This document outlines the coding standards and best practices for contributing to the SmartGraph project. Following these guidelines helps maintain consistency across the codebase and makes it easier for contributors and maintainers to read, understand, and modify the code.

## General Guidelines

1. Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guide for Python code.
2. Use 4 spaces for indentation (no tabs).
3. Keep lines to a maximum of 100 characters.
4. Use UTF-8 encoding for all Python files.
5. End files with a single newline character.

## Naming Conventions

- Use `snake_case` for function and variable names.
- Use `PascalCase` for class names.
- Use `UPPER_CASE` for constants.
- Prefix private attributes and methods with a single underscore (`_`).

Examples:

```python
def calculate_total_cost(items):
    pass

class GraphNode:
    pass

MAX_RETRY_ATTEMPTS = 3

class MyClass:
    def __init__(self):
        self._private_attribute = None

    def _private_method(self):
        pass
```

## Imports

1. Group imports in the following order:
   - Standard library imports
   - Third-party library imports
   - Local application imports
2. Use absolute imports when possible.
3. Avoid wildcard imports (`from module import *`).

Example:

```python
import os
from typing import List, Dict

import networkx as nx

from smartgraph.core import Node, Edge
from smartgraph.utils import calculate_graph_metrics
```

## Type Hints

Use type hints for function arguments and return values:

```python
def process_data(input_data: Dict[str, Any]) -> List[float]:
    pass
```

## Documentation

1. Use docstrings for all public modules, functions, classes, and methods.
2. Follow the [Google style](https://github.com/google/styleguide/blob/gh-pages/pyguide.md#38-comments-and-docstrings) for docstrings.
3. Include examples in docstrings where appropriate.

Example:

```python
def calculate_node_centrality(graph: nx.Graph, node_id: str) -> float:
    """
    Calculate the centrality of a node in the graph.

    Args:
        graph (nx.Graph): The input graph.
        node_id (str): The ID of the node to calculate centrality for.

    Returns:
        float: The centrality score of the node.

    Raises:
        ValueError: If the node_id is not present in the graph.

    Example:
        >>> G = nx.Graph()
        >>> G.add_edges_from([(1, 2), (1, 3), (2, 3), (3, 4)])
        >>> calculate_node_centrality(G, 3)
        0.6666666666666666
    """
    pass
```

## Error Handling

1. Use specific exception types when raising exceptions.
2. Handle exceptions at the appropriate level of abstraction.
3. Use context managers (`with` statements) for resource management.

Example:

```python
from smartgraph.exceptions import NodeNotFoundError

def process_node(graph, node_id):
    try:
        node = graph.get_node(node_id)
    except NodeNotFoundError:
        logger.warning(f"Node {node_id} not found in the graph")
        return None

    # Process the node
    pass
```

## Testing

1. Write unit tests for all new functionality.
2. Use `pytest` for writing and running tests.
3. Aim for high test coverage, especially for critical components.

Example:

```python
import pytest
from smartgraph import Graph, Node

def test_add_node():
    graph = Graph()
    node = Node("test_node")
    graph.add_node(node)
    assert "test_node" in graph.nodes
    assert graph.get_node("test_node") == node
```

## Comments

1. Write clear, concise comments to explain complex logic.
2. Avoid obvious comments that don't add value.
3. Keep comments up-to-date with code changes.

## Formatting

1. Use a consistent formatting style throughout the codebase.
2. Consider using tools like `black` for automatic code formatting.
3. Use `isort` to sort and organize imports.

## Version Control

1. Write clear, descriptive commit messages.
2. Use feature branches for developing new features or fixing bugs.
3. Keep pull requests focused on a single feature or bug fix.

## Performance Considerations

1. Be mindful of performance implications, especially for graph operations.
2. Use profiling tools to identify and optimize bottlenecks.
3. Consider using appropriate data structures and algorithms for efficiency.

By following these guidelines, you'll help maintain a high-quality, consistent codebase for SmartGraph. Remember that these guidelines are not exhaustive, and when in doubt, prioritize readability and maintainability.
