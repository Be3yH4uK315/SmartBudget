from aiokafka import AIOKafkaProducer
from .settings import settings
import json
import jsonschema
from jsonschema import validate
from logging import getLogger

logger = getLogger(__name__)

producer = None

async def startup_kafka():
    global producer
    producer = AIOKafkaProducer(bootstrap_servers=settings.kafka_bootstrap_servers)
    await producer.start()

async def shutdown_kafka():
    if producer:
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
        "role_id": {"type": "string", "format": "uuid"},
        "is_active": {"type": "boolean"}
    },
    "required": ["user_id", "email"]
}

async def send_event(topic: str, event_data: dict, schema: dict):
    try:
        validate(instance=event_data, schema=schema)
        await producer.send_and_wait(topic, value=json.dumps(event_data).encode('utf-8'))
        logger.info(f"Event sent to {topic}: {event_data}")
    except jsonschema.exceptions.ValidationError as e:
        logger.error(f"Invalid event data for {topic}: {e}")
        raise ValueError(f"Invalid event data: {e}")
    except Exception as e:
        logger.error(f"Kafka send failed: {e}")
        raise