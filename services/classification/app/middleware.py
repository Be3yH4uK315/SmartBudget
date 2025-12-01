import logging
import json
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from aiokafka.errors import KafkaError

from app import settings

logger = logging.getLogger(__name__)

async def error_middleware(request: Request, call_next):
    """Промежуточное ПО для обработки ошибок в запросах."""
    try:
        return await call_next(request)
    except SQLAlchemyError as e:
        logger.error(
            f"Database error: {e}",
            extra={"path": request.url.path, "method": request.method}
        )
        return JSONResponse(status_code=500, content={"detail": "Database error"})
    except KafkaError as e:
        logger.error(
            f"Kafka error: {e}",
            extra={"path": request.url.path, "method": request.method}
        )
        return JSONResponse(status_code=503, content={"detail": "Kafka service unavailable"})
    except HTTPException as e:
        logger.info(
            f"HTTP exception {e.status_code}: {e.detail}",
            extra={"path": request.url.path, "method": request.method}
        )
        raise
    except Exception as e:
        logger.error(
            f"Unexpected error: {e}",
            extra={"path": request.url.path, "method": request.method}
        )
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})

class JsonFormatter(logging.Formatter):
    """Средство форматирования JSON для журналов."""
    def format(self, record):
        log_data = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.msg,
            "logger": record.name,
            "extra": record.__dict__.get("extra", {}),
        }
        return json.dumps(log_data)

def setup_logging():
    """Настраивает ведение журнала с помощью JSON formatter."""
    root_logger = logging.getLogger()
    if root_logger.hasHandlers():
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter(datefmt="%Y-%m-%dT%H:%M:%S%z"))
    root_logger.addHandler(handler)
    root_logger.setLevel(settings.settings.log_level)