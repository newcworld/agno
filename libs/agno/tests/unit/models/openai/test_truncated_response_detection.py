from typing import Any, List, Optional

import pytest

from agno.exceptions import ContextWindowExceededError
from agno.models.message import Message
from agno.models.openai.chat import OpenAIChat
from agno.models.openai.responses import OpenAIResponses


class _FakeChatMessage:
    def __init__(self, *, content: Optional[str] = None, tool_calls: Optional[List[Any]] = None):
        self.role = "assistant"
        self.content = content
        self.tool_calls = tool_calls
        self.audio = None


class _FakeChatChoice:
    def __init__(self, *, message: _FakeChatMessage, finish_reason: str):
        self.message = message
        self.finish_reason = finish_reason


class _FakeChatCompletion:
    def __init__(self, *, message: _FakeChatMessage, finish_reason: str):
        self.choices = [_FakeChatChoice(message=message, finish_reason=finish_reason)]
        self.usage = None
        self.id = "chatcmpl_1"
        self.system_fingerprint = None
        self.model_extra = None
        self.error = None


class _FakeFunction:
    def __init__(self):
        self.name = "lookup"
        self.arguments = "{}"


class _FakeToolCall:
    def __init__(self):
        self.id = "call_1"
        self.type = "function"
        self.function = _FakeFunction()

    def model_dump(self):
        return {"id": self.id, "type": self.type, "function": {"name": "lookup", "arguments": "{}"}}


class _FakeIncompleteDetails:
    def __init__(self, reason: str):
        self.reason = reason


class _FakeOutputText:
    def __init__(self, text: str, annotations: Optional[List[Any]] = None):
        self.type = "output_text"
        self.text = text
        self.annotations = annotations or []


class _FakeMessageOutput:
    def __init__(self, text: str):
        self.type = "message"
        self.content = [_FakeOutputText(text)]


class _FakeFunctionCallOutput:
    def __init__(self):
        self.type = "function_call"
        self.id = "fc_1"
        self.call_id = "call_1"
        self.name = "lookup"
        self.arguments = "{}"


class _FakeResponsesResponse:
    def __init__(
        self,
        *,
        status: str = "completed",
        output: Optional[List[Any]] = None,
        output_text: str = "",
        incomplete_details: Any = None,
    ):
        self.id = "resp_1"
        self.status = status
        self.output = output or []
        self.output_text = output_text
        self.usage = None
        self.error = None
        self.incomplete_details = incomplete_details


class _FakeStreamEvent:
    def __init__(self, *, type: str = "response.completed", response: Optional[_FakeResponsesResponse] = None, delta: str = ""):
        self.type = type
        self.response = response
        self.delta = delta


def test_openai_chat_empty_length_response_raises_context_window_error():
    model = OpenAIChat(id="gpt-4.1-mini")
    response = _FakeChatCompletion(message=_FakeChatMessage(content=None), finish_reason="length")

    with pytest.raises(ContextWindowExceededError, match="context_length_exceeded"):
        model._parse_provider_response(response)  # type: ignore[arg-type]


def test_openai_chat_partial_length_response_is_allowed():
    model = OpenAIChat(id="gpt-4.1-mini")
    response = _FakeChatCompletion(message=_FakeChatMessage(content="partial"), finish_reason="length")

    parsed = model._parse_provider_response(response)  # type: ignore[arg-type]

    assert parsed.content == "partial"


def test_openai_chat_tool_call_length_response_is_allowed():
    model = OpenAIChat(id="gpt-4.1-mini")
    response = _FakeChatCompletion(
        message=_FakeChatMessage(tool_calls=[_FakeToolCall()]),
        finish_reason="length",
    )

    parsed = model._parse_provider_response(response)  # type: ignore[arg-type]

    assert parsed.tool_calls[0]["id"] == "call_1"


def test_openai_responses_incomplete_empty_response_raises_context_window_error():
    model = OpenAIResponses(id="gpt-4.1-mini")
    response = _FakeResponsesResponse(
        status="incomplete",
        incomplete_details=_FakeIncompleteDetails("max_output_tokens"),
    )

    with pytest.raises(ContextWindowExceededError, match="context_length_exceeded"):
        model._parse_provider_response(response)  # type: ignore[arg-type]


def test_openai_responses_incomplete_with_partial_content_is_allowed():
    model = OpenAIResponses(id="gpt-4.1-mini")
    response = _FakeResponsesResponse(
        status="incomplete",
        output=[_FakeMessageOutput("partial")],
        output_text="partial",
        incomplete_details={"reason": "max_output_tokens"},
    )

    parsed = model._parse_provider_response(response)  # type: ignore[arg-type]

    assert parsed.content == "partial"


def test_openai_responses_incomplete_with_tool_call_is_allowed():
    model = OpenAIResponses(id="gpt-4.1-mini")
    response = _FakeResponsesResponse(
        status="incomplete",
        output=[_FakeFunctionCallOutput()],
        incomplete_details=_FakeIncompleteDetails("max_output_tokens"),
    )

    parsed = model._parse_provider_response(response)  # type: ignore[arg-type]

    assert parsed.tool_calls[0]["id"] == "fc_1"


def test_openai_responses_streaming_incomplete_empty_response_raises_context_window_error():
    model = OpenAIResponses(id="gpt-4.1-mini")
    assistant_message = Message(role="assistant")
    response = _FakeResponsesResponse(
        status="incomplete",
        incomplete_details=_FakeIncompleteDetails("max_output_tokens"),
    )

    with pytest.raises(ContextWindowExceededError, match="context_length_exceeded"):
        model._parse_provider_response_delta(  # type: ignore[arg-type]
            _FakeStreamEvent(response=response), assistant_message, {}
        )


def test_openai_responses_streaming_incomplete_with_content_is_allowed():
    model = OpenAIResponses(id="gpt-4.1-mini")
    assistant_message = Message(role="assistant")
    response = _FakeResponsesResponse(
        status="incomplete",
        output=[_FakeMessageOutput("partial")],
        output_text="partial",
        incomplete_details=_FakeIncompleteDetails("max_output_tokens"),
    )

    parsed, tool_use = model._parse_provider_response_delta(  # type: ignore[arg-type]
        _FakeStreamEvent(response=response), assistant_message, {}
    )

    assert parsed.response_usage is None
    assert tool_use == {}


def test_openai_responses_streaming_incomplete_after_text_delta_is_allowed():
    model = OpenAIResponses(id="gpt-4.1-mini")
    assistant_message = Message(role="assistant")
    response = _FakeResponsesResponse(
        status="incomplete",
        incomplete_details=_FakeIncompleteDetails("max_output_tokens"),
    )

    model._parse_provider_response_delta(  # type: ignore[arg-type]
        _FakeStreamEvent(type="response.output_text.delta", delta="partial"), assistant_message, {}
    )
    parsed, tool_use = model._parse_provider_response_delta(  # type: ignore[arg-type]
        _FakeStreamEvent(response=response), assistant_message, {}
    )

    assert assistant_message.content == "partial"
    assert parsed.response_usage is None
    assert tool_use == {}
