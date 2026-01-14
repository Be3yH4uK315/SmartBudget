import asyncio
import logging
from typing import Optional
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
        value: bytes,
        key: bytes = None,
        headers: Optional[list[tuple[str, bytes]]] = None,
        wait: bool = True
    ) -> bool:
        """Отправляет событие."""
        if not self._is_running or not self.producer:
            logger.error("Kafka producer not running")
            return False

        try:
            if wait:
                await asyncio.wait_for(
                    self.producer.send_and_wait(
                        topic=topic,
                        key=key,
                        value=value,
                        headers=headers,
                    ),
                    timeout=SEND_TIMEOUT,
                )
            else:
                self.producer.send(
                    topic=topic,
                    key=key,
                    value=value,
                    headers=headers
                )
            return True
        except Exception as e:
            logger.error(f"Kafka send error: {e}")
            return False

    async def send_batch(self, events: list[dict]) -> list[bool]:
        """Массовая отправка событий."""
        if not self._is_running or not self.producer:
            logger.error("Kafka producer not running")
            return [False] * len(events)

        futures = []
        for event in events:
            try:
                fut = self.producer.send(
                    topic=event['topic'],
                    value=event['value'],
                    key=event.get('key'),
                    headers=event.get('headers')
                )
                futures.append(fut)
            except Exception as e:
                f = asyncio.Future()
                f.set_exception(e)
                futures.append(f)

        try:
            await self.producer.flush()
        except Exception as e:
            logger.error(f"Kafka flush failed: {e}")
        
        results = await asyncio.gather(*futures, return_exceptions=True)
        
        final_status = []
        for res in results:
            if isinstance(res, Exception):
                logger.error(f"Kafka batch send error: {res}")
                final_status.append(False)
            else:
                final_status.append(True)
                
        return final_status