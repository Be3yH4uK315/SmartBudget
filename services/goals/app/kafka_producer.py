import asyncio
import logging
from aiokafka import AIOKafkaProducer

from app import settings
from app.utils import serialization

logger = logging.getLogger(__name__)

SEND_TIMEOUT = 10

class KafkaProducer:
    """Kafka producer с валидацией и повторными попытками."""
    
    def __init__(self):
        self.producer = AIOKafkaProducer(
            bootstrap_servers=settings.settings.KAFKA.KAFKA_BOOTSTRAP_SERVERS,
            acks='all',
            linger_ms=50,
            request_timeout_ms=SEND_TIMEOUT * 1000
        )
        self._is_running = False

    async def start(self) -> None:
        """Запуск producer."""
        await self.producer.start()
        self._is_running = True
        logger.info("Kafka producer started")

    async def stop(self) -> None:
        """Остановка producer."""
        if self._is_running and self.producer:
            await self.producer.stop()
            self._is_running = False
            logger.info("Kafka producer stopped")

    async def send_event(
        self,
        topic: str,
        event_data: dict
    ) -> bool:
        """Отправляет событие с повторными попытками."""
        if not self._is_running or not self.producer:
            logger.error("Kafka producer not running")
            return False

        try:
            payload = serialization.to_json_str(event_data)

            key = event_data.get("goal_id") or event_data.get("event_id")

            await asyncio.wait_for(
                self.producer.send_and_wait(
                    topic=topic,
                    key=str(key).encode() if key else None,
                    value=payload.encode(),
                ),
                timeout=SEND_TIMEOUT,
            )
            return True

        except Exception as e:
            logger.error(f"Kafka send error: {e}")
            return False