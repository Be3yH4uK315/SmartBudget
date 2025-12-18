from decimal import Decimal
from datetime import date, datetime
import json
import logging
from aiokafka import AIOKafkaProducer
from jsonschema import validate
from jsonschema.exceptions import ValidationError

from app import settings, schemas

logger = logging.getLogger(__name__)

def jsonDefault(obj):
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
            bootstrap_servers=settings.settings.KAFKA.KAFKA_BOOTSTRAP_SERVERS
        )
        self._schemas = {
            settings.settings.KAFKA.KAFKA_TOPIC_BUDGET_EVENTS: schemas.BUDGET_EVENTS_SCHEMA,
            settings.settings.KAFKA.KAFKA_TOPIC_BUDGET_NOTIFICATION: schemas.BUDGET_NOTIFICATIONS_SCHEMA,
        }

    async def start(self):
        await self.producer.start()
        logger.info("KafkaProducer started.")

    async def stop(self):
        await self.producer.stop()
        logger.info("KafkaProducer stopped.")

    async def sendEvent(self, topic: str, eventData: dict, schema: dict = None):
        """Валидирует и отправляет событие."""
        try:
            dumped = json.dumps(eventData, default=jsonDefault)

            if schema:
                validateData = json.loads(dumped)
                validate(instance=validateData, schema=schema)

            valueBytes = dumped.encode('utf-8')

            await self.producer.send_and_wait(topic, value=valueBytes)
            logger.info(f"Sent event to {topic}: {eventData.get('event', 'unknown')}")
            
        except ValidationError as e:
            logger.error(f"Invalid event data for {topic}: {e}")
        except Exception as e:
            logger.error(f"Failed to send Kafka event to {topic}: {e}")
            raise

    async def sendBudgetEvent(self, eventData: dict):
        topic = settings.settings.KAFKA.KAFKA_TOPIC_BUDGET_EVENTS
        await self.sendEvent(topic, eventData, self._schemas[topic])

    async def sendNotification(self, eventData: dict):
        topic = settings.settings.KAFKA.KAFKA_TOPIC_BUDGET_NOTIFICATION
        await self.sendEvent(topic, eventData, self._schemas[topic])