from importlib.util import find_spec
import sys
from types import ModuleType
from typing import Any, List, Optional

import pytest

from agno.models.base import MessageData
from agno.models.message import Message

if find_spec("litellm") is None and "litellm" not in sys.modules:
    litellm_stub = ModuleType("litellm")
    litellm_stub.validate_environment = lambda **kwargs: {"keys_in_environment": True}  # type: ignore[attr-defined]
    sys.modules["litellm"] = litellm_stub

from agno.models.litellm import LiteLLM


class _FakeMessage:
    def __init__(self, *, content: Optional[str] = None, tool_calls: Optional[List[Any]] = None):
        self.content = content
        self.reasoning_content = None
        self.tool_calls = tool_calls


class _FakeDelta:
    def __init__(self, *, content: Optional[str] = None, tool_calls: Optional[List[Any]] = None):
        self.content = content
        self.reasoning_content = None
        self.tool_calls = tool_calls


class _FakeChoice:
    def __init__(
        self,
        *,
        message: Optional[_FakeMessage] = None,
        delta: Optional[_FakeDelta] = None,
        finish_reason: Optional[str] = None,
    ):
        self.message = message
        self.delta = delta
        self.finish_reason = finish_reason


class _FakeResponse:
    def __init__(self, *, choices: List[_FakeChoice], usage: Any = None):
        self.choices = choices
        self.usage = usage


class _FakeClient:
    def __init__(self, chunks: List[_FakeResponse]):
        self.chunks = chunks

    def completion(self, **kwargs: Any):
        return iter(self.chunks)


class _FakeAsyncClient:
    def __init__(self, chunks: List[_FakeResponse]):
        self.chunks = chunks

    async def completion(self, **kwargs: Any):
        for chunk in self.chunks:
            yield chunk


class _FakeACompletionClient:
    def __init__(self, chunks: List[_FakeResponse]):
        self.chunks = chunks

    async def acompletion(self, **kwargs: Any):
        return _FakeAsyncClient(self.chunks).completion()


def _delta(content: Optional[str] = None, finish_reason: Optional[str] = None) -> _FakeResponse:
    return _FakeResponse(choices=[_FakeChoice(delta=_FakeDelta(content=content), finish_reason=finish_reason)])


def test_delta_parser_exposes_finish_reason_in_provider_data():
    model = LiteLLM(id="gpt-4o")

    response = model._parse_provider_response_delta(_delta(finish_reason="length"))

    assert response.provider_data == {"finish_reason": "length"}
    assert response.content is None


def test_delta_parser_does_not_add_finish_reason_when_absent():
    model = LiteLLM(id="gpt-4o")

    response = model._parse_provider_response_delta(_delta(content="hello"))

    assert response.provider_data is None
    assert response.content == "hello"


def test_non_streaming_parser_exposes_finish_reason_in_provider_data():
    model = LiteLLM(id="gpt-4o")
    response = _FakeResponse(
        choices=[_FakeChoice(message=_FakeMessage(content="hello"), finish_reason="stop")],
    )

    parsed = model._parse_provider_response(response)

    assert parsed.content == "hello"
    assert parsed.provider_data == {"finish_reason": "stop"}


def test_invoke_stream_propagates_finish_reason():
    model = LiteLLM(id="gpt-4o", client=_FakeClient([_delta("hello"), _delta(finish_reason="length")]))
    assistant_message = Message(role="assistant")

    chunks = list(model.invoke_stream(messages=[Message(role="user", content="hi")], assistant_message=assistant_message))

    assert chunks[-1].provider_data == {"finish_reason": "length"}


@pytest.mark.asyncio
async def test_ainvoke_stream_propagates_finish_reason():
    model = LiteLLM(id="gpt-4o", client=_FakeACompletionClient([_delta("hello"), _delta(finish_reason="length")]))
    assistant_message = Message(role="assistant")

    chunks = [
        chunk
        async for chunk in model.ainvoke_stream(
            messages=[Message(role="user", content="hi")], assistant_message=assistant_message
        )
    ]

    assert chunks[-1].provider_data == {"finish_reason": "length"}


def test_finish_reason_survives_stream_merge_to_assistant_message():
    model = LiteLLM(id="gpt-4o")
    stream_data = MessageData()
    assistant_message = Message(role="assistant")

    for chunk in [_delta("hello"), _delta(finish_reason="length")]:
        list(model._populate_stream_data(stream_data, model._parse_provider_response_delta(chunk)))

    model._populate_assistant_message_from_stream_data(assistant_message, stream_data)

    assert assistant_message.content == "hello"
    assert assistant_message.provider_data == {"finish_reason": "length"}
