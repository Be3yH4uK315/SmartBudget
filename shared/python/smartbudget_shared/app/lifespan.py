import logging
from contextlib import asynccontextmanager
from collections.abc import Awaitable, Callable
from typing import Any


logger = logging.getLogger(__name__)

AsyncGetter = Callable[[], Awaitable[Any] | Any]
AsyncTask = Callable[[Any], Awaitable[Any] | Any]


async def _resolve(value: Awaitable[Any] | Any) -> Any:
    if hasattr(value, "__await__"):
        return await value
    return value


class LifespanConfig:
    """
    Конфигурация для управления жизненным циклом приложения, включающая функции 
    для инициализации ресурсов и задачи для выполнения при запуске и завершении работы приложения.
    """

    def __init__(
        self,
        engine_getter: AsyncGetter | None = None,
        redis_pool_getter: AsyncGetter | None = None,
        arq_pool_getter: AsyncGetter | None = None,
        startup_tasks: list[AsyncTask] | None = None,
        shutdown_tasks: list[AsyncTask] | None = None,
    ) -> None:
        self.engine_getter = engine_getter
        self.redis_pool_getter = redis_pool_getter
        self.arq_pool_getter = arq_pool_getter
        self.startup_tasks = startup_tasks or []
        self.shutdown_tasks = shutdown_tasks or []


def create_lifespan(config: LifespanConfig):
    """
    Создает функцию управления жизненным циклом приложения на основе предоставленной конфигурации.
    """

    @asynccontextmanager
    async def lifespan(app):
        logger.info("=== Application Startup ===")

        if config.engine_getter:
            engine = await _resolve(config.engine_getter())
            app.state.engine = engine
            logger.info("Database initialized")

        if config.redis_pool_getter:
            try:
                redis_pool = await _resolve(config.redis_pool_getter())
                app.state.redis_pool = redis_pool
                logger.info("Redis pool initialized")
            except Exception:
                logger.exception("Redis pool initialization failed")

        if config.arq_pool_getter:
            try:
                arq_pool = await _resolve(config.arq_pool_getter())
                app.state.arq_pool = arq_pool
                logger.info("ARQ pool initialized")
            except Exception:
                logger.exception("ARQ pool initialization failed")

        for task in config.startup_tasks:
            try:
                await _resolve(task(app))
                logger.debug("Startup task completed", extra={"task": task.__name__})
            except Exception:
                logger.exception("Startup task failed", extra={"task": task.__name__})

        yield

        logger.info("=== Application Shutdown ===")

        for task in reversed(config.shutdown_tasks):
            try:
                await _resolve(task(app))
                logger.debug("Shutdown task completed", extra={"task": task.__name__})
            except Exception:
                logger.exception("Shutdown task failed", extra={"task": task.__name__})

        if hasattr(app.state, "redis_pool") and app.state.redis_pool:
            try:
                await app.state.redis_pool.disconnect()
                logger.info("Redis pool closed")
            except Exception:
                logger.exception("Error closing Redis pool")

        if hasattr(app.state, "arq_pool") and app.state.arq_pool:
            try:
                await app.state.arq_pool.close()
                logger.info("ARQ pool closed")
            except Exception:
                logger.exception("Error closing ARQ pool")

        if hasattr(app.state, "engine") and app.state.engine:
            try:
                await app.state.engine.dispose()
                logger.info("Database connection closed")
            except Exception:
                logger.exception("Error closing database")

        logger.info("=== Application Shutdown Complete ===")

    return lifespan
