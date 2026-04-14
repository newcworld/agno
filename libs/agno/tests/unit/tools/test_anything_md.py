"""Unit tests for AnythingMDTools class."""

from unittest.mock import MagicMock, patch

import pytest

from agno.tools.anything_md import AnythingMDTools


@pytest.fixture
def tools():
    """Create an AnythingMDTools instance with default settings."""
    return AnythingMDTools(api_url="https://test.example.com")


@pytest.fixture
def all_tools():
    """Create an AnythingMDTools instance with all tools enabled."""
    return AnythingMDTools(api_url="https://test.example.com", all=True)


def test_initialization_default():
    """Test initialization with default values."""
    with patch.dict("os.environ", {}, clear=False):
        tools = AnythingMDTools()
        assert tools.name == "anything_md_tools"
        assert tools.api_url == "https://anything-md.doocs.org"
        assert tools.max_content_length == 10000
        assert tools.timeout == 30

        function_names = [func.name for func in tools.functions.values()]
        assert "scrape_url" in function_names
        assert "convert_html" not in function_names
        assert len(tools.functions) == 1


def test_initialization_with_env_var():
    """Test initialization reads ANYTHING_MD_API_URL from environment."""
    with patch.dict("os.environ", {"ANYTHING_MD_API_URL": "https://custom.example.com"}):
        tools = AnythingMDTools()
        assert tools.api_url == "https://custom.example.com"


def test_initialization_trailing_slash():
    """Test that trailing slash is stripped from api_url."""
    tools = AnythingMDTools(api_url="https://test.example.com/")
    assert tools.api_url == "https://test.example.com"


def test_initialization_custom():
    """Test initialization with custom parameters."""
    tools = AnythingMDTools(
        api_url="https://custom.example.com",
        max_content_length=5000,
        timeout=60,
    )
    assert tools.api_url == "https://custom.example.com"
    assert tools.max_content_length == 5000
    assert tools.timeout == 60


def test_initialization_all_tools():
    """Test initialization with all tools enabled."""
    tools = AnythingMDTools(all=True)
    function_names = [func.name for func in tools.functions.values()]
    assert "scrape_url" in function_names
    assert "convert_html" in function_names
    assert len(tools.functions) == 2


def test_initialization_selective_tools():
    """Test initialization with selective tool flags."""
    tools = AnythingMDTools(enable_scrape_url=False, enable_convert_html=True)
    function_names = [func.name for func in tools.functions.values()]
    assert "scrape_url" not in function_names
    assert "convert_html" in function_names
    assert len(tools.functions) == 1


def test_scrape_url_empty(tools):
    """Test scrape_url with empty URL."""
    result = tools.scrape_url("")
    assert result == "Error: No URL provided"


@patch("agno.tools.anything_md.httpx.post")
def test_scrape_url_success(mock_post, tools):
    """Test successful URL scraping."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "success": True,
        "url": "https://example.com",
        "name": "Example Domain",
        "mimeType": "text/html",
        "tokens": 0,
        "markdown": "# Example Domain\n\nThis domain is for illustrative examples.",
    }
    mock_response.raise_for_status = MagicMock()
    mock_post.return_value = mock_response

    result = tools.scrape_url("https://example.com")

    assert "Example Domain" in result
    assert "# Example Domain" in result
    mock_post.assert_called_once_with(
        "https://test.example.com/",
        json={"url": "https://example.com"},
        headers={"Content-Type": "application/json"},
        timeout=30,
    )


@patch("agno.tools.anything_md.httpx.post")
def test_scrape_url_no_name(mock_post, tools):
    """Test scraping when response has no name field."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "success": True,
        "markdown": "# Hello World",
    }
    mock_response.raise_for_status = MagicMock()
    mock_post.return_value = mock_response

    result = tools.scrape_url("https://example.com")

    assert result == "# Hello World"
    assert "Source:" not in result


@patch("agno.tools.anything_md.httpx.post")
def test_scrape_url_api_error(mock_post, tools):
    """Test scraping when API returns error."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "success": False,
        "error": "Failed to fetch URL: 404 Not Found",
    }
    mock_response.raise_for_status = MagicMock()
    mock_post.return_value = mock_response

    result = tools.scrape_url("https://example.com/missing")

    assert "Error from AnythingMD API" in result
    assert "404 Not Found" in result


@patch("agno.tools.anything_md.httpx.post")
def test_scrape_url_http_error(mock_post, tools):
    """Test scraping when HTTP request fails."""
    import httpx

    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_post.return_value = mock_response
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Server Error",
        request=MagicMock(),
        response=mock_response,
    )

    result = tools.scrape_url("https://example.com")

    assert "Error scraping" in result
    assert "HTTP 500" in result


@patch("agno.tools.anything_md.httpx.post")
def test_scrape_url_network_error(mock_post, tools):
    """Test scraping when network error occurs."""
    mock_post.side_effect = Exception("Connection refused")

    result = tools.scrape_url("https://example.com")

    assert "Error scraping" in result
    assert "Connection refused" in result


@patch("agno.tools.anything_md.httpx.post")
def test_scrape_url_content_truncation(mock_post, tools):
    """Test content truncation when exceeding max_content_length."""
    tools.max_content_length = 50
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "success": True,
        "markdown": "A" * 200,
    }
    mock_response.raise_for_status = MagicMock()
    mock_post.return_value = mock_response

    result = tools.scrape_url("https://example.com")

    assert result.endswith("... (content truncated)")
    assert len(result) == 50 + len("... (content truncated)")


@patch("agno.tools.anything_md.httpx.post")
def test_scrape_url_empty_markdown(mock_post, tools):
    """Test scraping when API returns empty markdown."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "success": True,
        "markdown": "",
    }
    mock_response.raise_for_status = MagicMock()
    mock_post.return_value = mock_response

    result = tools.scrape_url("https://example.com")

    assert result == "Error: no markdown content in response"


def test_convert_html_empty(all_tools):
    """Test convert_html with empty content."""
    result = all_tools.convert_html("")
    assert result == "Error: No HTML content provided"


@patch("agno.tools.anything_md.httpx.post")
def test_convert_html_success(mock_post, all_tools):
    """Test successful HTML conversion."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "success": True,
        "name": "page.html",
        "markdown": "# Hello\n\nWorld",
    }
    mock_response.raise_for_status = MagicMock()
    mock_post.return_value = mock_response

    result = all_tools.convert_html("<html><body><h1>Hello</h1><p>World</p></body></html>")

    assert "# Hello" in result
    assert "World" in result
    mock_post.assert_called_once_with(
        "https://test.example.com/",
        json={"html": "<html><body><h1>Hello</h1><p>World</p></body></html>"},
        headers={"Content-Type": "application/json"},
        timeout=30,
    )


@patch("agno.tools.anything_md.httpx.post")
def test_convert_html_with_filename(mock_post, all_tools):
    """Test HTML conversion with custom file name."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "success": True,
        "markdown": "# Test",
    }
    mock_response.raise_for_status = MagicMock()
    mock_post.return_value = mock_response

    all_tools.convert_html("<h1>Test</h1>", file_name="my-page.html")

    call_args = mock_post.call_args
    assert call_args[1]["json"]["fileName"] == "my-page.html"


@patch("agno.tools.anything_md.httpx.post")
def test_convert_html_api_error(mock_post, all_tools):
    """Test HTML conversion when API returns error."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "success": False,
        "error": "Conversion failed",
    }
    mock_response.raise_for_status = MagicMock()
    mock_post.return_value = mock_response

    result = all_tools.convert_html("<html>bad content</html>")

    assert "Error from AnythingMD API" in result
    assert "Conversion failed" in result


@patch("agno.tools.anything_md.httpx.post")
def test_convert_html_network_error(mock_post, all_tools):
    """Test HTML conversion when network error occurs."""
    mock_post.side_effect = Exception("Timeout")

    result = all_tools.convert_html("<h1>Test</h1>")

    assert "Error converting HTML" in result
    assert "Timeout" in result


def test_parse_response_unexpected_format(tools):
    """Test _parse_response with unexpected data format."""
    result = tools._parse_response("not a dict")
    assert "Error: unexpected response format" in result


def test_parse_response_unknown_error(tools):
    """Test _parse_response when error field is missing."""
    result = tools._parse_response({"success": False})
    assert "Unknown error" in result
