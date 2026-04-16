import asyncio
import json
import sys
from os import getenv
from typing import Any, Dict, List, Optional

from pydantic import ValidationError

from agno.tools import Toolkit
from agno.utils.log import log_info

try:
    from brave_search_python_client import BraveSearch
    from brave_search_python_client.constants import DEFAULT_RETRY_WAIT_TIME
    from brave_search_python_client.requests import WebSearchRequest
    from brave_search_python_client.responses import BraveSearchAPIError
except ImportError:
    raise ImportError(
        "`brave-search-python-client` not installed (requires Python 3.11+). "
        "Please install using `pip install brave-search-python-client`"
    )


class BraveSearchTools(Toolkit):
    """
    BraveSearch is a toolkit for searching Brave using the official
    `brave-search-python-client` (Brave Search API).

    Args:
        api_key (str, optional): Brave Search API subscription token. If omitted, reads
            `BRAVE_API_KEY` or `BRAVE_SEARCH_PYTHON_CLIENT_API_KEY`.
        fixed_max_results (Optional[int]): A fixed number of maximum results (capped at 20).
        fixed_language (Optional[str]): A fixed language for the search results.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        fixed_max_results: Optional[int] = None,
        fixed_language: Optional[str] = None,
        enable_brave_search: bool = True,
        all: bool = False,
        **kwargs,
    ):
        if sys.version_info < (3, 11):
            raise ImportError("BraveSearchTools requires Python 3.11+ for brave-search-python-client.")

        self.api_key = api_key or getenv("BRAVE_API_KEY") or getenv("BRAVE_SEARCH_PYTHON_CLIENT_API_KEY")
        if not self.api_key:
            raise ValueError(
                "BRAVE_API_KEY is required. Please set BRAVE_API_KEY (or BRAVE_SEARCH_PYTHON_CLIENT_API_KEY)."
            )

        self.fixed_max_results = fixed_max_results
        self.fixed_language = fixed_language

        self.brave_client = BraveSearch(api_key=self.api_key)

        tools = []
        async_tools = []
        if all or enable_brave_search:
            tools.append(self.brave_search)
            async_tools.append((self.abrave_search, "brave_search"))

        super().__init__(
            name="brave_search",
            tools=tools,
            async_tools=async_tools,
            **kwargs,
        )

    def _build_web_request(
        self,
        query: str,
        *,
        max_results: int,
        country: Optional[str],
        search_lang: str,
        result_filter: str,
        freshness: Optional[str],
        summary: Optional[bool],
        extra_snippets: Optional[bool],
    ) -> WebSearchRequest:
        capped = min(max(1, max_results), 20)
        return WebSearchRequest(
            q=query,
            count=capped,
            country=country,
            search_lang=search_lang,
            result_filter=result_filter,
            freshness=freshness,
            summary=summary,
            extra_snippets=extra_snippets,
        )

    @staticmethod
    def _web_results_payload(response: Any) -> List[Dict[str, Optional[str]]]:
        web = getattr(response, "web", None)
        if not web:
            return []
        results = getattr(web, "results", None) or []
        out: List[Dict[str, Optional[str]]] = []
        for result in results:
            out.append(
                {
                    "title": getattr(result, "title", None),
                    "url": str(getattr(result, "url", "") or ""),
                    "description": getattr(result, "description", None),
                }
            )
        return out

    def _format_response(self, response: Any, query: str) -> str:
        web_results = self._web_results_payload(response)
        filtered_results = {
            "web_results": web_results,
            "query": query,
            "total_results": len(web_results),
        }
        return json.dumps(filtered_results, indent=2)

    async def _run_web_search(
        self,
        request: WebSearchRequest,
        *,
        retries: int,
        wait_time: int,
    ) -> Any:
        return await self.brave_client.web(request, retries=retries, wait_time=wait_time)

    def brave_search(
        self,
        query: str,
        max_results: int = 5,
        country: str = "US",
        search_lang: str = "en",
        retries: int = 0,
        wait_time: int = DEFAULT_RETRY_WAIT_TIME,
        result_filter: str = "web",
        freshness: Optional[str] = None,
        summary: Optional[bool] = None,
        extra_snippets: Optional[bool] = None,
    ) -> str:
        """
        Search Brave for the specified query and return the results.

        Args:
            query (str): The query to search for.
            max_results (int, optional): The maximum number of results to return. Default is 5 (max 20).
            country (str, optional): The country code for search results. Default is "US".
            search_lang (str, optional): The language of the search results. Default is "en".
            retries (int, optional): Retries on failure (official client). Default is 0.
            wait_time (int, optional): Seconds between retries. Default follows Brave client.
            result_filter (str, optional): Comma-separated Brave result types. Default is "web".
            freshness (str, optional): Freshness filter (e.g. pd, pw, pm, py, or date range).
            summary (bool, optional): When True, enables summary key generation (see Brave Web API docs).
            extra_snippets (bool, optional): Request extra snippets when supported by your plan.
        Returns:
            str: A JSON formatted string containing the search results.
        """
        final_max_results = self.fixed_max_results if self.fixed_max_results is not None else max_results
        final_search_lang = self.fixed_language if self.fixed_language is not None else search_lang

        if not query:
            return json.dumps({"error": "Please provide a query to search for"})

        log_info("Searching Brave for: {}".format(query))

        try:
            request = self._build_web_request(
                query,
                max_results=final_max_results,
                country=country,
                search_lang=final_search_lang,
                result_filter=result_filter,
                freshness=freshness,
                summary=summary,
                extra_snippets=extra_snippets,
            )
        except ValidationError as e:
            return json.dumps({"error": "Invalid search parameters: {}".format(e)})

        try:
            response = asyncio.run(self._run_web_search(request, retries=retries, wait_time=wait_time))
        except BraveSearchAPIError as e:
            return json.dumps({"error": str(e)})

        return self._format_response(response, query)

    async def abrave_search(
        self,
        query: str,
        max_results: int = 5,
        country: str = "US",
        search_lang: str = "en",
        retries: int = 0,
        wait_time: int = DEFAULT_RETRY_WAIT_TIME,
        result_filter: str = "web",
        freshness: Optional[str] = None,
        summary: Optional[bool] = None,
        extra_snippets: Optional[bool] = None,
    ) -> str:
        """
        Async variant of ``brave_search`` for ``agent.arun`` / async tool execution.
        """
        final_max_results = self.fixed_max_results if self.fixed_max_results is not None else max_results
        final_search_lang = self.fixed_language if self.fixed_language is not None else search_lang

        if not query:
            return json.dumps({"error": "Please provide a query to search for"})

        log_info("Searching Brave for: {}".format(query))

        try:
            request = self._build_web_request(
                query,
                max_results=final_max_results,
                country=country,
                search_lang=final_search_lang,
                result_filter=result_filter,
                freshness=freshness,
                summary=summary,
                extra_snippets=extra_snippets,
            )
        except ValidationError as e:
            return json.dumps({"error": "Invalid search parameters: {}".format(e)})

        try:
            response = await self._run_web_search(request, retries=retries, wait_time=wait_time)
        except BraveSearchAPIError as e:
            return json.dumps({"error": str(e)})

        return self._format_response(response, query)
