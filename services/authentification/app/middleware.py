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
        response = await call_next(request)
        return response
    except IntegrityError as e:
        logger.error(f"Integrity error (e.g., duplicate email): {str(e)}", extra={"request_path": request.url.path, "method": request.method})
        return JSONResponse(status_code=409, content={"detail": "Duplicate entry"})
    except SQLAlchemyError as e:
        logger.error(f"Database error: {str(e)}", extra={"request_path": request.url.path, "method": request.method})
        return JSONResponse(status_code=500, content={"detail": "Database error"})
    except PyJWTError as e:
        logger.warning(f"JWT error: {str(e)}", extra={"request_path": request.url.path, "method": request.method})
        return JSONResponse(status_code=401, content={"detail": "Invalid token"})
    except KafkaError as e:
        logger.warning(f"Kafka send failed: {str(e)}", extra={"request_path": request.url.path, "method": request.method})
        return JSONResponse(status_code=500, content={"detail": "Kafka communication error"})
    except HTTPException as e:
        logger.info(f"HTTP exception: {e.detail}", extra={"status_code": e.status_code, "request_path": request.url.path})
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", extra={"request_path": request.url.path, "method": request.method})
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
    handler = StreamHandler()
    handler.setFormatter(JsonFormatter(datefmt="%Y-%m-%dT%H:%M:%S%z"))
    logging.root.addHandler(handler)
    logging.root.setLevel(settings.log_level)