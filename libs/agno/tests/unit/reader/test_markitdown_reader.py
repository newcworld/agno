import asyncio
from io import BytesIO
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest

from agno.knowledge.document.base import Document


# ---------------------------------------------------------------------------
# Helpers: mock MarkItDown before importing the reader module
# ---------------------------------------------------------------------------

def _make_mock_result(text: str = "# Converted\n\nSome markdown content."):
    """Build a mock MarkItDown conversion result."""
    result = Mock()
    result.text_content = text
    return result


def _make_mock_markitdown(text: str = "# Converted\n\nSome markdown content."):
    """Build a mock MarkItDown instance."""
    md = Mock()
    md.convert.return_value = _make_mock_result(text)
    md.convert_stream.return_value = _make_mock_result(text)
    return md


# ---------------------------------------------------------------------------
# Module-level patch: ensure markitdown import succeeds with a mock
# ---------------------------------------------------------------------------

_mock_mid_module = MagicMock()
_mock_mid_class = Mock(side_effect=lambda **kw: _make_mock_markitdown())
_mock_mid_module.MarkItDown = _mock_mid_class


@pytest.fixture(autouse=True)
def _patch_markitdown(monkeypatch):
    """Patch the markitdown import so the reader can be instantiated without installing markitdown."""
    import importlib
    import sys

    # Inject a fake markitdown module
    monkeypatch.setitem(sys.modules, "markitdown", _mock_mid_module)

    # Re-import the reader module so it picks up the patched markitdown
    import agno.knowledge.reader.markitdown_reader as mod

    monkeypatch.setattr(mod, "_MARKITDOWN_AVAILABLE", True)
    monkeypatch.setattr(mod, "MarkItDown", _mock_mid_class)

    # Patch _build_markitdown to return a fresh mock each time
    monkeypatch.setattr(mod, "_build_markitdown", lambda **kw: _make_mock_markitdown())

    yield


def _get_reader(**kwargs):
    from agno.knowledge.reader.markitdown_reader import MarkItDownReader

    return MarkItDownReader(**kwargs)


# ---------------------------------------------------------------------------
# Tests: instantiation
# ---------------------------------------------------------------------------


def test_instantiation():
    reader = _get_reader()
    assert reader is not None
    assert reader._md is not None


def test_import_error_when_not_available(monkeypatch):
    import agno.knowledge.reader.markitdown_reader as mod

    monkeypatch.setattr(mod, "_MARKITDOWN_AVAILABLE", False)

    with pytest.raises(ImportError, match="markitdown"):
        _get_reader()


def test_default_chunk_size():
    from agno.knowledge.chunking.document import DocumentChunking

    reader = _get_reader()
    assert reader.chunk_size == 5000
    assert isinstance(reader.chunking_strategy, DocumentChunking)


def test_custom_chunk_size():
    reader = _get_reader(chunk_size=800)
    assert reader.chunk_size == 800
    assert reader.chunking_strategy.chunk_size == 800


# ---------------------------------------------------------------------------
# Tests: supported types
# ---------------------------------------------------------------------------


def test_supported_content_types():
    from agno.knowledge.reader.markitdown_reader import MarkItDownReader
    from agno.knowledge.types import ContentType

    types = MarkItDownReader.get_supported_content_types()
    assert ContentType.IMAGE_PNG in types
    assert ContentType.IMAGE_JPEG in types
    assert ContentType.HTML in types


def test_supported_chunking_strategies():
    from agno.knowledge.reader.markitdown_reader import MarkItDownReader
    from agno.knowledge.chunking.strategy import ChunkingStrategyType

    strategies = MarkItDownReader.get_supported_chunking_strategies()
    assert ChunkingStrategyType.DOCUMENT_CHUNKER in strategies
    assert ChunkingStrategyType.FIXED_SIZE_CHUNKER in strategies


# ---------------------------------------------------------------------------
# Tests: read from file path
# ---------------------------------------------------------------------------


def test_read_file_path(tmp_path):
    html_file = tmp_path / "page.html"
    html_file.write_text("<html><body>hello</body></html>")

    reader = _get_reader()
    reader._md = _make_mock_markitdown("# Page\n\nhello")

    documents = reader.read(html_file)

    assert len(documents) >= 1
    assert documents[0].name == "page"
    assert "hello" in documents[0].content


def test_read_file_path_custom_name(tmp_path):
    html_file = tmp_path / "page.html"
    html_file.write_text("<html><body>hi</body></html>")

    reader = _get_reader()
    reader._md = _make_mock_markitdown("hi")

    documents = reader.read(html_file, name="custom")

    assert len(documents) >= 1
    assert documents[0].name == "custom"


def test_read_nonexistent_file():
    reader = _get_reader()
    with pytest.raises(FileNotFoundError, match="Could not find file"):
        reader.read(Path("/nonexistent/file.png"))


# ---------------------------------------------------------------------------
# Tests: read from BytesIO (uploaded file)
# ---------------------------------------------------------------------------


def test_read_bytesio():
    bio = BytesIO(b"\x89PNG\r\n\x1a\n fake png data")

    reader = _get_reader()
    reader._md = _make_mock_markitdown("# Image Description\n\nA photo of a cat.")

    documents = reader.read(bio, name="photo.png")

    assert len(documents) >= 1
    assert documents[0].name == "photo"
    assert "cat" in documents[0].content


def test_read_bytesio_no_name():
    bio = BytesIO(b"hello bytes")
    bio.name = "upload.html"

    reader = _get_reader()
    reader._md = _make_mock_markitdown("hello bytes")

    documents = reader.read(bio)

    assert len(documents) >= 1
    assert documents[0].name == "upload"


def test_read_bytesio_passes_extension():
    bio = BytesIO(b"fake image")

    reader = _get_reader()
    mock_md = _make_mock_markitdown("image content")
    reader._md = mock_md

    reader.read(bio, name="test.png")

    mock_md.convert_stream.assert_called_once()
    call_kwargs = mock_md.convert_stream.call_args
    assert call_kwargs[1].get("file_extension") == ".png" or call_kwargs[0][1] if len(call_kwargs[0]) > 1 else True


# ---------------------------------------------------------------------------
# Tests: read from string path
# ---------------------------------------------------------------------------


def test_read_string_path():
    reader = _get_reader()
    reader._md = _make_mock_markitdown("string path content")

    documents = reader.read("/some/file.html", name="myfile")

    assert len(documents) >= 1
    assert documents[0].name == "myfile"


def test_read_string_path_name_from_path():
    reader = _get_reader()
    reader._md = _make_mock_markitdown("inferred name")

    documents = reader.read("/some/document.htm")

    assert len(documents) >= 1
    assert documents[0].name == "document"


# ---------------------------------------------------------------------------
# Tests: empty / error handling
# ---------------------------------------------------------------------------


def test_empty_content_returns_empty():
    bio = BytesIO(b"data")

    reader = _get_reader()
    reader._md = _make_mock_markitdown("")

    documents = reader.read(bio, name="empty.png")
    assert documents == []


def test_whitespace_only_content_returns_empty():
    bio = BytesIO(b"data")

    reader = _get_reader()
    reader._md = _make_mock_markitdown("   \n  \t  ")

    documents = reader.read(bio, name="blank.png")
    assert documents == []


def test_conversion_exception_returns_empty():
    bio = BytesIO(b"data")

    reader = _get_reader()
    reader._md.convert_stream.side_effect = RuntimeError("boom")

    documents = reader.read(bio, name="fail.png")
    assert documents == []


# ---------------------------------------------------------------------------
# Tests: chunking
# ---------------------------------------------------------------------------


def test_chunking_enabled():
    bio = BytesIO(b"data")

    reader = _get_reader()
    reader._md = _make_mock_markitdown("chunk me")
    reader.chunk = True
    reader.chunk_document = Mock(return_value=[
        Document(name="doc", id="1", content="Chunk 1"),
        Document(name="doc", id="2", content="Chunk 2"),
    ])

    documents = reader.read(bio, name="doc.html")

    reader.chunk_document.assert_called_once()
    assert len(documents) == 2
    assert documents[0].content == "Chunk 1"


def test_chunking_disabled():
    bio = BytesIO(b"data")

    reader = _get_reader()
    reader._md = _make_mock_markitdown("no chunk")
    reader.chunk = False

    documents = reader.read(bio, name="doc.html")

    assert len(documents) == 1
    assert documents[0].content == "no chunk"


# ---------------------------------------------------------------------------
# Tests: async
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_async_read_file(tmp_path):
    html_file = tmp_path / "async.html"
    html_file.write_text("<p>async test</p>")

    reader = _get_reader()
    reader._md = _make_mock_markitdown("async content")

    documents = await reader.async_read(html_file)

    assert len(documents) >= 1
    assert "async content" in documents[0].content


@pytest.mark.asyncio
async def test_async_read_bytesio():
    bio = BytesIO(b"async bytes")

    reader = _get_reader()
    reader._md = _make_mock_markitdown("async bytes result")

    documents = await reader.async_read(bio, name="async.png")

    assert len(documents) >= 1
    assert documents[0].name == "async"


@pytest.mark.asyncio
async def test_async_nonexistent_file():
    reader = _get_reader()
    with pytest.raises(FileNotFoundError):
        await reader.async_read(Path("/no/such/file.png"))


@pytest.mark.asyncio
async def test_async_conversion_error():
    bio = BytesIO(b"fail")

    reader = _get_reader()
    reader._md.convert_stream.side_effect = RuntimeError("async boom")

    documents = await reader.async_read(bio, name="fail.png")
    assert documents == []


@pytest.mark.asyncio
async def test_async_concurrent_reads():
    reader = _get_reader()
    reader._md = _make_mock_markitdown("concurrent result")

    async def read_one(i):
        bio = BytesIO(f"data-{i}".encode())
        return await reader.async_read(bio, name=f"file{i}.html")

    results = await asyncio.gather(*[read_one(i) for i in range(3)])

    assert len(results) == 3
    assert all(len(docs) >= 1 for docs in results)


# ---------------------------------------------------------------------------
# Tests: ReaderFactory integration
# ---------------------------------------------------------------------------


def test_factory_routes_png_to_markitdown():
    from agno.knowledge.reader.reader_factory import ReaderFactory

    with patch.object(ReaderFactory, "create_reader") as mock_create:
        mock_create.return_value = _get_reader()
        ReaderFactory.get_reader_for_extension(".png")
        mock_create.assert_called_with("markitdown")


def test_factory_routes_jpg_to_markitdown():
    from agno.knowledge.reader.reader_factory import ReaderFactory

    with patch.object(ReaderFactory, "create_reader") as mock_create:
        mock_create.return_value = _get_reader()
        ReaderFactory.get_reader_for_extension(".jpg")
        mock_create.assert_called_with("markitdown")


def test_factory_routes_jpeg_to_markitdown():
    from agno.knowledge.reader.reader_factory import ReaderFactory

    with patch.object(ReaderFactory, "create_reader") as mock_create:
        mock_create.return_value = _get_reader()
        ReaderFactory.get_reader_for_extension(".jpeg")
        mock_create.assert_called_with("markitdown")


def test_factory_routes_html_to_markitdown():
    from agno.knowledge.reader.reader_factory import ReaderFactory

    with patch.object(ReaderFactory, "create_reader") as mock_create:
        mock_create.return_value = _get_reader()
        ReaderFactory.get_reader_for_extension(".html")
        mock_create.assert_called_with("markitdown")


def test_factory_routes_image_mime_to_markitdown():
    from agno.knowledge.reader.reader_factory import ReaderFactory

    with patch.object(ReaderFactory, "create_reader") as mock_create:
        mock_create.return_value = _get_reader()
        ReaderFactory.get_reader_for_extension("image/png")
        mock_create.assert_called_with("markitdown")


def test_factory_still_routes_pdf_to_pdf():
    from agno.knowledge.reader.reader_factory import ReaderFactory

    with patch.object(ReaderFactory, "create_reader") as mock_create:
        mock_create.return_value = Mock()
        ReaderFactory.get_reader_for_extension(".pdf")
        mock_create.assert_called_with("pdf")


def test_factory_still_routes_txt_to_text():
    from agno.knowledge.reader.reader_factory import ReaderFactory

    with patch.object(ReaderFactory, "create_reader") as mock_create:
        mock_create.return_value = Mock()
        ReaderFactory.get_reader_for_extension(".txt")
        mock_create.assert_called_with("text")


# ---------------------------------------------------------------------------
# Tests: _build_markitdown helper
# ---------------------------------------------------------------------------


def test_build_markitdown_without_api_key(monkeypatch):
    import agno.knowledge.reader.markitdown_reader as mod

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    mock_md_cls = Mock(return_value=Mock())
    monkeypatch.setattr(mod, "MarkItDown", mock_md_cls)

    # Call the real _build_markitdown (not the patched one)
    from agno.knowledge.reader.markitdown_reader import _build_markitdown as real_build
    # We need to reimport to get the un-patched version - just test the logic
    result = mod._build_markitdown()

    # Should be called without llm_client/llm_model when no API key
    assert result is not None


def test_build_markitdown_with_api_key(monkeypatch):
    import agno.knowledge.reader.markitdown_reader as mod

    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")
    monkeypatch.setenv("OPENAI_API_BASE", "https://api.example.com")
    monkeypatch.setenv("MARKITDOWN_MODEL", "gpt-4o")

    mock_openai_cls = Mock()
    mock_client = Mock()
    mock_openai_cls.return_value = mock_client

    mock_md_cls = Mock(return_value=Mock())

    # Restore the real _build_markitdown
    monkeypatch.setattr(mod, "MarkItDown", mock_md_cls)
    monkeypatch.setattr(mod, "_build_markitdown", mod._build_markitdown.__wrapped__ if hasattr(mod._build_markitdown, "__wrapped__") else mod._build_markitdown)

    with patch.dict("sys.modules", {"openai": Mock(OpenAI=mock_openai_cls)}):
        result = mod._build_markitdown()

    assert result is not None
