from datetime import datetime
import json
import logging
from uuid import UUID
from aiokafka import AIOKafkaProducer
from pydantic import BaseModel

logger = logging.getLogger(__name__)

async def sendKafkaEvent(
    kafkaProducer: AIOKafkaProducer,
    topic: str,
    eventData: dict | BaseModel
):
    """
    Валидирует и отправляет событие в Kafka.
    """
    try:
        if isinstance(eventData, BaseModel):
            valueBytes = eventData.model_dump_json().encode('utf-8')
        else:
            def defaultJsonSerializer(obj):
                if isinstance(obj, datetime):
                    return obj.isoformat()
                if isinstance(obj, UUID):
                    return str(obj)
                if isinstance(obj, (set, tuple)):
                    return list(obj)
                if isinstance(obj, bytes):
                    return obj.decode('utf-8')
                raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")

            valueBytes = json.dumps(
                eventData, 
                default=defaultJsonSerializer
            ).encode('utf-8')

        await kafkaProducer.send_and_wait(topic, value=valueBytes)
        logger.debug(f"Kafka event sent to {topic}")
    except Exception as e:
        logger.error(f"Failed to send Kafka event to {topic}: {e}")
        raise