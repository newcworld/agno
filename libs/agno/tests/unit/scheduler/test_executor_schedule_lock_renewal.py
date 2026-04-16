"""Core tests for scheduler DB lock renewal during long background runs."""

import itertools
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agno.db.schemas.scheduler import Schedule
from agno.scheduler.executor import ScheduleExecutor


@pytest.fixture
def executor_default_renew() -> ScheduleExecutor:
    return ScheduleExecutor(
        base_url="http://localhost:8000",
        internal_service_token="tok",
        poll_interval=0,
        schedule_lock_renew_interval=30,
    )


class TestTouchScheduleLockIfDue:
    """Unit tests for ``ScheduleExecutor._touch_schedule_lock_if_due``."""

    @pytest.mark.asyncio
    async def test_skips_when_worker_id_missing(self, executor_default_renew: ScheduleExecutor) -> None:
        db = MagicMock(renew_schedule_lock=MagicMock(return_value=True))
        out = await executor_default_renew._touch_schedule_lock_if_due(db, "sid", None, 0.0)
        assert out == 0.0
        db.renew_schedule_lock.assert_not_called()

    @pytest.mark.asyncio
    async def test_skips_when_schedule_id_missing(self, executor_default_renew: ScheduleExecutor) -> None:
        db = MagicMock(renew_schedule_lock=MagicMock(return_value=True))
        out = await executor_default_renew._touch_schedule_lock_if_due(db, "", "wid", 0.0)
        assert out == 0.0
        db.renew_schedule_lock.assert_not_called()

    @pytest.mark.asyncio
    async def test_skips_when_interval_disabled(self) -> None:
        executor = ScheduleExecutor(
            base_url="http://localhost:8000",
            internal_service_token="tok",
            schedule_lock_renew_interval=0,
        )
        db = MagicMock(renew_schedule_lock=MagicMock(return_value=True))
        out = await executor._touch_schedule_lock_if_due(db, "sid", "wid", 0.0)
        assert out == 0.0
        db.renew_schedule_lock.assert_not_called()

    @pytest.mark.asyncio
    async def test_skips_when_db_has_no_renew_method(self, executor_default_renew: ScheduleExecutor) -> None:
        db = object()
        out = await executor_default_renew._touch_schedule_lock_if_due(db, "sid", "wid", 0.0)
        assert out == 0.0

    @pytest.mark.asyncio
    async def test_skips_before_interval_elapses(self, executor_default_renew: ScheduleExecutor) -> None:
        db = MagicMock()
        db.renew_schedule_lock = MagicMock(return_value=True)
        with patch("agno.scheduler.executor.time.monotonic", return_value=115.0):
            out = await executor_default_renew._touch_schedule_lock_if_due(db, "sid", "wid", 100.0)
        assert out == 100.0
        db.renew_schedule_lock.assert_not_called()

    @pytest.mark.asyncio
    async def test_calls_sync_renew_when_elapsed(self, executor_default_renew: ScheduleExecutor) -> None:
        db = MagicMock()
        db.renew_schedule_lock = MagicMock(return_value=True)
        with patch("agno.scheduler.executor.time.monotonic", side_effect=[150.0, 999.0]):
            out = await executor_default_renew._touch_schedule_lock_if_due(db, "sid", "wid", 100.0)
        assert out == 999.0
        db.renew_schedule_lock.assert_called_once_with("sid", "wid")

    @pytest.mark.asyncio
    async def test_calls_async_renew_when_elapsed(self, executor_default_renew: ScheduleExecutor) -> None:
        db = MagicMock()
        db.renew_schedule_lock = AsyncMock(return_value=True)
        with patch("agno.scheduler.executor.time.monotonic", side_effect=[150.0, 888.0]):
            out = await executor_default_renew._touch_schedule_lock_if_due(db, "sid", "wid", 100.0)
        assert out == 888.0
        db.renew_schedule_lock.assert_awaited_once_with("sid", "wid")

    @pytest.mark.asyncio
    async def test_false_from_renew_keeps_last_timestamp(self, executor_default_renew: ScheduleExecutor) -> None:
        db = MagicMock()
        db.renew_schedule_lock = MagicMock(return_value=False)
        with patch("agno.scheduler.executor.time.monotonic", return_value=200.0):
            out = await executor_default_renew._touch_schedule_lock_if_due(db, "sid", "wid", 100.0)
        assert out == 100.0
        db.renew_schedule_lock.assert_called_once()

    @pytest.mark.asyncio
    async def test_exception_from_renew_keeps_last_timestamp(self, executor_default_renew: ScheduleExecutor) -> None:
        db = MagicMock()
        db.renew_schedule_lock = MagicMock(side_effect=RuntimeError("db unavailable"))
        with patch("agno.scheduler.executor.time.monotonic", return_value=200.0):
            out = await executor_default_renew._touch_schedule_lock_if_due(db, "sid", "wid", 100.0)
        assert out == 100.0


class TestPollRunLockRenewal:
    """``_poll_run`` should invoke lock renewal on long-poll paths."""

    @pytest.mark.asyncio
    async def test_poll_run_triggers_touch_each_iteration(self) -> None:
        executor = ScheduleExecutor(
            base_url="http://localhost:8000",
            internal_service_token="tok",
            poll_interval=0,
            schedule_lock_renew_interval=1,
        )
        db = MagicMock()
        db.renew_schedule_lock = MagicMock(return_value=True)

        call_count = 0

        async def mock_request(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            resp = MagicMock()
            if call_count == 1:
                resp.status_code = 200
                resp.json = MagicMock(return_value={"status": "RUNNING"})
            else:
                resp.status_code = 200
                resp.json = MagicMock(return_value={"status": "COMPLETED"})
            return resp

        mock_client = AsyncMock()
        mock_client.request = mock_request

        tick = itertools.count(0.0, 12.0)
        with patch("agno.scheduler.executor.time.monotonic", side_effect=lambda: float(next(tick))):
            result = await executor._poll_run(
                mock_client,
                {},
                "agents",
                "a1",
                "run-1",
                "sess-1",
                86_400,
                db,
                "sched-z",
                "worker-z",
            )

        assert result["status"] == "success"
        assert call_count == 2
        assert db.renew_schedule_lock.call_count >= 1


class TestExecuteForwardsWorkerId:
    """``execute`` must pass ``worker_id`` into the endpoint layer for background runs."""

    @pytest.mark.asyncio
    async def test_execute_passes_worker_id_to_call_endpoint(self) -> None:
        executor = ScheduleExecutor(
            base_url="http://localhost:8000",
            internal_service_token="tok",
            poll_interval=0,
        )
        schedule = {
            "id": "sched-exec",
            "name": "t",
            "cron_expr": "* * * * *",
            "timezone": "UTC",
            "endpoint": "/agents/x/runs",
            "method": "POST",
            "payload": {"message": "m"},
            "max_retries": 0,
            "retry_delay_seconds": 0,
        }
        mock_db = MagicMock()
        mock_db.create_schedule_run = MagicMock()
        mock_db.update_schedule_run = MagicMock()
        mock_db.release_schedule = MagicMock()

        captured: dict = {}

        async def capture_call(sched: Schedule, db: object, worker_id: object) -> dict:
            captured["worker_id"] = worker_id
            return {
                "status": "success",
                "status_code": 200,
                "error": None,
                "run_id": None,
                "session_id": None,
                "input": None,
                "output": None,
                "requirements": None,
            }

        with patch.object(executor, "_call_endpoint", side_effect=capture_call):
            await executor.execute(schedule, mock_db, worker_id="poller-worker-9")

        assert captured["worker_id"] == "poller-worker-9"


class TestRetryLoopLockRenewal:
    """Between retry attempts the executor should attempt a lock heartbeat."""

    @pytest.mark.asyncio
    @patch("agno.scheduler.executor.asyncio.sleep", new_callable=AsyncMock)
    async def test_retry_path_calls_touch_before_sleep(self, mock_sleep: AsyncMock) -> None:
        executor = ScheduleExecutor(
            base_url="http://localhost:8000",
            internal_service_token="tok",
            poll_interval=0,
            schedule_lock_renew_interval=10,
        )
        schedule = {
            "id": "sched-retry",
            "name": "t",
            "cron_expr": "* * * * *",
            "timezone": "UTC",
            "endpoint": "/config",
            "method": "GET",
            "payload": None,
            "max_retries": 1,
            "retry_delay_seconds": 5,
        }
        mock_db = MagicMock()
        mock_db.create_schedule_run = MagicMock()
        mock_db.update_schedule_run = MagicMock()
        mock_db.release_schedule = MagicMock()
        mock_db.renew_schedule_lock = MagicMock(return_value=True)

        call_count = 0

        async def fail_then_ok(*_a, **_kw):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise RuntimeError("transient")
            return {
                "status": "success",
                "status_code": 200,
                "error": None,
                "run_id": None,
                "session_id": None,
                "input": None,
                "output": None,
                "requirements": None,
            }

        tick = itertools.count(1000.0, 25.0)
        with patch.object(executor, "_call_endpoint", side_effect=fail_then_ok):
            with patch("agno.scheduler.executor.time.monotonic", side_effect=lambda: float(next(tick))):
                result = await executor.execute(schedule, mock_db, worker_id="w-retry")

        assert result["status"] == "success"
        assert mock_db.renew_schedule_lock.call_count >= 1
        assert all(
            call.args == ("sched-retry", "w-retry") for call in mock_db.renew_schedule_lock.call_args_list
        )
        mock_sleep.assert_awaited_once()

    @pytest.mark.asyncio
    @patch("agno.scheduler.executor.asyncio.sleep", new_callable=AsyncMock)
    async def test_retry_sleep_bumps_lock_even_when_touch_throttled(self, mock_sleep: AsyncMock) -> None:
        """Throttled ``_touch`` must not be the only heartbeat: sleep can exceed lock grace."""
        executor = ScheduleExecutor(
            base_url="http://localhost:8000",
            internal_service_token="tok",
            poll_interval=0,
            schedule_lock_renew_interval=86_400,
        )
        schedule = {
            "id": "sched-sleep-bump",
            "name": "t",
            "cron_expr": "* * * * *",
            "timezone": "UTC",
            "endpoint": "/config",
            "method": "GET",
            "payload": None,
            "max_retries": 1,
            "retry_delay_seconds": 2,
        }
        mock_db = MagicMock()
        mock_db.create_schedule_run = MagicMock()
        mock_db.update_schedule_run = MagicMock()
        mock_db.release_schedule = MagicMock()
        mock_db.renew_schedule_lock = MagicMock(return_value=True)

        st = {"n": 0}

        async def fail_then_ok(*_a, **_kw):
            if st["n"] == 0:
                st["n"] = 1
                raise RuntimeError("transient")
            return {
                "status": "success",
                "status_code": 200,
                "error": None,
                "run_id": None,
                "session_id": None,
                "input": None,
                "output": None,
                "requirements": None,
            }

        with patch.object(executor, "_call_endpoint", side_effect=fail_then_ok):
            with patch("agno.scheduler.executor.time.monotonic", return_value=0.0):
                await executor.execute(schedule, mock_db, worker_id="w-sleep")

        assert mock_db.renew_schedule_lock.call_count >= 1
        mock_db.renew_schedule_lock.assert_any_call("sched-sleep-bump", "w-sleep")

    @pytest.mark.asyncio
    @patch("agno.scheduler.executor.asyncio.sleep", new_callable=AsyncMock)
    async def test_retry_path_invokes_touch_hook_even_if_renew_disabled(self, mock_sleep: AsyncMock) -> None:
        """Guarantees the retry branch awaits ``_touch_schedule_lock_if_due`` (regression guard)."""
        executor = ScheduleExecutor(
            base_url="http://localhost:8000",
            internal_service_token="tok",
            poll_interval=0,
            schedule_lock_renew_interval=0,
        )
        schedule = {
            "id": "sched-retry-2",
            "name": "t",
            "cron_expr": "* * * * *",
            "timezone": "UTC",
            "endpoint": "/config",
            "method": "GET",
            "payload": None,
            "max_retries": 1,
            "retry_delay_seconds": 1,
        }
        mock_db = MagicMock()
        mock_db.create_schedule_run = MagicMock()
        mock_db.update_schedule_run = MagicMock()
        mock_db.release_schedule = MagicMock()

        attempt = {"n": 0}

        async def fail_then_ok(*_a, **_kw):
            if attempt["n"] == 0:
                attempt["n"] = 1
                raise RuntimeError("transient")
            return {
                "status": "success",
                "status_code": 200,
                "error": None,
                "run_id": None,
                "session_id": None,
                "input": None,
                "output": None,
                "requirements": None,
            }

        touch = AsyncMock(side_effect=lambda _db, sid, wid, last: last)
        with patch.object(executor, "_touch_schedule_lock_if_due", touch):
            with patch.object(executor, "_call_endpoint", side_effect=fail_then_ok):
                await executor.execute(schedule, mock_db, worker_id="w-2")

        touch.assert_awaited()
        assert touch.await_args_list[0].args[2] == "w-2"
