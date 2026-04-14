import asyncio
import os
from io import BytesIO
from pathlib import Path
from typing import IO, Any, Dict, List, Optional, Union
from uuid import uuid4

from agno.knowledge.chunking.document import DocumentChunking
from agno.knowledge.chunking.strategy import ChunkingStrategy, ChunkingStrategyType
from agno.knowledge.document.base import Document
from agno.knowledge.reader.base import Reader
from agno.knowledge.types import ContentType
from agno.utils.log import log_debug, log_error

try:
    from markitdown import MarkItDown

    _MARKITDOWN_AVAILABLE = True
except ImportError:
    _MARKITDOWN_AVAILABLE = False
    MarkItDown = None  # type: ignore[assignment,misc]


def _build_markitdown(**kwargs) -> "MarkItDown":
    """Build a MarkItDown instance, optionally with LLM vision support for images."""
    api_key = os.getenv("OPENAI_API_KEY")
    api_base = os.getenv("OPENAI_API_BASE")

    if api_key:
        try:
            from openai import OpenAI

            client_kwargs: Dict[str, Any] = {"api_key": api_key}
            if api_base:
                client_kwargs["base_url"] = api_base
            client = OpenAI(**client_kwargs)
            model = os.getenv("MARKITDOWN_MODEL", "gpt-4o-mini")
            return MarkItDown(llm_client=client, llm_model=model, **kwargs)
        except Exception:
            pass

    return MarkItDown(**kwargs)


class MarkItDownReader(Reader):
    """Reader that uses Microsoft's MarkItDown to convert files to Markdown.

    Supports PDF, DOCX, PPTX, XLSX, HTML, images (with LLM vision), audio,
    CSV, JSON, XML, ZIP, and more — all without heavy ML dependencies like torch.

    For images, set OPENAI_API_KEY (and optionally OPENAI_API_BASE / MARKITDOWN_MODEL)
    to enable LLM-powered image descriptions.
    """

    def __init__(
        self,
        chunking_strategy: Optional[ChunkingStrategy] = None,
        **kwargs,
    ):
        if not _MARKITDOWN_AVAILABLE:
            raise ImportError(
                "The `markitdown` package is not installed. "
                "Install it via: pip install 'markitdown[pdf,docx,pptx,xlsx]'"
            )
        if chunking_strategy is None:
            chunk_size = kwargs.get("chunk_size", 5000)
            chunking_strategy = DocumentChunking(chunk_size=chunk_size)
        super().__init__(chunking_strategy=chunking_strategy, **kwargs)
        self._md = _build_markitdown()

    @classmethod
    def get_supported_chunking_strategies(cls) -> List[ChunkingStrategyType]:
        return [
            ChunkingStrategyType.DOCUMENT_CHUNKER,
            ChunkingStrategyType.FIXED_SIZE_CHUNKER,
            ChunkingStrategyType.AGENTIC_CHUNKER,
            ChunkingStrategyType.RECURSIVE_CHUNKER,
            ChunkingStrategyType.SEMANTIC_CHUNKER,
        ]

    @classmethod
    def get_supported_content_types(cls) -> List[ContentType]:
        return [
            ContentType.IMAGE_PNG,
            ContentType.IMAGE_JPEG,
            ContentType.IMAGE_JPG,
            ContentType.IMAGE_TIFF,
            ContentType.IMAGE_TIF,
            ContentType.IMAGE_BMP,
            ContentType.IMAGE_WEBP,
            ContentType.HTML,
            ContentType.HTM,
        ]

    def _convert(self, source: Any, name: Optional[str] = None) -> str:
        """Run MarkItDown conversion and return markdown text."""
        if isinstance(source, (str, Path)):
            result = self._md.convert(str(source))
        else:
            # BytesIO / file-like object
            source.seek(0)
            ext = None
            if name:
                ext = Path(name).suffix or None
            result = self._md.convert_stream(source, file_extension=ext)
        return result.text_content or ""

    def read(self, file: Union[Path, str, IO[Any]], name: Optional[str] = None) -> List[Document]:
        try:
            if isinstance(file, Path):
                if not file.exists():
                    raise FileNotFoundError(f"Could not find file: {file}")
                log_debug(f"Reading: {file}")
                doc_name = name or file.stem
            elif isinstance(file, str):
                doc_name = name or Path(file).stem
            else:
                log_debug(f"Reading uploaded file: {getattr(file, 'name', 'BytesIO')}")
                if name and "." in name:
                    doc_name = Path(name).stem
                else:
                    doc_name = name or getattr(file, "name", "markitdown_file").split(".")[0]

            content = self._convert(file, name=name)
            if not content.strip():
                log_error(f"MarkItDown returned empty content for: {doc_name}")
                return []

            documents = [Document(name=doc_name, id=str(uuid4()), content=content)]

            if self.chunk:
                chunked = []
                for doc in documents:
                    chunked.extend(self.chunk_document(doc))
                return chunked
            return documents

        except (FileNotFoundError, ValueError):
            raise
        except Exception as e:
            log_error(f"Error converting document with MarkItDown: {e}")
            return []

    async def async_read(self, file: Union[Path, str, IO[Any]], name: Optional[str] = None) -> List[Document]:
        try:
            return await asyncio.to_thread(self.read, file, name)
        except (FileNotFoundError, ValueError):
            raise
        except Exception as e:
            log_error(f"Error reading file asynchronously with MarkItDown: {e}")
            return []
