"""Tests for tool_call_timeout feature in Model and Agent.

Covers:
- Model.tool_call_timeout attribute defaults and propagation
- Sync timeout in Model.run_function_call via concurrent.futures
- Async timeout in Model.arun_function_call via asyncio.wait_for
- Agent.tool_call_timeout parameter and flow to Model via _init
- Storage serialization/deserialization of tool_call_timeout
- Normal execution (no timeout set, no timeout triggered)
"""

import asyncio
import os
import time
from unittest.mock import MagicMock

import pytest

os.environ.setdefault("OPENAI_API_KEY", "test-key-for-testing")

from agno.agent.agent import Agent
from agno.models.openai.chat import OpenAIChat
from agno.tools.function import Function, FunctionCall, FunctionExecutionResult


# =============================================================================
# Helpers
# =============================================================================


def _make_slow_tool(duration: float = 5.0):
    """Create a tool function that blocks for `duration` seconds."""

    def slow_tool() -> str:
        """A tool that sleeps."""
        time.sleep(duration)
        return "completed"

    return slow_tool


def _make_fast_tool():
    """Create a tool function that returns immediately."""

    def fast_tool() -> str:
        """A tool that returns instantly."""
        return "fast result"

    return fast_tool


async def _async_slow_tool() -> str:
    """An async tool that sleeps for 5 seconds."""
    await asyncio.sleep(5.0)
    return "async completed"


async def _async_fast_tool() -> str:
    """An async tool that returns instantly."""
    return "async fast result"


def _build_function_call(entrypoint, name="test_tool"):
    """Build a FunctionCall from an entrypoint."""
    func = Function(name=name, entrypoint=entrypoint)
    return FunctionCall(function=func, arguments={})


@pytest.fixture
def model():
    """Create a basic model for testing."""
    return OpenAIChat(id="gpt-4o-mini")


# =============================================================================
# Tests for Model.tool_call_timeout attribute
# =============================================================================


class TestModelToolCallTimeoutAttribute:
    def test_default_is_none(self, model):
        """tool_call_timeout defaults to None (no timeout)."""
        assert model.tool_call_timeout is None

    def test_can_be_set(self, model):
        """tool_call_timeout can be set on the model."""
        model.tool_call_timeout = 30
        assert model.tool_call_timeout == 30

    def test_can_be_set_to_none(self, model):
        """tool_call_timeout can be explicitly set to None."""
        model.tool_call_timeout = 60
        model.tool_call_timeout = None
        assert model.tool_call_timeout is None


# =============================================================================
# Tests for sync timeout (Model.run_function_call)
# =============================================================================


class TestSyncToolCallTimeout:
    def test_slow_tool_times_out(self, model):
        """A slow tool is terminated after tool_call_timeout seconds."""
        model.tool_call_timeout = 1
        fc = _build_function_call(_make_slow_tool(10.0))

        start = time.time()
        results = list(model.run_function_call(function_call=fc, function_call_results=[]))
        elapsed = time.time() - start

        assert elapsed < 3.0, f"Should have timed out in ~1s but took {elapsed:.1f}s"
        assert fc.error is not None
        assert "timed out" in fc.error

    def test_fast_tool_succeeds_with_timeout_set(self, model):
        """A fast tool completes normally even when timeout is set."""
        model.tool_call_timeout = 10
        fc = _build_function_call(_make_fast_tool())

        results = list(model.run_function_call(function_call=fc, function_call_results=[]))
        assert fc.error is None
        assert fc.result == "fast result"

    def test_no_timeout_lets_tool_run(self, model):
        """When tool_call_timeout is None, tools run without time limit."""
        model.tool_call_timeout = None
        fc = _build_function_call(_make_slow_tool(0.2))

        start = time.time()
        results = list(model.run_function_call(function_call=fc, function_call_results=[]))
        elapsed = time.time() - start

        assert fc.error is None
        assert fc.result == "completed"
        assert elapsed < 2.0

    def test_timeout_returns_failure_result(self, model):
        """Timed-out tool produces a tool_call_completed event with error."""
        model.tool_call_timeout = 1
        fc = _build_function_call(_make_slow_tool(10.0))

        from agno.models.response import ModelResponse, ModelResponseEvent

        events = list(model.run_function_call(function_call=fc, function_call_results=[]))
        started_events = [e for e in events if isinstance(e, ModelResponse) and e.event == ModelResponseEvent.tool_call_started.value]
        completed_events = [e for e in events if isinstance(e, ModelResponse) and e.event == ModelResponseEvent.tool_call_completed.value]

        assert len(started_events) == 1
        assert len(completed_events) == 1

    def test_timeout_error_message_includes_duration(self, model):
        """Timeout error message includes the timeout duration."""
        model.tool_call_timeout = 2
        fc = _build_function_call(_make_slow_tool(10.0))

        list(model.run_function_call(function_call=fc, function_call_results=[]))
        assert "2 seconds" in fc.error


# =============================================================================
# Tests for async timeout (Model.arun_function_call)
# =============================================================================


class TestAsyncToolCallTimeout:
    @pytest.mark.asyncio
    async def test_sync_slow_tool_times_out_async(self, model):
        """A sync slow tool run via asyncio.to_thread is terminated after timeout."""
        model.tool_call_timeout = 1
        fc = _build_function_call(_make_slow_tool(10.0))

        start = time.time()
        success, timer, fc_result, exec_result = await model.arun_function_call(function_call=fc)
        elapsed = time.time() - start

        assert elapsed < 3.0, f"Should have timed out in ~1s but took {elapsed:.1f}s"
        assert success is False
        assert fc.error is not None
        assert "timed out" in fc.error

    @pytest.mark.asyncio
    async def test_async_slow_tool_times_out(self, model):
        """An async slow tool is terminated after timeout."""
        model.tool_call_timeout = 1
        fc = _build_function_call(_async_slow_tool)

        start = time.time()
        success, timer, fc_result, exec_result = await model.arun_function_call(function_call=fc)
        elapsed = time.time() - start

        assert elapsed < 3.0, f"Should have timed out in ~1s but took {elapsed:.1f}s"
        assert success is False
        assert fc.error is not None
        assert "timed out" in fc.error

    @pytest.mark.asyncio
    async def test_async_fast_tool_succeeds_with_timeout(self, model):
        """A fast async tool completes normally when timeout is set."""
        model.tool_call_timeout = 10
        fc = _build_function_call(_async_fast_tool)

        success, timer, fc_result, exec_result = await model.arun_function_call(function_call=fc)
        assert success is True
        assert fc.error is None

    @pytest.mark.asyncio
    async def test_sync_fast_tool_succeeds_with_timeout_async(self, model):
        """A fast sync tool completes normally in async path when timeout is set."""
        model.tool_call_timeout = 10
        fc = _build_function_call(_make_fast_tool())

        success, timer, fc_result, exec_result = await model.arun_function_call(function_call=fc)
        assert success is True
        assert fc.error is None

    @pytest.mark.asyncio
    async def test_no_timeout_lets_async_tool_run(self, model):
        """When tool_call_timeout is None, async tools run without time limit."""
        model.tool_call_timeout = None
        fc = _build_function_call(_async_fast_tool)

        success, timer, fc_result, exec_result = await model.arun_function_call(function_call=fc)
        assert success is True
        assert fc.error is None

    @pytest.mark.asyncio
    async def test_timeout_error_message_includes_duration_async(self, model):
        """Timeout error message includes the timeout duration in async path."""
        model.tool_call_timeout = 2
        fc = _build_function_call(_async_slow_tool)

        success, timer, fc_result, exec_result = await model.arun_function_call(function_call=fc)
        assert "2 seconds" in fc.error


# =============================================================================
# Tests for Agent.tool_call_timeout parameter
# =============================================================================


class TestAgentToolCallTimeout:
    def test_agent_default_is_none(self):
        """Agent.tool_call_timeout defaults to None."""
        agent = Agent(name="test")
        assert agent.tool_call_timeout is None

    def test_agent_accepts_timeout(self):
        """Agent constructor accepts tool_call_timeout."""
        agent = Agent(name="test", tool_call_timeout=60)
        assert agent.tool_call_timeout == 60

    def test_agent_propagates_to_model(self):
        """Agent.tool_call_timeout is propagated to Model during init."""
        agent = Agent(
            model=OpenAIChat(id="gpt-4o-mini"),
            tool_call_timeout=45,
        )
        assert agent.model is not None
        assert agent.model.tool_call_timeout == 45

    def test_agent_none_does_not_override_model(self):
        """When Agent.tool_call_timeout is None, Model.tool_call_timeout stays None."""
        agent = Agent(
            model=OpenAIChat(id="gpt-4o-mini"),
            tool_call_timeout=None,
        )
        assert agent.model is not None
        assert agent.model.tool_call_timeout is None

    def test_agent_model_timeout_independent(self):
        """Model can have its own timeout set independently from Agent."""
        m = OpenAIChat(id="gpt-4o-mini")
        m.tool_call_timeout = 30
        agent = Agent(model=m, tool_call_timeout=60)
        # Agent's value takes precedence during init
        assert agent.model.tool_call_timeout == 60


# =============================================================================
# Tests for storage serialization (to_dict / from_dict)
# =============================================================================


class TestToolCallTimeoutStorage:
    def test_serialize_timeout(self):
        """tool_call_timeout is included in to_dict output."""
        from agno.agent import _storage

        agent = Agent(name="test", tool_call_timeout=90)
        config = _storage.to_dict(agent)
        assert config.get("tool_call_timeout") == 90

    def test_serialize_none_timeout_not_in_config(self):
        """tool_call_timeout=None is not included in serialized config."""
        from agno.agent import _storage

        agent = Agent(name="test", tool_call_timeout=None)
        config = _storage.to_dict(agent)
        assert "tool_call_timeout" not in config

    def test_roundtrip_preserves_timeout(self):
        """tool_call_timeout survives a to_dict -> from_dict roundtrip."""
        from agno.agent import _storage

        agent = Agent(name="roundtrip-test", tool_call_timeout=75)
        config = _storage.to_dict(agent)
        restored = _storage.from_dict(Agent, config)
        assert restored.tool_call_timeout == 75

    def test_roundtrip_missing_timeout_defaults_none(self):
        """Missing tool_call_timeout in config defaults to None after from_dict."""
        from agno.agent import _storage

        agent = Agent(name="no-timeout-test")
        config = _storage.to_dict(agent)
        assert "tool_call_timeout" not in config
        restored = _storage.from_dict(Agent, config)
        assert restored.tool_call_timeout is None
