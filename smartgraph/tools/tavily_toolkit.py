# smartgraph/tools/tavily_toolkit.py

import asyncio
import json
from functools import partial
from os import getenv
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from tavily import TavilyClient

from .base_toolkit import Toolkit

load_dotenv()


class TavilyToolkit(Toolkit):
    def __init__(
        self,
        api_key: Optional[str] = None,
        search_depth: str = "advanced",
        max_tokens: int = 4000,
        include_answer: bool = True,
    ):
        self.api_key = api_key or getenv("TAVILY_API_KEY")
        if not self.api_key:
            raise ValueError("TAVILY_API_KEY not provided")

        self.client = TavilyClient(api_key=self.api_key)
        self.search_depth = search_depth
        self.max_tokens = max_tokens
        self.include_answer = include_answer

    @property
    def name(self) -> str:
        return "TavilyToolkit"

    @property
    def description(self) -> str:
        return "A toolkit for performing web searches using the Tavily API."

    @property
    def functions(self) -> Dict[str, Any]:
        return {
            "tavily_search": self.search,
            "tavily_search_with_context": self.search_with_context,
        }

    @property
    def schemas(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "tavily_search",
                    "description": "Search the web using Tavily API",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "The search query"},
                            "max_results": {
                                "type": "integer",
                                "description": "Maximum number of results to return",
                                "default": 5,
                            },
                        },
                        "required": ["query"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "tavily_search_with_context",
                    "description": "Search the web using Tavily API with context",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "The search query"}
                        },
                        "required": ["query"],
                    },
                },
            },
        ]

    async def search(self, query: str, max_results: int = 5) -> str:
        """Search the web using Tavily API."""
        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(
            None,
            partial(
                self.client.search,
                query=query,
                search_depth=self.search_depth,
                max_results=max_results,
                include_answer=self.include_answer,
            ),
        )
        return json.dumps(self._process_response(response, query))

    async def search_with_context(self, query: str) -> str:
        """Search the web using Tavily API with context."""
        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(
            None,
            partial(
                self.client.get_search_context,
                query=query,
                search_depth=self.search_depth,
                max_tokens=self.max_tokens,
                include_answer=self.include_answer,
            ),
        )
        return response

    def _process_response(self, response: Dict[str, Any], query: str) -> Dict[str, Any]:
        clean_response = {"query": query}
        if "answer" in response:
            clean_response["answer"] = response["answer"]

        clean_results = []
        current_token_count = len(json.dumps(clean_response))
        for result in response.get("results", []):
            clean_result = {
                "title": result["title"],
                "url": result["url"],
                "content": result["content"],
                "score": result["score"],
            }
            current_token_count += len(json.dumps(clean_result))
            if current_token_count > self.max_tokens:
                break
            clean_results.append(clean_result)
        clean_response["results"] = clean_results

        return clean_response
