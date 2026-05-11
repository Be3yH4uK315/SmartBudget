import asyncio
import json
import logging
from typing import Any

from aiokafka import AIOKafkaProducer

from app.core.config import settings
from app.core.context import get_request_id

logger = logging.getLogger(__name__)

SEND_TIMEOUT_SECONDS = 10
REQUEST_ID_HEADER = "X-Request-ID"


class KafkaProducerWrapper:
    """Kafka producer с контролем состояния, request_id headers и batch-отправкой."""

    def __init__(self) -> None:
        self.producer: AIOKafkaProducer | None = None
        self._is_running = False

    async def start(self) -> None:
        """Запускает Kafka producer."""
        if self._is_running:
            return

        self.producer = AIOKafkaProducer(
            bootstrap_servers=settings.KAFKA.KAFKA_BOOTSTRAP_SERVERS,
            acks="all",
            linger_ms=50,
            request_timeout_ms=SEND_TIMEOUT_SECONDS * 1000,
        )

        await self.producer.start()
        self._is_running = True

        logger.info(
            "Kafka producer started",
            extra={
                "bootstrap_servers": settings.KAFKA.KAFKA_BOOTSTRAP_SERVERS,
            },
        )

    async def stop(self) -> None:
        """Останавливает Kafka producer."""
        if not self._is_available:
            return

        assert self.producer is not None

        await self.producer.stop()
        self._is_running = False
        self.producer = None

        logger.info("Kafka producer stopped")

    async def send_json(
        self,
        topic: str,
        payload: dict[str, Any],
        key: str | bytes | None = None,
        headers: list[tuple[str, bytes]] | None = None,
        wait: bool = True,
    ) -> bool:
        """Отправляет dict payload в Kafka как JSON."""
        return await self.send_event(
            topic=topic,
            value=self._to_json_bytes(payload),
            key=self._normalize_key(key),
            headers=self._merge_headers(headers),
            wait=wait,
        )

    async def send_event(
        self,
        topic: str,
        value: bytes,
        key: bytes | str | None = None,
        headers: list[tuple[str, bytes]] | None = None,
        wait: bool = True,
    ) -> bool:
        """Отправляет одно событие в Kafka."""
        if not self._is_available:
            logger.error(
                "Kafka producer is not running",
                extra={"topic": topic},
            )
            return False

        assert self.producer is not None

        normalized_key = self._normalize_key(key)
        merged_headers = self._merge_headers(headers)

        try:
            if wait:
                await asyncio.wait_for(
                    self.producer.send_and_wait(
                        topic=topic,
                        key=normalized_key,
                        value=value,
                        headers=merged_headers,
                    ),
                    timeout=SEND_TIMEOUT_SECONDS,
                )
            else:
                await self.producer.send(
                    topic=topic,
                    key=normalized_key,
                    value=value,
                    headers=merged_headers,
                )

            logger.debug(
                "Kafka event sent",
                extra={
                    "topic": topic,
                    "key": normalized_key.decode("utf-8", errors="replace")
                    if normalized_key
                    else None,
                    "wait": wait,
                },
            )

            return True

        except Exception as exc:
            logger.error(
                "Kafka send error",
                extra={"topic": topic, "error": str(exc)},
                exc_info=True,
            )
            return False

    async def send_batch(self, events: list[dict[str, Any]]) -> list[bool]:
        """Отправляет несколько событий в Kafka и возвращает статус каждого."""
        if not events:
            return []

        if not self._is_available:
            logger.error("Kafka producer is not running")
            return [False] * len(events)

        assert self.producer is not None

        futures: list[Any] = []

        for event in events:
            try:
                topic = event["topic"]
                value = self._normalize_value(event["value"])
                key = self._normalize_key(event.get("key"))
                headers = self._merge_headers(event.get("headers"))

                future = await self.producer.send(
                    topic=topic,
                    value=value,
                    key=key,
                    headers=headers,
                )
                futures.append(future)

            except Exception as exc:
                failed_future = asyncio.get_running_loop().create_future()
                failed_future.set_exception(exc)
                futures.append(failed_future)

        try:
            await asyncio.wait_for(
                self.producer.flush(),
                timeout=SEND_TIMEOUT_SECONDS,
            )
        except Exception as exc:
            logger.error(
                "Kafka flush failed",
                extra={"error": str(exc)},
                exc_info=True,
            )

        results = await asyncio.gather(*futures, return_exceptions=True)

        statuses: list[bool] = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(
                    "Kafka batch send error",
                    extra={"error": str(result)},
                    exc_info=True,
                )
                statuses.append(False)
            else:
                statuses.append(True)

        return statuses

    @property
    def _is_available(self) -> bool:
        """Проверяет, готов ли producer к отправке сообщений."""
        return self._is_running and self.producer is not None

    @staticmethod
    def _to_json_bytes(payload: dict[str, Any]) -> bytes:
        """Сериализует dict в JSON bytes."""
        return json.dumps(
            payload,
            ensure_ascii=False,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")

    @classmethod
    def _normalize_value(cls, value: Any) -> bytes:
        """Нормализует Kafka value до bytes."""
        if isinstance(value, bytes):
            return value

        if isinstance(value, str):
            return value.encode("utf-8")

        if isinstance(value, dict):
            return cls._to_json_bytes(value)

        raise TypeError(f"Unsupported Kafka value type: {type(value).__name__}")

    @staticmethod
    def _normalize_key(key: bytes | str | None) -> bytes | None:
        """Нормализует Kafka key до bytes."""
        if key is None:
            return None

        if isinstance(key, bytes):
            return key

        return key.encode("utf-8")

    @staticmethod
    def _build_request_headers() -> list[tuple[str, bytes]]:
        """Формирует Kafka headers с request_id."""
        headers: list[tuple[str, bytes]] = []

        request_id = get_request_id()
        if request_id and request_id != "unknown":
            headers.append((REQUEST_ID_HEADER, request_id.encode("utf-8")))

        return headers

    @classmethod
    def _merge_headers(
        cls,
        headers: list[tuple[str, bytes]] | None,
    ) -> list[tuple[str, bytes]] | None:
        """Добавляет request_id header, если он еще не передан явно."""
        merged = list(headers or [])

        has_request_id = any(key == REQUEST_ID_HEADER for key, _ in merged)
        if not has_request_id:
            merged.extend(cls._build_request_headers())

        return merged or None
