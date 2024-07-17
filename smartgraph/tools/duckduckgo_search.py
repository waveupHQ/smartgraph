# smartgraph/tools/duckduckgo_search.py

import json
from typing import Dict, List

try:
    from duckduckgo_search import DDGS
except ImportError:
    raise ImportError("Please install duckduckgo-search: pip install duckduckgo-search")


class DuckDuckGoSearch:
    def __init__(self, max_results: int = 5):
        self.max_results = max_results
        self.ddgs = DDGS()

    def search(self, query: str) -> str:
        """Perform a web search using DuckDuckGo.

        Args:
            query (str): The search query.

        Returns:
            str: JSON string of search results.
        """
        results = list(self.ddgs.text(keywords=query, max_results=self.max_results))
        return json.dumps(results, indent=2)

    def news(self, query: str) -> str:
        """Get the latest news from DuckDuckGo.

        Args:
            query (str): The news query.

        Returns:
            str: JSON string of news results.
        """
        results = list(self.ddgs.news(keywords=query, max_results=self.max_results))
        return json.dumps(results, indent=2)

    @property
    def search_schema(self) -> Dict:
        return {
            "type": "function",
            "function": {
                "name": "duckduckgo_search",
                "description": "Search the web using DuckDuckGo",
                "parameters": {
                    "type": "object",
                    "properties": {"query": {"type": "string", "description": "The search query"}},
                    "required": ["query"],
                },
            },
        }

    @property
    def news_schema(self) -> Dict:
        return {
            "type": "function",
            "function": {
                "name": "duckduckgo_news",
                "description": "Get the latest news from DuckDuckGo",
                "parameters": {
                    "type": "object",
                    "properties": {"query": {"type": "string", "description": "The news query"}},
                    "required": ["query"],
                },
            },
        }
