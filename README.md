# SmartGraph

SmartGraph is a powerful Python library for building stateful, multi-component applications with Large Language Models (LLMs). Built on top of the ReactiveX for Python (reactivex) framework, SmartGraph provides a reactive, flexible, and maintainable system for creating complex data processing pipelines.

Think of SmartGraph as "Svelte for backend LLM components" - it offers a simple, reactive approach to building complex LLM-powered applications, similar to how Svelte simplifies frontend development.

## Features

- Declarative and reactive framework for defining workflows
- Support for both simple linear and complex branching workflows
- Powerful state management capabilities
- Multi-component support with easy integration of LLMs and pre-built toolkits
- Compilation step for graph validation and runtime configuration
- Comprehensive error handling and logging

## Installation

Install SmartGraph using pip:

```bash
pip install smartgraph
```

## Quick Start

Here's an example of how to use SmartGraph to create a search assistant that can answer questions using web search results:

```python
import asyncio
import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from smartgraph import ReactiveSmartGraph
from smartgraph.components import CompletionComponent
from smartgraph.tools.duckduckgo_toolkit import DuckDuckGoToolkit
from smartgraph.logging import SmartGraphLogger

# Load environment variables
load_dotenv()

# Set up logging
logger = SmartGraphLogger.get_logger()
logger.set_level("INFO")

# Create a graph and pipeline
graph = ReactiveSmartGraph()
pipeline = graph.create_pipeline("SearchAssistant")

# Initialize DuckDuckGoToolkit
ddg_toolkit = DuckDuckGoToolkit()

# Add CompletionComponent with DuckDuckGoToolkit
completion = CompletionComponent(
    name="SearchAssistant",
    model="gpt-4o-mini",
    api_key=os.getenv("OPENAI_API_KEY"),
    toolkits=[ddg_toolkit],
    system_context="You are a helpful assistant that can search the internet for information.",
)

pipeline.add_component(completion)

# Compile the graph
graph.compile()

# Create FastAPI app
app = FastAPI()

class SearchQuery(BaseModel):
    query: str

@app.post("/search")
async def search(search_query: SearchQuery):
    try:
        result = await graph.execute("SearchAssistant", {"message": search_query.query})
        return {"response": result.get("ai_response", "No response generated.")}
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred during processing")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

This example sets up a FastAPI application with a `/search` endpoint. When a POST request is sent to this endpoint with a search query, SmartGraph processes the query using the DuckDuckGoToolkit to search the web and the CompletionComponent to generate a response based on the search results.

To run this example:

1. Save the code in a file (e.g., `main.py`).
2. Set up your environment variables (OPENAI_API_KEY) in a `.env` file.
3. Install the required dependencies (`smartgraph`, `fastapi`, `uvicorn`, `python-dotenv`).
4. Run the script: `python main.py`
5. Send a POST request to `http://localhost:8000/search` with a JSON body like `{"query": "What is the capital of France?"}`.

This example demonstrates how SmartGraph can be used to create a simple API for a search assistant, showcasing its ability to integrate different components and toolkits in a reactive pipeline.

## Documentation

For more detailed information on how to use SmartGraph, please refer to our [documentation](https:smartgraph.waveup.dev).

## Core Concepts

- **ReactiveSmartGraph**: The main class representing the entire graph structure.
- **Pipeline**: A sequence of connected components that process data.
- **ReactiveComponent**: The base class for all components in SmartGraph.
- **CompletionComponent**: A component for integrating Large Language Models.
- **Toolkits**: Pre-built components for common tasks like web searches and memory management.

## Advanced Features

- Custom component creation
- Complex branching workflows
- Asynchronous API integration
- Caching and retry mechanisms
- Input validation
- Graph visualization

## Contributing

We welcome contributions! Please see our [contributing guide](/contributing) for details on how to get started.

## License

SmartGraph is released under the MIT License. See the [LICENSE](LICENSE) file for more details.

## Support

If you encounter any issues or have questions, please file an issue on the [GitHub issue tracker](https://github.com/waveupHQ/smartgraph/issues).

## Acknowledgements

SmartGraph is built on top of the excellent [ReactiveX for Python](https://github.com/ReactiveX/RxPY) library. We're grateful to the ReactiveX community for their work.
