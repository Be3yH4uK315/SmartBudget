import logging
import json
from logging import Formatter

from app import settings

class JsonFormatter(Formatter):
    """Средство форматирования JSON для журналов."""
    def format(self, record):
        logData = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }
        
        if hasattr(record, 'extra'):
             logData.update(record.extra)
             
        if record.exc_info:
            logData['exc_info'] = self.formatException(record.exc_info)

        return json.dumps(logData, default=str, ensure_ascii=False)

def setupLogging():
    """Настраивает ведение журнала с помощью JSON formatter."""
    rootLogger = logging.getLogger()
    
    if rootLogger.hasHandlers():
        for handler in rootLogger.handlers[:]:
            rootLogger.removeHandler(handler)
            
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter(datefmt="%Y-%m-%dT%H:%M:%S%z"))
    rootLogger.addHandler(handler)
    rootLogger.setLevel(settings.settings.APP.LOG_LEVEL)

    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("aiokafka").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("aiocache").setLevel(logging.WARNING)