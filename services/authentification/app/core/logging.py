import logging
import json
from logging import Formatter
from typing import Any
from app.core.config import settings

SENSITIVE_KEYS = {'password', 'token', 'access_token', 'refresh_token', 'new_password'}

class JsonFormatter(Formatter):
    """Средство форматирования JSON для журналов с маскированием данных."""
    
    def _filter_sensitive_data(self, data: Any) -> Any:
        """Рекурсивно маскирует чувствительные данные."""
        if isinstance(data, dict):
            return {
                k: "***" if k in SENSITIVE_KEYS else self._filter_sensitive_data(v)
                for k, v in data.items()
            }
        if isinstance(data, list):
            return [self._filter_sensitive_data(v) for v in data]
        return data

    def format(self, record):
        log_data = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }
        
        if hasattr(record, 'extra'):
            log_data.update(self._filter_sensitive_data(record.extra))

        if record.exc_info:
            log_data['exc_info'] = self.formatException(record.exc_info)

        return json.dumps(log_data, default=str, ensure_ascii=False)

def setup_logging():
    """Настраивает ведение журнала с помощью JSON formatter."""
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
