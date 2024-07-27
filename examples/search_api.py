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
