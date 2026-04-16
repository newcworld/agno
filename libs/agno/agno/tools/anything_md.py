from os import getenv
from typing import Any, List, Optional

import httpx

from agno.tools import Toolkit
from agno.utils.log import log_debug, log_warning


class AnythingMDTools(Toolkit):
    """
    AnythingMD is a toolkit for converting URLs and HTML content to Markdown.

    Powered by the Anything-MD API (Cloudflare Workers AI), it supports PDF, HTML,
    Office documents, images, CSV, and more.

    Args:
        api_url: The Anything-MD API endpoint. Defaults to ANYTHING_MD_API_URL env var
            or the public instance at https://anything-md.doocs.org.
        max_content_length: Maximum content length in characters. Default is 10000.
        timeout: HTTP request timeout in seconds. Default is 30.
        enable_scrape_url: Enable URL scraping functionality. Default is True.
        enable_convert_html: Enable HTML-to-Markdown conversion. Default is False.
        all: Enable all tools. Overrides individual flags when True. Default is False.
    """

    def __init__(
        self,
        api_url: Optional[str] = None,
        max_content_length: int = 10000,
        timeout: int = 30,
        enable_scrape_url: bool = True,
        enable_convert_html: bool = False,
        all: bool = False,
        **kwargs: Any,
    ):
        self.api_url = (api_url or getenv("ANYTHING_MD_API_URL", "https://anything-md.doocs.org")).rstrip("/")
        self.max_content_length = max_content_length
        self.timeout = timeout

        tools: List[Any] = []
        if all or enable_scrape_url:
            tools.append(self.scrape_url)
        if all or enable_convert_html:
            tools.append(self.convert_html)

        super().__init__(name="anything_md_tools", tools=tools, **kwargs)

    def scrape_url(self, url: str) -> str:
        """Use this function to scrape a webpage and get its content as Markdown.

        Supports HTML pages, PDFs, Office documents, images, CSV, and more.

        Args:
            url: The URL to scrape and convert to Markdown.

        Returns:
            The page content in Markdown format, or an error message.
        """
        if not url:
            return "Error: No URL provided"

        log_debug(f"AnythingMD: scraping URL: {url}")
        try:
            response = httpx.post(
                f"{self.api_url}/",
                json={"url": url},
                headers={"Content-Type": "application/json"},
                timeout=self.timeout,
            )
            response.raise_for_status()
            return self._parse_response(response.json())
        except httpx.HTTPStatusError as e:
            msg = f"Error scraping {url}: HTTP {e.response.status_code}"
            log_warning(msg)
            return msg
        except Exception as e:
            msg = f"Error scraping {url}: {e}"
            log_warning(msg)
            return msg

    def convert_html(self, html: str, file_name: Optional[str] = None) -> str:
        """Use this function to convert raw HTML content to Markdown.

        Args:
            html: The HTML content to convert.
            file_name: Optional output file name hint (e.g. "page.html").

        Returns:
            The converted Markdown content, or an error message.
        """
        if not html:
            return "Error: No HTML content provided"

        log_debug("AnythingMD: converting HTML content")
        try:
            payload: dict[str, Any] = {"html": html}
            if file_name:
                payload["fileName"] = file_name

            response = httpx.post(
                f"{self.api_url}/",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=self.timeout,
            )
            response.raise_for_status()
            return self._parse_response(response.json())
        except httpx.HTTPStatusError as e:
            msg = f"Error converting HTML: HTTP {e.response.status_code}"
            log_warning(msg)
            return msg
        except Exception as e:
            msg = f"Error converting HTML: {e}"
            log_warning(msg)
            return msg

    def _parse_response(self, data: Any) -> str:
        """Parse the API response and return markdown content or error."""
        if not isinstance(data, dict):
            return f"Error: unexpected response format: {data}"

        if not data.get("success", False):
            error = data.get("error", "Unknown error")
            return f"Error from AnythingMD API: {error}"

        markdown = data.get("markdown", "")
        if not markdown:
            return "Error: no markdown content in response"

        result_parts = []
        name = data.get("name")
        if name:
            result_parts.append(f"Source: {name}")

        if self.max_content_length and len(markdown) > self.max_content_length:
            markdown = markdown[: self.max_content_length] + "... (content truncated)"

        result_parts.append(markdown)
        return "\n\n".join(result_parts)
