import asyncio
from contextlib import suppress
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.scheduler import MetricCleanupScheduler
from app.middleware import MetricMiddleware

pytestmark = pytest.mark.asyncio


async def test_run_cleanup_loop_runs_cleanup():
    """run_cleanup_loop calls cleanup_old_metrics before sleeping."""
    cleanup_calls = []

    async def fake_cleanup(_session, retention_days):
        cleanup_calls.append(retention_days)
        return 5

    with (
        patch("app.core.scheduler.asyncio.sleep", new=AsyncMock()) as mock_sleep,
        patch("app.core.scheduler.db.AsyncSessionLocal") as mock_session_factory,
        patch(
            "app.core.scheduler.metric_service.cleanup_old_metrics",
            side_effect=fake_cleanup,
        ),
        patch("app.core.scheduler.settings") as mock_settings,
    ):
        mock_settings.METRIC_CLEANUP_INTERVAL_HOURS = 24
        mock_settings.METRIC_RETENTION_DAYS = 90

        mock_session = AsyncMock()
        mock_session_factory.return_value.__aenter__ = AsyncMock(
            return_value=mock_session
        )
        mock_session_factory.return_value.__aexit__ = AsyncMock(return_value=False)

        # Cleanup runs first, then sleep; cancel on the first sleep
        mock_sleep.side_effect = [asyncio.CancelledError()]

        scheduler = MetricCleanupScheduler()
        with pytest.raises(asyncio.CancelledError):
            await scheduler.run_cleanup_loop()

    mock_sleep.assert_called_once_with(24 * 3600)
    assert cleanup_calls == [90]


async def test_run_cleanup_loop_handles_exception():
    """run_cleanup_loop logs exceptions and continues without crashing."""
    with (
        patch(
            "app.core.scheduler.asyncio.sleep",
            new=AsyncMock(side_effect=asyncio.CancelledError()),
        ),
        patch("app.core.scheduler.db.AsyncSessionLocal") as mock_session_factory,
        patch("app.core.scheduler.settings") as mock_settings,
        patch("app.core.scheduler.logger") as mock_logger,
        pytest.raises(asyncio.CancelledError),
    ):
        mock_settings.METRIC_CLEANUP_INTERVAL_HOURS = 1
        mock_settings.METRIC_RETENTION_DAYS = 30

        mock_session_factory.return_value.__aenter__ = AsyncMock(
            side_effect=RuntimeError("DB unavailable")
        )
        mock_session_factory.return_value.__aexit__ = AsyncMock(return_value=False)

        scheduler = MetricCleanupScheduler()
        await scheduler.run_cleanup_loop()

    mock_logger.exception.assert_called_once_with("Metric cleanup failed")


async def test_run_cleanup_loop_is_cancellable():
    """run_cleanup_loop can be cancelled cleanly while sleeping."""
    with (
        patch(
            "app.core.scheduler.asyncio.sleep",
            new=AsyncMock(side_effect=asyncio.CancelledError()),
        ),
        patch("app.core.scheduler.db.AsyncSessionLocal") as mock_session_factory,
        patch("app.core.scheduler.metric_service.cleanup_old_metrics", new=AsyncMock()),
        patch("app.core.scheduler.settings") as mock_settings,
        pytest.raises(asyncio.CancelledError),
    ):
        mock_settings.METRIC_CLEANUP_INTERVAL_HOURS = 1
        mock_settings.METRIC_RETENTION_DAYS = 90
        mock_session = AsyncMock()
        mock_session_factory.return_value.__aenter__ = AsyncMock(
            return_value=mock_session
        )
        mock_session_factory.return_value.__aexit__ = AsyncMock(return_value=False)
        scheduler = MetricCleanupScheduler()
        await scheduler.run_cleanup_loop()


async def test_metric_cleanup_scheduler_start_is_idempotent():
    """MetricCleanupScheduler.start does not create duplicate running tasks."""
    scheduler = MetricCleanupScheduler()
    started = asyncio.Event()
    blocker = asyncio.Event()

    async def fake_run_cleanup_loop(_self: MetricCleanupScheduler) -> None:
        started.set()
        await blocker.wait()

    with patch.object(
        MetricCleanupScheduler,
        "run_cleanup_loop",
        new=fake_run_cleanup_loop,
    ):
        scheduler.start()
        await started.wait()
        first_task = scheduler._task
        scheduler.start()

    assert scheduler._task is first_task
    assert first_task is not None
    assert not first_task.done()

    first_task.cancel()
    with suppress(asyncio.CancelledError):
        await first_task


async def test_metric_cleanup_scheduler_stop_cancels_task_and_clears_reference():
    """MetricCleanupScheduler.stop cancels the task and clears the reference."""
    scheduler = MetricCleanupScheduler()
    task = MagicMock()
    scheduler._task = task

    async def fake_wait(aws, *, timeout=None):  # noqa: ARG001
        return (aws, set())  # all tasks reported as done

    with (
        patch("app.core.scheduler.asyncio.wait", new=fake_wait),
        patch("app.core.scheduler.logger") as mock_logger,
    ):
        await scheduler.stop(timeout_seconds=5)

    task.cancel.assert_called_once()
    mock_logger.info.assert_called_once_with("Cleanup scheduler stopped")
    assert scheduler._task is None


async def test_metric_cleanup_scheduler_stop_timeout_keeps_running_reference():
    """MetricCleanupScheduler.stop logs a warning and keeps reference on timeout."""
    scheduler = MetricCleanupScheduler()
    task = MagicMock()
    scheduler._task = task

    async def fake_wait_timeout(aws, *, timeout=None):  # noqa: ARG001
        return (set(), aws)  # no tasks done within timeout

    with (
        patch("app.core.scheduler.asyncio.wait", new=fake_wait_timeout),
        patch("app.core.scheduler.logger") as mock_logger,
    ):
        await scheduler.stop(timeout_seconds=5)

    task.cancel.assert_called_once()
    mock_logger.warning.assert_called_once_with(
        "Timed out waiting for cleanup scheduler to stop after %.1fs",
        5,
    )
    assert scheduler._task is task


async def test_metric_cleanup_scheduler_stop_cancels_real_task():
    """MetricCleanupScheduler.stop cleanly cancels a real asyncio.Task."""
    scheduler = MetricCleanupScheduler()

    async def block_forever() -> None:
        await asyncio.sleep(9999)

    scheduler._task = asyncio.create_task(block_forever())
    await asyncio.sleep(0)  # allow the task to start

    await scheduler.stop(timeout_seconds=1.0)

    assert scheduler._task is None


async def test_metric_middleware_registers_on_app_state():
    """MetricMiddleware registers itself on app_state when provided."""
    mock_app = AsyncMock()
    app_state = MagicMock()

    middleware = MetricMiddleware(mock_app, app_state=app_state)

    assert app_state.metric_middleware is middleware


async def test_metric_middleware_no_app_state():
    """MetricMiddleware works normally when no app_state is provided."""
    mock_app = AsyncMock()
    middleware = MetricMiddleware(mock_app)

    assert middleware._background_tasks == set()
    assert middleware._project_id is None


async def test_metric_middleware_drain_background_tasks_waits_for_tasks():
    """MetricMiddleware drains in-flight background tasks successfully."""
    mock_app = AsyncMock()
    middleware = MetricMiddleware(mock_app)

    task = asyncio.create_task(asyncio.sleep(0))
    middleware._background_tasks.add(task)
    task.add_done_callback(middleware._background_tasks.discard)

    await middleware.drain_background_tasks(timeout_seconds=1)

    assert task.done()


async def test_metric_middleware_drain_background_tasks_cancels_on_timeout():
    """MetricMiddleware cancels pending tasks when drain timeout is hit."""
    mock_app = AsyncMock()
    middleware = MetricMiddleware(mock_app)

    blocking_task = asyncio.create_task(asyncio.sleep(60))
    middleware._background_tasks.add(blocking_task)
    blocking_task.add_done_callback(middleware._background_tasks.discard)

    with patch("app.middleware.logger") as mock_logger:
        await middleware.drain_background_tasks(timeout_seconds=0.001)

    assert blocking_task.cancelled()
    mock_logger.warning.assert_called_once()
