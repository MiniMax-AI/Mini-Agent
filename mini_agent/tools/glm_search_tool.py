"""GLM Search Tool - Web search powered by ZhipuAI (GLM).

This tool provides web search capabilities using ZhipuAI's search API.
It supports parallel multi-query searches with configurable parameters.
"""

import asyncio
import os
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any

from .base import Tool, ToolResult


@dataclass
class SearchResult:
    """Single search result item."""

    title: str
    snippet: str
    link: str
    source: str


@dataclass
class QuerySearchResult:
    """Search results for a single query."""

    query: str
    results: list[dict[str, str]]
    success: bool
    error_message: str | None = None


class GLMSearchTool(Tool):
    """Web search tool powered by ZhipuAI (GLM).

    This tool enables the agent to search the web using ZhipuAI's search API.
    It supports multiple queries in parallel and returns structured results.

    Features:
    - Multi-query parallel search
    - Configurable search parameters (engine, count, recency, content size)
    - Automatic result formatting
    - Graceful error handling

    Example usage by agent:
    - glm_search(query="Python async programming", count=5)
    - glm_search(query="MiniMax AI latest news", search_recency_filter="pastWeek")
    """

    def __init__(self, api_key: str | None = None):
        """Initialize GLM search tool.

        Args:
            api_key: ZhipuAI API key. If not provided, will use ZHIPU_API_KEY env var.
        """
        self.api_key = api_key or os.getenv("ZHIPU_API_KEY")
        if not self.api_key:
            raise ValueError("ZHIPU_API_KEY not provided and not found in environment variables")

    @property
    def name(self) -> str:
        return "glm_search"

    @property
    def description(self) -> str:
        return """Search the web using ZhipuAI (GLM) search API.

Performs intelligent web search and returns relevant results with titles, snippets, and links.
Supports multiple search queries and various configuration options.

Parameters:
  - query (required): Search query string
  - search_engine: Search engine type (default: "search_pro")
  - count: Number of results to return (default: 5, max: 15)
  - search_recency_filter: Time filter - "pastMonth", "pastWeek", "pastDay" (default: "pastMonth")
  - content_size: Summary detail level - "low", "medium", "high" (default: "high")

Returns structured search results with title, snippet, link, and source for each result.

Examples:
  - glm_search(query="Python async programming")
  - glm_search(query="AI news", count=10, search_recency_filter="pastWeek")
  - glm_search(query="machine learning tutorial", content_size="high")"""

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query string",
                },
                "search_engine": {
                    "type": "string",
                    "description": "Search engine type (default: 'search_pro')",
                    "enum": ["search_pro", "search_basic"],
                    "default": "search_pro",
                },
                "count": {
                    "type": "integer",
                    "description": "Number of results to return (default: 5, max: 15)",
                    "minimum": 1,
                    "maximum": 15,
                    "default": 5,
                },
                "search_recency_filter": {
                    "type": "string",
                    "description": "Time filter for search results",
                    "enum": ["pastMonth", "pastWeek", "pastDay"],
                    "default": "pastMonth",
                },
                "content_size": {
                    "type": "string",
                    "description": "Summary detail level",
                    "enum": ["low", "medium", "high"],
                    "default": "high",
                },
            },
            "required": ["query"],
        }

    def _search_single_query(
        self, query: str, search_params: dict[str, Any]
    ) -> QuerySearchResult:
        """Search a single query (synchronous, used in thread pool).

        Args:
            query: Search query string
            search_params: Search parameters dict

        Returns:
            QuerySearchResult with results or error
        """
        try:
            # Import here to avoid import errors if zhipuai not installed
            from zhipuai import ZhipuAI

            # Create client
            client = ZhipuAI(api_key=self.api_key)

            # Perform search
            response = client.web_search.web_search(
                search_query=query, **search_params
            )

            # Process results
            results = []
            for item in response.search_result:
                results.append(
                    {
                        "title": item.title,
                        "snippet": item.content,
                        "link": item.link,
                        "source": item.media,
                    }
                )

            return QuerySearchResult(
                query=query, results=results, success=True, error_message=None
            )

        except Exception as e:
            return QuerySearchResult(
                query=query, results=[], success=False, error_message=str(e)
            )

    def _format_search_results(self, results: list[QuerySearchResult]) -> str:
        """Format search results for display.

        Args:
            results: List of QuerySearchResult objects

        Returns:
            Formatted string representation (model-friendly, concise format)
        """
        if not results:
            return "No search results found."

        output_parts = []

        for query_result in results:
            output_parts.append(f"Query: {query_result.query}")

            if not query_result.success:
                output_parts.append(
                    f"Error: {query_result.error_message}"
                )
                output_parts.append("")
                continue

            if not query_result.results:
                output_parts.append("No results found.")
                output_parts.append("")
                continue

            for idx, result in enumerate(query_result.results, 1):
                output_parts.append(f"\n[{idx}] {result['title']}")
                output_parts.append(f"URL: {result['link']}")
                output_parts.append(f"Source: {result['source']}")
                output_parts.append(f"Content: {result['snippet']}")

            output_parts.append("")

        return "\n".join(output_parts)

    async def execute(
        self,
        query: str,
        search_engine: str = "search_pro",
        count: int = 5,
        search_recency_filter: str = "pastMonth",
        content_size: str = "high",
    ) -> ToolResult:
        """Execute web search.

        Args:
            query: Search query string
            search_engine: Search engine type
            count: Number of results
            search_recency_filter: Time filter
            content_size: Summary detail level

        Returns:
            ToolResult with formatted search results
        """
        try:
            # Validate and prepare parameters
            count = min(max(1, count), 15)  # Clamp to 1-15

            search_params = {
                "search_engine": search_engine,
                "count": count,
                "search_recency_filter": search_recency_filter,
                "content_size": content_size,
            }

            # Execute search in thread pool (since zhipuai client is sync)
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, self._search_single_query, query, search_params
            )

            # Format results
            formatted_output = self._format_search_results([result])

            if not result.success:
                return ToolResult(
                    success=False,
                    content="",
                    error=f"Search failed: {result.error_message}",
                )

            return ToolResult(
                success=True,
                content=formatted_output,
            )

        except Exception as e:
            return ToolResult(
                success=False,
                content="",
                error=f"GLM search execution failed: {str(e)}",
            )


class GLMBatchSearchTool(Tool):
    """Batch web search tool for multiple queries in parallel.

    This tool enables searching multiple queries simultaneously,
    which is more efficient than sequential searches.
    """

    def __init__(self, api_key: str | None = None):
        """Initialize GLM batch search tool.

        Args:
            api_key: ZhipuAI API key. If not provided, will use ZHIPU_API_KEY env var.
        """
        self.api_key = api_key or os.getenv("ZHIPU_API_KEY")
        if not self.api_key:
            raise ValueError("ZHIPU_API_KEY not provided and not found in environment variables")

    @property
    def name(self) -> str:
        return "glm_batch_search"

    @property
    def description(self) -> str:
        return """Search the web for multiple queries in parallel using ZhipuAI (GLM).

This tool performs multiple web searches simultaneously, which is more efficient
than running multiple single searches sequentially.

Parameters:
  - queries (required): List of search query strings
  - search_engine: Search engine type (default: "search_pro")
  - count: Number of results per query (default: 5, max: 15)
  - search_recency_filter: Time filter (default: "pastMonth")
  - content_size: Summary detail level (default: "high")

Example:
  glm_batch_search(queries=["Python async", "FastAPI tutorial", "Docker guide"])"""

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "queries": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of search query strings",
                },
                "search_engine": {
                    "type": "string",
                    "description": "Search engine type (default: 'search_pro')",
                    "default": "search_pro",
                },
                "count": {
                    "type": "integer",
                    "description": "Number of results per query (default: 5, max: 15)",
                    "default": 5,
                },
                "search_recency_filter": {
                    "type": "string",
                    "description": "Time filter",
                    "default": "pastMonth",
                },
                "content_size": {
                    "type": "string",
                    "description": "Summary detail level",
                    "default": "high",
                },
            },
            "required": ["queries"],
        }

    def _search_single_query(
        self, query: str, search_params: dict[str, Any]
    ) -> QuerySearchResult:
        """Search a single query (synchronous, used in thread pool).

        Args:
            query: Search query string
            search_params: Search parameters dict

        Returns:
            QuerySearchResult with results or error
        """
        try:
            from zhipuai import ZhipuAI

            client = ZhipuAI(api_key=self.api_key)
            response = client.web_search.web_search(
                search_query=query, **search_params
            )

            results = []
            for item in response.search_result:
                results.append(
                    {
                        "title": item.title,
                        "snippet": item.content,
                        "link": item.link,
                        "source": item.media,
                    }
                )

            return QuerySearchResult(
                query=query, results=results, success=True, error_message=None
            )

        except Exception as e:
            return QuerySearchResult(
                query=query, results=[], success=False, error_message=str(e)
            )

    def _format_search_results(self, results: list[QuerySearchResult]) -> str:
        """Format search results for display (model-friendly, concise format)."""
        if not results:
            return "No search results found."

        output_parts = []

        for query_result in results:
            output_parts.append(f"Query: {query_result.query}")

            if not query_result.success:
                output_parts.append(
                    f"Error: {query_result.error_message}"
                )
                output_parts.append("")
                continue

            if not query_result.results:
                output_parts.append("No results found.")
                output_parts.append("")
                continue

            for idx, result in enumerate(query_result.results, 1):
                output_parts.append(f"\n[{idx}] {result['title']}")
                output_parts.append(f"URL: {result['link']}")
                output_parts.append(f"Source: {result['source']}")
                output_parts.append(f"Content: {result['snippet']}")

            output_parts.append("")

        return "\n".join(output_parts)

    async def execute(
        self,
        queries: list[str],
        search_engine: str = "search_pro",
        count: int = 5,
        search_recency_filter: str = "pastMonth",
        content_size: str = "high",
    ) -> ToolResult:
        """Execute batch web search.

        Args:
            queries: List of search query strings
            search_engine: Search engine type
            count: Number of results per query
            search_recency_filter: Time filter
            content_size: Summary detail level

        Returns:
            ToolResult with formatted search results for all queries
        """
        try:
            if not queries:
                return ToolResult(
                    success=False, content="", error="No queries provided"
                )

            # Validate and prepare parameters
            count = min(max(1, count), 15)

            search_params = {
                "search_engine": search_engine,
                "count": count,
                "search_recency_filter": search_recency_filter,
                "content_size": content_size,
            }

            # Execute searches in parallel using thread pool
            loop = asyncio.get_event_loop()
            max_workers = min(5, len(queries))  # Max 5 concurrent searches

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all queries
                futures = [
                    loop.run_in_executor(
                        executor, self._search_single_query, query, search_params
                    )
                    for query in queries
                ]

                # Wait for all to complete
                search_results = await asyncio.gather(*futures)

            # Sort results by original query order
            query_order = {query: i for i, query in enumerate(queries)}
            search_results_sorted = sorted(
                search_results, key=lambda x: query_order.get(x.query, len(queries))
            )

            # Format results
            formatted_output = self._format_search_results(search_results_sorted)

            # Check if any search failed
            all_success = all(r.success for r in search_results_sorted)
            if not all_success:
                failed_queries = [r.query for r in search_results_sorted if not r.success]
                return ToolResult(
                    success=False,
                    content=formatted_output,
                    error=f"Some searches failed: {', '.join(failed_queries)}",
                )

            return ToolResult(
                success=True,
                content=formatted_output,
            )

        except Exception as e:
            return ToolResult(
                success=False,
                content="",
                error=f"GLM batch search execution failed: {str(e)}",
            )
