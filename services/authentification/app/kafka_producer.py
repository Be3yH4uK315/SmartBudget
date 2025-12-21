import logging
from aiokafka import AIOKafkaProducer

from app import settings, utils

logger = logging.getLogger(__name__)

class KafkaProducer:
    """Kafka producer. Отвечает только за отправку байтов."""
    
    def __init__(self):
        self.producer = AIOKafkaProducer(
            bootstrap_servers=settings.settings.KAFKA.KAFKA_BOOTSTRAP_SERVERS,
            acks='all',
            retries=3
        )
        self._is_running = False

    async def start(self) -> None:
        await self.producer.start()
        self._is_running = True

    async def stop(self) -> None:
        if self._is_running:
            await self.producer.stop()
            self._is_running = False

    async def send_event(self, topic: str, event_data: dict) -> bool:
        """
        Отправляет событие.
        """
        if not self._is_running:
            logger.error("KafkaProducer is not running")
            return False

        try:
            payload = utils.to_json_str(event_data)
            key = event_data.get("user_id") or event_data.get("email")
            key_bytes = str(key).encode() if key else None

            await self.producer.send_and_wait(
                topic=topic,
                key=key_bytes,
                value=payload.encode()
            )
            return True

        except Exception as e:
            logger.error(f"Kafka send error to topic {topic}: {e}")
            return False