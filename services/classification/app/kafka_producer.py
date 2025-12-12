from datetime import datetime
import json
import logging
from uuid import UUID
from aiokafka import AIOKafkaProducer
from pydantic import BaseModel

logger = logging.getLogger(__name__)

async def send_kafka_event(
    producer: AIOKafkaProducer,
    topic: str,
    event_data: dict | BaseModel
):
    """
    Валидирует и отправляет событие в Kafka.
    """
    try:
        if isinstance(event_data, BaseModel):
            value_bytes = event_data.model_dump_json().encode('utf-8')
        else:
            def default_json_serializer(obj):
                if isinstance(obj, datetime):
                    return obj.isoformat()
                if isinstance(obj, UUID):
                    return str(obj)
                if isinstance(obj, (set, tuple)):
                    return list(obj)
                if isinstance(obj, bytes):
                    return obj.decode('utf-8')
                raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")

            value_bytes = json.dumps(
                event_data, 
                default=default_json_serializer
            ).encode('utf-8')

        await producer.send_and_wait(topic, value=value_bytes)
        logger.debug(f"Kafka event sent to {topic}")
    except Exception as e:
        logger.error(f"Failed to send Kafka event to {topic}: {e}")
        raise