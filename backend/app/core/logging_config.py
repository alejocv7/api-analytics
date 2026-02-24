import logging
import sys

from asgi_correlation_id import CorrelationIdFilter
from colorlog import ColoredFormatter
from pythonjsonlogger import json as jsonlogger

from app.core.config import settings


def setup_logging() -> None:
    """
    Configure structured JSON logging for the application.
    """
    log_level = settings.LOG_LEVEL

    # Correlation ID filter for asgi-correlation-id
    cid_filter = CorrelationIdFilter(uuid_length=32, default_value="-")

    formatter: logging.Formatter
    if settings.ENVIRONMENT == "local":
        formatter = ColoredFormatter(
            "%(log_color)s%(asctime)s - %(levelname)s - %(name)s - %(message)s"
            " - [%(correlation_id)s]%(reset)s",
            log_colors={
                "DEBUG": "white",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "red,bg_white",
            },
        )
    else:
        formatter = jsonlogger.JsonFormatter(
            "%(asctime)s %(levelname)s %(name)s %(message)s %(correlation_id)s"
        )

    handler = logging.StreamHandler(sys.stdout)
    handler.addFilter(cid_filter)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()

    # Remove existing handlers to avoid duplicate logs (especially in uvicorn)
    for h in root_logger.handlers[:]:
        h.close()
        root_logger.removeHandler(h)

    root_logger.addHandler(handler)
    root_logger.setLevel(log_level)

    # Optionally suppress noisy logs from libraries
    for name in ("uvicorn.access", "uvicorn.error"):
        uv_logger = logging.getLogger(name)
        uv_logger.handlers.clear()
        uv_logger.addHandler(handler)
        uv_logger.propagate = False

    logging.info("Logging configured")
