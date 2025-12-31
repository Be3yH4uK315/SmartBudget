import logging
from aiokafka import AIOKafkaProducer
from app.core.config import settings

logger = logging.getLogger(__name__)

class KafkaProducerWrapper:
    def __init__(self):
        self.producer = AIOKafkaProducer(
            bootstrap_servers=settings.KAFKA.KAFKA_BOOTSTRAP_SERVERS
        )

    async def start(self):
        await self.producer.start()

    async def stop(self):
        await self.producer.stop()

    async def send_raw(self, topic: str, value: bytes, key: bytes = None) -> bool:
        """Отправка сырых байтов."""
        try:
            await self.producer.send_and_wait(topic, value=value, key=key)
            return True
        except Exception as e:
            logger.error(f"Kafka send error: {e}")
            return False