import asyncio
import logging
from aiokafka import AIOKafkaProducer
from app.core.config import settings

logger = logging.getLogger(__name__)

SEND_TIMEOUT = 10

class KafkaProducerWrapper:
    """Kafka producer с валидацией и повторными попытками."""
    
    def __init__(self):
        self.producer = AIOKafkaProducer(
            bootstrap_servers=settings.KAFKA.KAFKA_BOOTSTRAP_SERVERS,
            acks='all',
            linger_ms=50,
            request_timeout_ms=SEND_TIMEOUT * 1000
        )
        self._is_running = False

    async def start(self) -> None:
        await self.producer.start()
        self._is_running = True
        logger.info("Kafka producer started")

    async def stop(self) -> None:
        if self._is_running and self.producer:
            await self.producer.stop()
            self._is_running = False
            logger.info("Kafka producer stopped")

    async def send_batch(self, events: list[dict]) -> list[bool]:
        """Массовая отправка событий."""
        if not self._is_running:
            return [False] * len(events)

        futures = []
        for event in events:
            try:
                fut = self.producer.send(
                    topic=event['topic'],
                    value=event['value'],
                    key=event.get('key')
                )
                futures.append(fut)
            except Exception as e:
                f = asyncio.Future()
                f.set_exception(e)
                futures.append(f)

        results = await asyncio.gather(*futures, return_exceptions=True)
        
        final_status = []
        for res in results:
            if isinstance(res, Exception):
                logger.error(f"Kafka batch send error: {res}")
                final_status.append(False)
            else:
                final_status.append(True)
                
        return final_status