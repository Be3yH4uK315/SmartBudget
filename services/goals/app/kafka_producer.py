from decimal import Decimal
from datetime import date, datetime
import json
import logging
from aiokafka import AIOKafkaProducer
from jsonschema import validate
from jsonschema.exceptions import ValidationError

from app import settings, schemas

logger = logging.getLogger(__name__)

def json_default(obj):
    """Расширенная сериализация: обрабатывает Decimal и даты."""
    if isinstance(obj, Decimal):
        return str(obj)
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    raise TypeError

class KafkaProducer:
    """Обертка для AIOKafkaProducer с валидацией по JSON Schema."""
    def __init__(self):
        self.producer = AIOKafkaProducer(
            bootstrap_servers=settings.settings.kafka.kafka_bootstrap_servers
        )
        self._schemas = {
            settings.settings.kafka.kafka_topic_budget_events: schemas.BUDGET_EVENTS_SCHEMA,
            settings.settings.kafka.kafka_topic_budget_notification: schemas.BUDGET_NOTIFICATIONS_SCHEMA,
        }

    async def start(self):
        await self.producer.start()
        logger.info("KafkaProducer started.")

    async def stop(self):
        await self.producer.stop()
        logger.info("KafkaProducer stopped.")

    async def send_event(self, topic: str, event_data: dict, schema: dict = None):
        """Валидирует и отправляет событие."""
        try:
            dumped_str = json.dumps(event_data, default=json_default)

            if schema:
                validate_data = json.loads(dumped_str)
                validate(instance=validate_data, schema=schema)

            value_bytes = dumped_str.encode('utf-8')

            await self.producer.send_and_wait(topic, value=value_bytes)
            logger.info(f"Sent event to {topic}: {event_data.get('event', 'unknown')}")
            
        except ValidationError as e:
            logger.error(f"Invalid event data for {topic}: {e}")
        except Exception as e:
            logger.error(f"Failed to send Kafka event to {topic}: {e}")
            raise

    async def send_budget_event(self, event_data: dict):
        topic = settings.settings.kafka.kafka_topic_budget_events
        await self.send_event(topic, event_data, self._schemas[topic])

    async def send_notification(self, event_data: dict):
        topic = settings.settings.kafka.kafka_topic_budget_notification
        await self.send_event(topic, event_data, self._schemas[topic])