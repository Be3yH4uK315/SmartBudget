from decimal import Decimal
from datetime import date, datetime
import json
import logging
import asyncio
from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaError, KafkaTimeoutError
from jsonschema import validate
from jsonschema.exceptions import ValidationError

from app import settings, schemas

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_DELAY = 1

def json_default(obj):
    """Расширенная сериализация."""
    if isinstance(obj, Decimal):
        return str(obj)
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

class KafkaProducer:
    """Kafka producer с валидацией и повторными попытками."""
    
    def __init__(self):
        self.producer = AIOKafkaProducer(
            bootstrap_servers=settings.settings.KAFKA.KAFKA_BOOTSTRAP_SERVERS,
            acks='all',
            retries=3,
            request_timeout_ms=10000
        )
        self._schemas = {
            settings.settings.KAFKA.KAFKA_TOPIC_BUDGET_EVENTS: schemas.BUDGET_EVENTS_SCHEMA,
            settings.settings.KAFKA.KAFKA_TOPIC_BUDGET_NOTIFICATION: schemas.BUDGET_NOTIFICATIONS_SCHEMA,
        }
        self._is_running = False

    async def start(self) -> None:
        """Запуск producer."""
        try:
            await self.producer.start()
            self._is_running = True
            logger.info("KafkaProducer started successfully")
        except KafkaError as e:
            logger.error(f"Failed to start KafkaProducer: {e}")
            raise

    async def stop(self) -> None:
        """Остановка producer."""
        if self._is_running:
            try:
                await self.producer.stop()
                self._is_running = False
                logger.info("KafkaProducer stopped")
            except Exception as e:
                logger.error(f"Error stopping KafkaProducer: {e}")

    async def send_event(
        self, 
        topic: str, 
        event_data: dict, 
        schema: dict = None
    ) -> bool:
        """Отправляет событие с повторными попытками."""
        if not self._is_running:
            logger.warning("Producer is not running, cannot send event")
            return False

        try:
            dumped = json.dumps(event_data, default=json_default)

            if schema:
                try:
                    validate_data = json.loads(dumped)
                    validate(instance=validate_data, schema=schema)
                except ValidationError as e:
                    logger.error(f"Event validation failed for {topic}: {e.message}")
                    return False

            value_bytes = dumped.encode('utf-8')

            for attempt in range(MAX_RETRIES):
                try:
                    await self.producer.send_and_wait(topic, value=value_bytes)
                    logger.info(f"Event sent to {topic}: {event_data.get('event', 'unknown')}")
                    return True
                except KafkaTimeoutError as e:
                    if attempt < MAX_RETRIES - 1:
                        wait_time = RETRY_DELAY * (2 ** attempt)
                        logger.warning(
                            f"Kafka timeout (attempt {attempt + 1}/{MAX_RETRIES}), "
                            f"retrying in {wait_time}s: {e}"
                        )
                        await asyncio.sleep(wait_time)
                    else:
                        logger.error(f"Failed to send event after {MAX_RETRIES} attempts: {e}")
                        return False
                except KafkaError as e:
                    logger.error(f"Kafka error sending event: {e}")
                    return False
            
        except Exception as e:
            logger.error(f"Unexpected error in send_event: {e}")
            return False

    async def send_budget_event(self, event_data: dict) -> bool:
        """Отправляет событие в топик бюджета."""
        topic = settings.settings.KAFKA.KAFKA_TOPIC_BUDGET_EVENTS
        return await self.send_event(topic, event_data, self._schemas.get(topic))

    async def send_notification(self, event_data: dict) -> bool:
        """Отправляет уведомление."""
        topic = settings.settings.KAFKA.KAFKA_TOPIC_BUDGET_NOTIFICATION
        return await self.send_event(topic, event_data, self._schemas.get(topic))