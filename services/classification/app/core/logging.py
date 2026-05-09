import json
import logging
from logging import Formatter, LogRecord

from app.core.config import settings


class JsonFormatter(Formatter):
    """JSON formatter для логов приложения."""

    def format(self, record: LogRecord) -> str:
        """Формирует JSON-представление log record."""
        log_data = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }

        extra = getattr(record, "extra", None)
        if isinstance(extra, dict):
            log_data.update(extra)

        if record.exc_info:
            log_data["exc_info"] = self.formatException(record.exc_info)

        return json.dumps(
            log_data,
            default=str,
            ensure_ascii=False,
        )


def setup_logging() -> None:
    """Настраивает JSON-логирование приложения."""
    root_logger = logging.getLogger()

    if root_logger.hasHandlers():
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter(datefmt="%Y-%m-%dT%H:%M:%S%z"))

    root_logger.addHandler(handler)
    root_logger.setLevel(settings.APP.LOG_LEVEL)

    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("aiokafka").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("aiocache").setLevel(logging.WARNING)
