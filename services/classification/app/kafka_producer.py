from datetime import datetime
import json
import logging
from uuid import UUID
from aiokafka import AIOKafkaProducer
from jsonschema import validate
from jsonschema.exceptions import ValidationError

from app import kafka

logger = logging.getLogger(__name__)

async def send_kafka_event(
    producer: AIOKafkaProducer,
    topic: str,
    event_data: dict
):
    """
    Валидирует и отправляет событие в Kafka.
    """
    schema = kafka.SCHEMAS_MAP.get(topic)
    if not schema:
        logger.error(f"No Kafka schema found for topic: {topic}")
    else:
        try:
            validate(instance=event_data, schema=schema)
        except ValidationError as e:
            logger.error(f"Invalid Kafka event data for topic {topic}: {e}")
            return

    try:
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