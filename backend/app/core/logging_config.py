import logging
import sys

from pythonjsonlogger import jsonlogger

from app.core.config import settings


def setup_logging():
    """
    Configure structured JSON logging for the application.
    """
    log_level = logging.INFO
    if settings.ENVIRONMENT == "local":
        log_level = logging.DEBUG

    # Formatter configuration
    class CustomJsonFormatter(jsonlogger.JsonFormatter):
        def add_fields(self, log_record, record, message_dict):
            super().add_fields(log_record, record, message_dict)
            from app.middleware import request_id_ctx

            log_record["request_id"] = request_id_ctx.get()

    handler = logging.StreamHandler(sys.stdout)
    formatter = CustomJsonFormatter("%(asctime)s %(levelname)s %(name)s %(message)s")
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
