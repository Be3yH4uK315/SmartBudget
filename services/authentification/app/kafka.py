from typing import Optional
from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaConnectionError
import json
import jsonschema
from jsonschema import validate
from logging import getLogger
import asyncio
from .settings import settings

logger = getLogger(__name__)

producer: Optional[AIOKafkaProducer] = None

async def startup_kafka():
    global producer
    producer = AIOKafkaProducer(bootstrap_servers=settings.kafka_bootstrap_servers)
    await producer.start()

async def shutdown_kafka():
    if producer is not None:
        await producer.stop()

AUTH_EVENTS_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "Auth Events Schema",
    "type": "object",
    "properties": {
        "event": {"type": "string", "enum": ["user.registered", "user.login", "user.logout", "user.password_changed", "user.password_reset", "user.token_invalid"]},
        "user_id": {"type": "string", "format": "uuid"},
        "email": {"type": "string"},
        "ip": {"type": "string"},
        "location": {"type": "string"}
    },
    "required": ["event", "user_id"]
}

USERS_ACTIVE_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "user_id": {"type": "string", "format": "uuid"},
        "email": {"type": "string"},
        "name": {"type": "string"},
        "country": {"type": "string"},
        "role": {"type": "integer"},
        "is_active": {"type": "boolean"}
    },
    "required": ["user_id", "email"]
}

async def send_event(topic: str, event_data: dict, schema: dict):
    if producer is None:
        raise RuntimeError("Kafka producer not initialized")
    retries = 3
    for attempt in range(retries):
        try:
            validate(instance=event_data, schema=schema)
            await producer.send_and_wait(topic, value=json.dumps(event_data).encode('utf-8'))
            logger.info(f"Event sent to {topic}: {event_data}")
            return
        except jsonschema.exceptions.ValidationError as e:
            logger.error(f"Invalid event data for {topic}: {e}")
            raise ValueError(f"Invalid event data: {e}")
        except KafkaConnectionError as e:
            logger.warning(f"Kafka connection failed on attempt {attempt+1}: {e}")
            await asyncio.sleep(0.5 * (2 ** attempt))
        except Exception as e:
            logger.error(f"Kafka send failed: {e}")
            raise
    raise RuntimeError("Kafka send failed after retries")