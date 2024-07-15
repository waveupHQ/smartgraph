# SmartGraph

SmartGraph is a Python library for building stateful, multi-actor applications with Large Language Models (LLMs). Built on top of the phidata framework, it offers core benefits such as cycles, controllability, and persistence.

## Features

- **Cycles**: Define flows that involve cycles, essential for most agentic architectures.
- **Controllability**: Fine-grained control over both the flow and state of your application.
- **Persistence**: Built-in persistence for advanced human-in-the-loop and memory features.

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

## Documentation

For more detailed information on how to use SmartGraph, please refer to our [documentation](link-to-your-documentation).

## Contributing

We welcome contributions! Please see our [contributing guide](link-to-contributing-guide) for details on how to get started.

## License

SmartGraph is released under the MIT License. See the LICENSE file for more details.
