"""Web search tool with configurable backends."""

import os
from abc import ABC, abstractmethod

from pydantic import Field

from koder.config.settings import get_settings
from koder.tools.base import ReadOnlyTool
from koder.tools.registry import registry


class SearchBackend(ABC):
    """Abstract base class for search backends."""

    @abstractmethod
    def search(
        self, query: str, max_results: int, safe_search: bool
    ) -> list[dict[str, str]]:
        """Execute search and return list of results.

        Each result should be a dict with keys: title, url, description
        """
        pass


class DuckDuckGoBackend(SearchBackend):
    """DuckDuckGo search backend (free, no API key required)."""

    def search(
        self, query: str, max_results: int, safe_search: bool
    ) -> list[dict[str, str]]:
        """Execute DuckDuckGo search."""
        try:
            from ddgs import DDGS
        except ImportError:
            try:
                # Fallback to old package name
                from duckduckgo_search import DDGS
            except ImportError:
                raise ImportError(
                    "ddgs package not installed. Install with: pip install ddgs"
                )

        try:
            ddgs = DDGS()
            safesearch = "moderate" if safe_search else "off"
            results = ddgs.text(
                query, region="wt-wt", safesearch=safesearch, max_results=max_results
            )

            formatted_results = []
            for result in results:
                formatted_results.append(
                    {
                        "title": result.get("title", ""),
                        "url": result.get("href", ""),
                        "description": result.get("body", ""),
                    }
                )
            return formatted_results

        except Exception as e:
            raise RuntimeError(f"DuckDuckGo search failed: {str(e)}")


class TavilyBackend(SearchBackend):
    """Tavily AI search backend (requires API key)."""

    def __init__(self, api_key: str | None = None):
        """Initialize Tavily backend.

        Args:
            api_key: Tavily API key. If not provided, will try to get from env.
        """
        self.api_key = api_key or os.getenv("TAVILY_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Tavily API key not found. Set TAVILY_API_KEY environment variable "
                "or provide via web_search.tavily_api_key in settings."
            )

    def search(
        self, query: str, max_results: int, safe_search: bool
    ) -> list[dict[str, str]]:
        """Execute Tavily search."""
        try:
            from tavily import TavilyClient
        except ImportError:
            raise ImportError(
                "tavily-python package not installed. "
                "Install with: pip install tavily-python"
            )

        try:
            client = TavilyClient(api_key=self.api_key)
            response = client.search(
                query=query,
                max_results=max_results,
                search_depth="basic",
                include_answer=True,
            )

            formatted_results = []

            # Include AI-generated answer if available
            if response.get("answer"):
                formatted_results.append(
                    {
                        "title": "AI Summary",
                        "url": "",
                        "description": response["answer"],
                    }
                )

            # Add search results
            for result in response.get("results", []):
                formatted_results.append(
                    {
                        "title": result.get("title", ""),
                        "url": result.get("url", ""),
                        "description": result.get("content", ""),
                    }
                )

            return formatted_results[:max_results]

        except Exception as e:
            raise RuntimeError(f"Tavily search failed: {str(e)}")


class BraveBackend(SearchBackend):
    """Brave search backend (requires API key)."""

    def __init__(self, api_key: str | None = None):
        """Initialize Brave backend.

        Args:
            api_key: Brave API key. If not provided, will try to get from env.
        """
        self.api_key = api_key or os.getenv("BRAVE_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Brave API key not found. Set BRAVE_API_KEY environment variable "
                "or provide via web_search.brave_api_key in settings."
            )

    def search(
        self, query: str, max_results: int, safe_search: bool
    ) -> list[dict[str, str]]:
        """Execute Brave search."""
        try:
            import requests
        except ImportError:
            raise ImportError(
                "requests package not installed. Install with: pip install requests"
            )

        try:
            url = "https://api.search.brave.com/res/v1/web/search"
            headers = {
                "Accept": "application/json",
                "X-Subscription-Token": self.api_key,
            }
            params = {
                "q": query,
                "count": max_results,
                "safesearch": "moderate" if safe_search else "off",
            }

            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            formatted_results = []
            for result in data.get("web", {}).get("results", []):
                formatted_results.append(
                    {
                        "title": result.get("title", ""),
                        "url": result.get("url", ""),
                        "description": result.get("description", ""),
                    }
                )

            return formatted_results

        except Exception as e:
            raise RuntimeError(f"Brave search failed: {str(e)}")


@registry.register(category="web", is_read_only=True)
class WebSearchTool(ReadOnlyTool):
    """Search the web for current information using configurable backends.

    Supports three backends:
    - DuckDuckGo (default, free, no API key required)
    - Tavily (requires API key, optimized for AI)
    - Brave (requires API key, independent search index)
    """

    name: str = "web_search"
    description: str = (
        "Search the web for current information, recent events, or general knowledge. "
        "Useful when you need up-to-date information that may not be in your training data. "
        "Input should be a clear, specific search query. "
        "Returns relevant web pages with titles, URLs, and descriptions."
    )

    backend: str | None = Field(
        default=None, description="Search backend (auto-selected from settings if None)"
    )
    max_results: int | None = Field(
        default=None, description="Max results (uses settings default if None)"
    )
    safe_search: bool | None = Field(
        default=None, description="Safe search (uses settings default if None)"
    )

    def _get_backend(self) -> SearchBackend:
        """Get the appropriate search backend based on settings."""
        settings = get_settings()
        backend_name = self.backend or settings.web_search.backend

        if backend_name == "duckduckgo":
            return DuckDuckGoBackend()
        elif backend_name == "tavily":
            api_key = settings.web_search.tavily_api_key
            if not api_key:
                raise ValueError(
                    "Tavily backend selected but no API key found. "
                    "Either set TAVILY_API_KEY environment variable or switch to "
                    "'duckduckgo' backend."
                )
            return TavilyBackend(api_key=api_key)
        elif backend_name == "brave":
            api_key = settings.web_search.brave_api_key
            if not api_key:
                raise ValueError(
                    "Brave backend selected but no API key found. "
                    "Either set BRAVE_API_KEY environment variable or switch to "
                    "'duckduckgo' backend."
                )
            return BraveBackend(api_key=api_key)
        else:
            raise ValueError(
                f"Unknown search backend: {backend_name}. "
                "Valid options: duckduckgo, tavily, brave"
            )

    def _format_results(self, results: list[dict[str, str]]) -> str:
        """Format search results into a readable string."""
        if not results:
            return "No results found."

        formatted = []
        for i, result in enumerate(results, 1):
            title = result.get("title", "No title")
            url = result.get("url", "")
            description = result.get("description", "No description available")

            if url:
                formatted.append(f"{i}. {title}\n   URL: {url}\n   {description}\n")
            else:
                # For AI summaries or results without URLs
                formatted.append(f"{i}. {title}\n   {description}\n")

        return "\n".join(formatted)

    def _run(self, query: str) -> str:
        """Execute web search.

        Args:
            query: Search query string

        Returns:
            Formatted search results with titles, URLs, and descriptions
        """
        try:
            settings = get_settings()
            max_results = self.max_results or settings.web_search.max_results
            safe_search = (
                self.safe_search
                if self.safe_search is not None
                else settings.web_search.safe_search
            )

            backend = self._get_backend()
            results = backend.search(
                query=query, max_results=max_results, safe_search=safe_search
            )

            return self._format_results(results)

        except Exception as e:
            return self._handle_error(e)
