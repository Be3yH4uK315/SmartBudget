import asyncio
import logging
from typing import Any

from aiokafka import AIOKafkaProducer

from app.core.config import settings

logger = logging.getLogger(__name__)
SEND_TIMEOUT = 10


class KafkaProducerWrapper:
    """Kafka producer с поддержкой батчинга."""

    def __init__(self):
        self.producer = AIOKafkaProducer(
            bootstrap_servers=settings.KAFKA.KAFKA_BOOTSTRAP_SERVERS,
            acks="all",
            linger_ms=50,
            request_timeout_ms=SEND_TIMEOUT * 1000,
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

    async def send_event(
        self,
        topic: str,
        value: bytes,
        key: bytes | None = None,
        headers: list[tuple[str, bytes]] | None = None,
        wait: bool = True,
    ) -> bool:
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
                await self.producer.send(
                    topic=topic,
                    key=key,
                    value=value,
                    headers=headers,
                )
            return True
        except Exception as exc:
            logger.error("Kafka send error to %s: %s", topic, exc, exc_info=True)
            return False

    async def send_batch(self, events: list[dict[str, Any]]) -> list[bool]:
        if not self._is_running or not self.producer:
            logger.error("Kafka producer not running")
            return [False] * len(events)

        futures: list[asyncio.Task] = []
        for event in events:
            try:
                future = asyncio.create_task(
                    self.producer.send_and_wait(
                        topic=event["topic"],
                        value=event["value"],
                        key=event.get("key"),
                        headers=event.get("headers"),
                    )
                )
                futures.append(future)
            except Exception as exc:
                future = asyncio.get_running_loop().create_future()
                future.set_exception(exc)
                futures.append(future)

        try:
            results = await asyncio.wait_for(
                asyncio.gather(*futures, return_exceptions=True),
                timeout=SEND_TIMEOUT,
            )
        except Exception as exc:
            logger.error("Kafka batch send failed: %s", exc, exc_info=True)
            return [False] * len(events)

        statuses: list[bool] = []
        for result in results:
            if isinstance(result, Exception):
                logger.error("Kafka batch send error: %s", result, exc_info=True)
                statuses.append(False)
            else:
                statuses.append(True)
        return statuses
