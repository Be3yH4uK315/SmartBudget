import logging
from typing import Any, Callable, Optional

from sqlalchemy.ext.asyncio import AsyncEngine

logger = logging.getLogger(__name__)


class AppStateManager:
    """Менеджер состояния приложения для хранения и управления ресурсами, такими как база данных, Redis, ARQ pool и Kafka producer."""

    def __init__(self):
        self.engine: Optional[AsyncEngine] = None
        self.db_session_maker: Optional[Any] = None
        self.redis_pool: Optional[Any] = None
        self.arq_pool: Optional[Any] = None
        self.kafka_producer: Optional[Any] = None

    async def cleanup(self) -> None:
        """Очистка ресурсов при завершении работы приложения."""
        if self.kafka_producer:
            try:
                await self.kafka_producer.stop()
            except Exception:
                logger.exception("Error stopping Kafka producer")

        if self.arq_pool:
            try:
                await self.arq_pool.close()
            except Exception:
                logger.exception("Error closing ARQ pool")

        if self.redis_pool:
            try:
                await self.redis_pool.disconnect()
            except Exception:
                logger.exception("Error closing Redis pool")

        if self.engine:
            try:
                await self.engine.dispose()
            except Exception:
                logger.exception("Error disposing engine")


class LifespanContext:
    """
    Контекст управления жизненным циклом приложения,
    позволяющий регистрировать и выполнять обработчики при запуске и завершении работы приложения.
    """

    def __init__(self, state_manager: AppStateManager):
        self.state_manager = state_manager
        self.startup_handlers: list[Callable] = []
        self.shutdown_handlers: list[Callable] = []

    def on_startup(self, handler: Callable) -> Callable:
        """Регистрирует обработчик для выполнения при запуске приложения."""
        self.startup_handlers.append(handler)
        return handler

    def on_shutdown(self, handler: Callable) -> Callable:
        """Регистрирует обработчик для выполнения при завершении работы приложения."""
        self.shutdown_handlers.append(handler)
        return handler

    async def execute_startup(self) -> None:
        """Выполняет все зарегистрированные обработчики запуска приложения."""
        for handler in self.startup_handlers:
            try:
                result = handler(self.state_manager)
                if hasattr(result, "__aiter__"):
                    async for _ in result:
                        pass
                elif hasattr(result, "__await__"):
                    await result
            except Exception:
                logger.exception("Startup handler failed")
                raise

    async def execute_shutdown(self) -> None:
        """Выполняет все зарегистрированные обработчики завершения работы приложения."""
        for handler in reversed(self.shutdown_handlers):
            try:
                result = handler(self.state_manager)
                if hasattr(result, "__aiter__"):
                    async for _ in result:
                        pass
                elif hasattr(result, "__await__"):
                    await result
            except Exception:
                logger.exception("Shutdown handler failed")
