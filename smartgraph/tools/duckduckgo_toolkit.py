# smartgraph/tools/duckduckgo_toolkit.py

import json
from typing import Any, Dict, List, Optional

from duckduckgo_search import DDGS

from .base_toolkit import Toolkit


class DuckDuckGoToolkit(Toolkit):
    def __init__(self, max_results: int = 5):
        self.max_results = max_results
        self.ddgs = DDGS()

    @property
    def name(self) -> str:
        return "DuckDuckGoToolkit"

    @property
    def description(self) -> str:
        return "A toolkit for performing web searches and fetching news using DuckDuckGo."

    @property
    def functions(self) -> Dict[str, Any]:
        return {
            "duckduckgo_search": self.search,
            "duckduckgo_news": self.news
        }

    @property
    def schemas(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "duckduckgo_search",
                    "description": "Search the web using DuckDuckGo",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "The search query"},
                            "max_results": {"type": "integer", "description": "Maximum number of results to return"}
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "duckduckgo_news",
                    "description": "Get the latest news from DuckDuckGo",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "The news query"},
                            "max_results": {"type": "integer", "description": "Maximum number of news items to return"}
                        },
                        "required": ["query"]
                    }
                }
            }
        ]

    async def search(self, query: str, max_results: Optional[int] = None) -> str:
        """Perform a web search using DuckDuckGo."""
        max_results = max_results or self.max_results
        results = list(self.ddgs.text(keywords=query, max_results=max_results))
        return json.dumps(results, indent=2)

    async def news(self, query: str, max_results: Optional[int] = None) -> str:
        """Get the latest news from DuckDuckGo."""
        max_results = max_results or self.max_results
        results = list(self.ddgs.news(keywords=query, max_results=max_results))
        return json.dumps(results, indent=2)
