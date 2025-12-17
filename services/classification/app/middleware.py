import logging
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from aiokafka.errors import KafkaError

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