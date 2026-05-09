import asyncio
import logging
from typing import Any

from aiokafka import AIOKafkaProducer

from app.core.config import settings

logger = logging.getLogger(__name__)

SEND_TIMEOUT_SECONDS = 10


class KafkaProducerWrapper:
    """Kafka producer с поддержкой одиночной и пакетной отправки."""

    def __init__(self) -> None:
        self.producer = AIOKafkaProducer(
            bootstrap_servers=settings.KAFKA.KAFKA_BOOTSTRAP_SERVERS,
            acks="all",
            linger_ms=50,
            request_timeout_ms=SEND_TIMEOUT_SECONDS * 1000,
        )
        self._is_running = False

    async def start(self) -> None:
        """Запускает Kafka producer."""
        await self.producer.start()
        self._is_running = True
        logger.info("Kafka producer started")

    async def stop(self) -> None:
        """Останавливает Kafka producer."""
        if not self._is_available:
            return

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
        """Отправляет одно событие в Kafka."""
        if not self._is_available:
            logger.error("Kafka producer is not running")
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
                    timeout=SEND_TIMEOUT_SECONDS,
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
            logger.error(
                "Kafka send error to %s: %s",
                topic,
                exc,
                exc_info=True,
            )
            return False

    async def send_batch(self, events: list[dict[str, Any]]) -> list[bool]:
        """Отправляет batch событий в Kafka."""
        if not self._is_available:
            logger.error("Kafka producer is not running")
            return [False] * len(events)

        futures = []

        for event in events:
            try:
                future = await self.producer.send(
                    topic=event["topic"],
                    value=event["value"],
                    key=event.get("key"),
                    headers=event.get("headers"),
                )
                futures.append(future)

            except Exception as exc:
                failed_future = asyncio.get_running_loop().create_future()
                failed_future.set_exception(exc)
                futures.append(failed_future)

        try:
            await self.producer.flush()
        except Exception as exc:
            logger.error("Kafka flush failed: %s", exc, exc_info=True)

        results = await asyncio.gather(*futures, return_exceptions=True)

        statuses: list[bool] = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(
                    "Kafka batch send error: %s",
                    result,
                    exc_info=True,
                )
                statuses.append(False)
            else:
                statuses.append(True)

        return statuses

    @property
    def _is_available(self) -> bool:
        """Проверяет, доступен ли producer."""
        return self._is_running and self.producer is not None
