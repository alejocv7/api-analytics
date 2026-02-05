import logging
import sys

from colorlog import ColoredFormatter
from pythonjsonlogger import json as jsonlogger

from app.core.config import settings


def setup_logging():
    """
    Configure structured JSON logging for the application.
    """
    log_level = settings.LOG_LEVEL

    formatter = None
    if settings.ENVIRONMENT == "local":
        formatter = CustomFormatter(
            "%(log_color)s%(asctime)s - %(levelname)s - %(name)s - %(message)s - [request_id=%(request_id)s]%(reset)s"
        )
    else:
        formatter = CustomJsonFormatter(
            "%(asctime)s %(levelname)s %(name)s %(message)s"
        )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    # Configure root logger
    root_logger = logging.getLogger()

    # Remove existing handlers to avoid duplicate logs (especially in uvicorn)
    for h in root_logger.handlers[:]:
        root_logger.removeHandler(h)

    root_logger.addHandler(handler)
    root_logger.setLevel(log_level)

    # Optionally suppress noisy logs from libraries
    logging.getLogger("uvicorn.access").handlers = [handler]
    logging.getLogger("uvicorn.error").handlers = [handler]

    # Example structured log on startup
    logging.info(
        "Logging configured",
        extra={
            "environment": settings.ENVIRONMENT,
            "log_level": logging.getLevelName(log_level),
        },
    )


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        from app.middleware import request_id_ctx

        log_record["request_id"] = request_id_ctx.get()


class CustomFormatter(ColoredFormatter):
    LOG_COLORS = {
        "DEBUG": "white",
        "INFO": "green",
        "WARNING": "yellow",
        "ERROR": "red",
        "CRITICAL": "red,bg_white",
    }

    RESET = "\033[0m"

    def __init__(self, fmt=None, datefmt=None):
        # Use the class-level color table when initializing the parent
        super().__init__(fmt=fmt, log_colors=self.LOG_COLORS, datefmt=datefmt)

    def format(self, record):
        from app.middleware import request_id_ctx

        record.request_id = request_id_ctx.get()

        return super().format(record)
