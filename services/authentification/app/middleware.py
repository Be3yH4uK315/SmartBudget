import logging
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from jwt.exceptions import PyJWTError
from aiokafka.errors import KafkaError
from logging import getLogger, Formatter, StreamHandler
import json
from .settings import settings

logger = getLogger(__name__)

async def error_middleware(request: Request, call_next):
    try:
        return await call_next(request)
    except IntegrityError as e:
        logger.error(
            f"Integrity error: {e}",
            extra={"path": request.url.path, "method": request.method}
        )
        return JSONResponse(status_code=409, content={"detail": "Duplicate entry"})
    except SQLAlchemyError as e:
        logger.error(
            f"Database error: {e}",
            extra={"path": request.url.path, "method": request.method}
        )
        return JSONResponse(status_code=500, content={"detail": "Database error"})
    except PyJWTError as e:
        logger.warning(
            f"JWT error: {e}",
            extra={"path": request.url.path, "method": request.method}
        )
        return JSONResponse(status_code=401, content={"detail": "Invalid token"})
    except KafkaError as e:
        logger.warning(
            f"Kafka error: {e}",
            extra={"path": request.url.path, "method": request.method}
        )
        return JSONResponse(status_code=500, content={"detail": "Kafka error"})
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

class JsonFormatter(Formatter):
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
    root_logger = logging.getLogger()
    if root_logger.hasHandlers():
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
    handler = StreamHandler()
    handler.setFormatter(JsonFormatter(datefmt="%Y-%m-%dT%H:%M:%S%z"))
    root_logger.addHandler(handler)
    root_logger.setLevel(settings.log_level)