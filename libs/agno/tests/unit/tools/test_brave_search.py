import json
import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

pytest.importorskip("brave_search_python_client")

from agno.tools.bravesearch import BraveSearchTools

pytestmark = pytest.mark.skipif(
    sys.version_info < (3, 11),
    reason="brave-search-python-client requires Python 3.11+",
)


@pytest.fixture
def mock_brave_client():
    with patch("agno.tools.bravesearch.BraveSearch") as mock_cls:
        mock_instance = MagicMock()
        mock_result = MagicMock()
        mock_result.web = MagicMock()
        mock_result.web.results = []
        mock_instance.web = AsyncMock(return_value=mock_result)
        mock_cls.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def brave_search_tools(mock_brave_client):
    os.environ["BRAVE_API_KEY"] = "test_api_key"
    return BraveSearchTools()


def test_init_with_api_key():
    with patch("agno.tools.bravesearch.BraveSearch"):
        tools = BraveSearchTools(api_key="test_key")
        assert tools.api_key == "test_key"
        assert tools.fixed_max_results is None
        assert tools.fixed_language is None


def test_init_with_env_var():
    os.environ["BRAVE_API_KEY"] = "env_test_key"
    with patch("agno.tools.bravesearch.BraveSearch"):
        tools = BraveSearchTools()
        assert tools.api_key == "env_test_key"


def test_init_with_alternate_env_var():
    if "BRAVE_API_KEY" in os.environ:
        del os.environ["BRAVE_API_KEY"]
    os.environ["BRAVE_SEARCH_PYTHON_CLIENT_API_KEY"] = "alt_key"
    with patch("agno.tools.bravesearch.BraveSearch"):
        tools = BraveSearchTools()
        assert tools.api_key == "alt_key"
    del os.environ["BRAVE_SEARCH_PYTHON_CLIENT_API_KEY"]


def test_init_without_api_key():
    if "BRAVE_API_KEY" in os.environ:
        del os.environ["BRAVE_API_KEY"]
    if "BRAVE_SEARCH_PYTHON_CLIENT_API_KEY" in os.environ:
        del os.environ["BRAVE_SEARCH_PYTHON_CLIENT_API_KEY"]
    with pytest.raises(ValueError, match="BRAVE_API_KEY is required"):
        BraveSearchTools()


def test_init_with_fixed_params():
    with patch("agno.tools.bravesearch.BraveSearch"):
        tools = BraveSearchTools(api_key="test_key", fixed_max_results=10, fixed_language="fr")
        assert tools.fixed_max_results == 10
        assert tools.fixed_language == "fr"


def test_toolkit_integration():
    with patch("agno.tools.bravesearch.BraveSearch"):
        tools = BraveSearchTools(api_key="test_key")
        assert tools.name == "brave_search"
        assert len(tools.tools) == 1
        assert tools.tools[0].__name__ == "brave_search"
        assert "brave_search" in tools.async_functions


def test_brave_search_empty_query(brave_search_tools):
    result = brave_search_tools.brave_search("")
    assert json.loads(result) == {"error": "Please provide a query to search for"}


def test_brave_search_none_query(brave_search_tools):
    result = brave_search_tools.brave_search(None)
    assert json.loads(result) == {"error": "Please provide a query to search for"}


def test_brave_search_whitespace_query(brave_search_tools, mock_brave_client):
    mock_result = MagicMock()
    mock_result.web.results = []
    mock_brave_client.web = AsyncMock(return_value=mock_result)

    result = brave_search_tools.brave_search("   ")
    result_dict = json.loads(result)

    assert result_dict["query"] == "   "
    assert result_dict["web_results"] == []
    assert result_dict["total_results"] == 0


def test_brave_search_successful(brave_search_tools, mock_brave_client):
    mock_web_result = MagicMock()
    mock_web_result.title = "Test Title"
    mock_web_result.url = "https://test.com"
    mock_web_result.description = "Test Description"

    mock_result = MagicMock()
    mock_result.web.results = [mock_web_result]
    mock_brave_client.web = AsyncMock(return_value=mock_result)

    result = brave_search_tools.brave_search("test query")
    result_dict = json.loads(result)

    assert result_dict["query"] == "test query"
    assert len(result_dict["web_results"]) == 1
    assert result_dict["web_results"][0]["title"] == "Test Title"
    assert result_dict["web_results"][0]["url"] == "https://test.com"
    assert result_dict["web_results"][0]["description"] == "Test Description"
    assert result_dict["total_results"] == 1


@pytest.mark.asyncio
async def test_abrave_search_successful(brave_search_tools, mock_brave_client):
    mock_web_result = MagicMock()
    mock_web_result.title = "Async Title"
    mock_web_result.url = "https://async.example"
    mock_web_result.description = "Async Desc"

    mock_result = MagicMock()
    mock_result.web.results = [mock_web_result]
    mock_brave_client.web = AsyncMock(return_value=mock_result)

    result = await brave_search_tools.abrave_search("async query")
    result_dict = json.loads(result)
    assert result_dict["query"] == "async query"
    assert result_dict["web_results"][0]["title"] == "Async Title"
    mock_brave_client.web.assert_awaited()


def test_brave_search_with_multiple_results(brave_search_tools, mock_brave_client):
    mock_results = []
    for i in range(3):
        mock_result = MagicMock()
        mock_result.title = "Title {}".format(i)
        mock_result.url = "https://test{}.com".format(i)
        mock_result.description = "Description {}".format(i)
        mock_results.append(mock_result)

    mock_search_result = MagicMock()
    mock_search_result.web.results = mock_results
    mock_brave_client.web = AsyncMock(return_value=mock_search_result)

    result = brave_search_tools.brave_search("test query")
    result_dict = json.loads(result)

    assert result_dict["query"] == "test query"
    assert len(result_dict["web_results"]) == 3
    assert result_dict["total_results"] == 3
    for i in range(3):
        assert result_dict["web_results"][i]["title"] == "Title {}".format(i)
        assert result_dict["web_results"][i]["url"] == "https://test{}.com".format(i)
        assert result_dict["web_results"][i]["description"] == "Description {}".format(i)


def test_brave_search_with_malformed_results(brave_search_tools, mock_brave_client):
    mock_web_result = MagicMock()
    mock_web_result.title = None
    mock_web_result.url = None
    mock_web_result.description = None

    mock_result = MagicMock()
    mock_result.web.results = [mock_web_result]
    mock_brave_client.web = AsyncMock(return_value=mock_result)

    result = brave_search_tools.brave_search("test query")
    result_dict = json.loads(result)

    assert result_dict["query"] == "test query"
    assert len(result_dict["web_results"]) == 1
    assert result_dict["web_results"][0]["title"] is None
    assert result_dict["web_results"][0]["url"] == ""
    assert result_dict["web_results"][0]["description"] is None
    assert result_dict["total_results"] == 1


def test_brave_search_with_custom_params(brave_search_tools, mock_brave_client):
    mock_result = MagicMock()
    mock_result.web.results = []
    mock_brave_client.web = AsyncMock(return_value=mock_result)

    brave_search_tools.brave_search(
        query="test query",
        max_results=3,
        country="GB",
        search_lang="fr",
        retries=2,
        wait_time=5,
        result_filter="web",
        freshness="pw",
        summary=True,
    )

    mock_brave_client.web.assert_awaited_once()
    _args, kwargs = mock_brave_client.web.call_args
    request = _args[0]
    assert request.q == "test query"
    assert request.count == 3
    assert str(request.country) == "GB"
    assert request.search_lang == "fr"
    assert request.result_filter == "web"
    assert request.freshness == "pw"
    assert request.summary is True
    assert kwargs["retries"] == 2
    assert kwargs["wait_time"] == 5


def test_brave_search_with_default_params(brave_search_tools, mock_brave_client):
    mock_result = MagicMock()
    mock_result.web.results = []
    mock_brave_client.web = AsyncMock(return_value=mock_result)

    brave_search_tools.brave_search(query="test query")

    _args, kwargs = mock_brave_client.web.call_args
    request = _args[0]
    assert request.q == "test query"
    assert request.count == 5
    assert str(request.country) == "US"
    assert request.search_lang == "en"
    assert request.result_filter == "web"
    assert kwargs["retries"] == 0


def test_brave_search_with_none_country(brave_search_tools, mock_brave_client):
    mock_result = MagicMock()
    mock_result.web.results = []
    mock_brave_client.web = AsyncMock(return_value=mock_result)

    brave_search_tools.brave_search(query="test query", country=None)

    _args, _kwargs = mock_brave_client.web.call_args
    request = _args[0]
    assert request.q == "test query"
    assert str(request.country) == "ALL"


def test_brave_search_with_fixed_params():
    with patch("agno.tools.bravesearch.BraveSearch") as mock_cls:
        mock_instance = MagicMock()
        mock_result = MagicMock()
        mock_result.web.results = []
        mock_instance.web = AsyncMock(return_value=mock_result)
        mock_cls.return_value = mock_instance

        tools = BraveSearchTools(api_key="test_key", fixed_max_results=5, fixed_language="fr")

        result = tools.brave_search(query="test query", max_results=10, search_lang="en")
        result_dict = json.loads(result)

        assert result_dict["query"] == "test query"
        assert result_dict["web_results"] == []
        assert result_dict["total_results"] == 0

        _args, _kwargs = mock_instance.web.call_args
        request = _args[0]
        assert request.count == 5
        assert request.search_lang == "fr"


def test_brave_search_max_results_capped_at_20(brave_search_tools, mock_brave_client):
    mock_result = MagicMock()
    mock_result.web.results = []
    mock_brave_client.web = AsyncMock(return_value=mock_result)

    brave_search_tools.brave_search(query="q", max_results=100)

    _args, _kwargs = mock_brave_client.web.call_args
    assert _args[0].count == 20


def test_brave_search_no_web_results(brave_search_tools, mock_brave_client):
    mock_result = MagicMock()
    mock_result.web = None
    mock_brave_client.web = AsyncMock(return_value=mock_result)

    result = brave_search_tools.brave_search("test query")
    result_dict = json.loads(result)

    assert result_dict["query"] == "test query"
    assert result_dict["web_results"] == []
    assert result_dict["total_results"] == 0


def test_brave_search_web_attribute_missing(brave_search_tools, mock_brave_client):
    class BareResponse:
        pass

    mock_brave_client.web = AsyncMock(return_value=BareResponse())

    result = brave_search_tools.brave_search("test query")
    result_dict = json.loads(result)

    assert result_dict["query"] == "test query"
    assert result_dict["web_results"] == []
    assert result_dict["total_results"] == 0


def test_brave_search_empty_web_results(brave_search_tools, mock_brave_client):
    mock_result = MagicMock()
    mock_result.web.results = []
    mock_brave_client.web = AsyncMock(return_value=mock_result)

    result = brave_search_tools.brave_search("test query")
    result_dict = json.loads(result)

    assert result_dict["query"] == "test query"
    assert result_dict["web_results"] == []
    assert result_dict["total_results"] == 0


def test_brave_search_exception_handling(brave_search_tools, mock_brave_client):
    mock_brave_client.web.side_effect = Exception("API Error")

    with pytest.raises(Exception, match="API Error"):
        brave_search_tools.brave_search("test query")


def test_brave_search_api_error_json(brave_search_tools, mock_brave_client):
    from brave_search_python_client.responses import BraveSearchAPIError

    mock_brave_client.web.side_effect = BraveSearchAPIError("rate limited")

    result = brave_search_tools.brave_search("test query")
    assert json.loads(result) == {"error": "rate limited"}


@pytest.mark.asyncio
async def test_abrave_search_api_error_json(brave_search_tools, mock_brave_client):
    from brave_search_python_client.responses import BraveSearchAPIError

    mock_brave_client.web.side_effect = BraveSearchAPIError("rate limited")

    result = await brave_search_tools.abrave_search("test query")
    assert json.loads(result) == {"error": "rate limited"}


@patch("agno.tools.bravesearch.log_info")
def test_brave_search_logging(mock_log_info, brave_search_tools, mock_brave_client):
    mock_result = MagicMock()
    mock_result.web.results = []
    mock_brave_client.web = AsyncMock(return_value=mock_result)

    brave_search_tools.brave_search("test query")

    mock_log_info.assert_called_once_with("Searching Brave for: test query")


def test_brave_search_result_filter_passed_through(brave_search_tools, mock_brave_client):
    mock_result = MagicMock()
    mock_result.web.results = []
    mock_brave_client.web = AsyncMock(return_value=mock_result)

    brave_search_tools.brave_search("test query", result_filter="web,summarizer")

    _args, _kwargs = mock_brave_client.web.call_args
    assert _args[0].result_filter == "web,summarizer"


def test_brave_search_invalid_country_returns_json_error(brave_search_tools, mock_brave_client):
    result = brave_search_tools.brave_search("q", country="not-a-country")
    data = json.loads(result)
    assert "error" in data
    assert "Invalid search parameters" in data["error"]
    mock_brave_client.web.assert_not_called()


def test_brave_search_url_conversion(brave_search_tools, mock_brave_client):
    mock_web_result = MagicMock()
    mock_web_result.title = "Test Title"
    mock_web_result.url = 12345
    mock_web_result.description = "Test Description"

    mock_result = MagicMock()
    mock_result.web.results = [mock_web_result]
    mock_brave_client.web = AsyncMock(return_value=mock_result)

    result = brave_search_tools.brave_search("test query")
    result_dict = json.loads(result)

    assert result_dict["web_results"][0]["url"] == "12345"


def test_json_serialization_integrity(brave_search_tools, mock_brave_client):
    mock_web_result = MagicMock()
    mock_web_result.title = "Test Title"
    mock_web_result.url = "https://test.com"
    mock_web_result.description = "Test Description"

    mock_result = MagicMock()
    mock_result.web.results = [mock_web_result]
    mock_brave_client.web = AsyncMock(return_value=mock_result)

    result = brave_search_tools.brave_search("test query")

    parsed = json.loads(result)

    assert "web_results" in parsed
    assert "query" in parsed
    assert "total_results" in parsed

    json.dumps(parsed)
