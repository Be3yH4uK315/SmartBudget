from datetime import datetime
import json
import logging
from uuid import UUID
from typing import Any
from aiokafka import AIOKafkaProducer
from pydantic import BaseModel

logger = logging.getLogger(__name__)

def _default_json_serializer(obj: Any):
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, UUID):
        return str(obj)
    if isinstance(obj, (set, tuple)):
        return list(obj)
    if isinstance(obj, bytes):
        return obj.decode('utf-8')
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")

async def send_kafka_event(
    producer: AIOKafkaProducer,
    topic: str,
    event_data: dict | BaseModel
) -> None:
    """
    Валидирует и отправляет событие в Kafka.
    """
    try:
        if isinstance(event_data, BaseModel):
            value_bytes = event_data.model_dump_json().encode('utf-8')
        else:
            value_bytes = json.dumps(event_data, default=_default_json_serializer).encode('utf-8')

        await producer.send_and_wait(topic, value=value_bytes)
        logger.debug("Kafka event sent to %s", topic)
    except Exception as exc:
        logger.error("Failed to send Kafka event to %s: %s", topic, exc)
        raise