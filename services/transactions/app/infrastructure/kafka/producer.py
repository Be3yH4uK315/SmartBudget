import asyncio
import logging
from typing import Any

import orjson
from aiokafka import AIOKafkaProducer

from app.core.config import settings
from app.core.context import get_request_id
from app.utils.serialization import to_jsonable

logger = logging.getLogger(__name__)
SEND_TIMEOUT = 10


class KafkaProducerWrapper:
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
        if self._is_running:
            await self.producer.stop()
            self._is_running = False
            logger.info("Kafka producer stopped")

    async def send_json(
        self,
        topic: str,
        payload: dict[str, Any],
        key: str | None = None,
    ) -> bool:
        if not self._is_running:
            logger.error("Kafka producer is not running")
            return False

        headers = []
        if request_id := get_request_id():
            headers.append(("X-Request-ID", request_id.encode("utf-8")))

        try:
            await asyncio.wait_for(
                self.producer.send_and_wait(
                    topic=topic,
                    key=key.encode("utf-8") if key else None,
                    value=orjson.dumps(to_jsonable(payload)),
                    headers=headers or None,
                ),
                timeout=SEND_TIMEOUT,
            )
            return True
        except Exception as exc:
            logger.error("Kafka send error to %s: %s", topic, exc, exc_info=True)
            return False
