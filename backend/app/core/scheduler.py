import asyncio
import logging

from app.core import db
from app.core.config import settings
from app.services import metric_service

logger = logging.getLogger(__name__)


class MetricCleanupScheduler:
    """Lifecycle manager for the periodic metric cleanup task."""

    def __init__(self) -> None:
        self._task: asyncio.Task[None] | None = None

    async def run_cleanup_loop(self) -> None:
        """Delete old metrics based on configured interval and retention.

        On failure, it will retry after the configured interval.
        """
        while True:
            try:
                async with db.AsyncSessionLocal() as session:
                    deleted = await metric_service.cleanup_old_metrics(
                        session, settings.METRIC_RETENTION_DAYS
                    )
                    logger.info("Cleaned up %d old metrics", deleted)
            except Exception:
                logger.exception("Metric cleanup failed")
            await asyncio.sleep(settings.METRIC_CLEANUP_INTERVAL_HOURS * 3600)

    def start(self) -> None:
        """Start the periodic cleanup loop if not already running."""
        if self._task and not self._task.done():
            return
        self._task = asyncio.create_task(
            self.run_cleanup_loop(), name="metric_cleanup_scheduler"
        )

    async def stop(self, timeout_seconds: float) -> None:
        """Cancel the cleanup loop and wait up to timeout_seconds for shutdown."""
        if self._task is None:
            return

        task = self._task
        task.cancel()
        done, _ = await asyncio.wait({task}, timeout=timeout_seconds)
        if task in done:
            self._task = None
            logger.info("Cleanup scheduler stopped")
        else:
            logger.warning(
                "Timed out waiting for cleanup scheduler to stop after %.1fs",
                timeout_seconds,
            )
