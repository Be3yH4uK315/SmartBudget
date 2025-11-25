from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from jwt.exceptions import PyJWTError
from aiokafka.errors import KafkaError
from logging import getLogger

logger = getLogger(__name__)

async def error_middleware(request: Request, call_next):
    """Промежуточное программное обеспечение для обработки ошибок в запросах."""
    try:
        return await call_next(request)
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
            extra={"path": request.url.path, "method": request.method, "error_type": type(e).__name__}
        )
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})