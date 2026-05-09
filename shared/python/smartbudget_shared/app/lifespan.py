import logging
from collections.abc import Awaitable, Callable
from contextlib import asynccontextmanager
from typing import Any

logger = logging.getLogger(__name__)

AsyncGetter = Callable[[], Awaitable[Any] | Any]
AsyncTask = Callable[[Any], Awaitable[Any] | Any]
SessionFactoryGetter = Callable[[Any], Any]


async def _resolve(value: Awaitable[Any] | Any) -> Any:
    """Возвращает результат awaitable или обычное значение."""
    if hasattr(value, "__await__"):
        return await value

    return value


class LifespanConfig:
    """Конфигурация общего lifespan для FastAPI-сервисов."""

    def __init__(
        self,
        engine_getter: AsyncGetter | None = None,
        session_factory_getter: SessionFactoryGetter | None = None,
        redis_pool_getter: AsyncGetter | None = None,
        redis_pool_closer: AsyncTask | None = None,
        arq_pool_getter: AsyncGetter | None = None,
        startup_tasks: list[AsyncTask] | None = None,
        shutdown_tasks: list[AsyncTask] | None = None,
    ) -> None:
        self.engine_getter = engine_getter
        self.session_factory_getter = session_factory_getter
        self.redis_pool_getter = redis_pool_getter
        self.redis_pool_closer = redis_pool_closer
        self.arq_pool_getter = arq_pool_getter
        self.startup_tasks = startup_tasks or []
        self.shutdown_tasks = shutdown_tasks or []


def create_lifespan(config: LifespanConfig):
    """Создает FastAPI lifespan function по переданной конфигурации."""

    @asynccontextmanager
    async def lifespan(app):
        logger.info("=== Application Startup ===")

        if config.engine_getter:
            engine = await _resolve(config.engine_getter())
            app.state.engine = engine

            if config.session_factory_getter:
                app.state.db_session_maker = config.session_factory_getter(engine)

            logger.info("Database initialized")

        if config.redis_pool_getter:
            try:
                redis_pool = await _resolve(config.redis_pool_getter())
                app.state.redis_pool = redis_pool
                logger.info("Redis pool initialized")
            except Exception:
                app.state.redis_pool = None
                logger.exception("Redis pool initialization failed")

        if config.arq_pool_getter:
            try:
                arq_pool = await _resolve(config.arq_pool_getter())
                app.state.arq_pool = arq_pool
                logger.info("ARQ pool initialized")
            except Exception:
                app.state.arq_pool = None
                logger.exception("ARQ pool initialization failed")

        for task in config.startup_tasks:
            try:
                await _resolve(task(app))
                logger.debug(
                    "Startup task completed",
                    extra={"task": getattr(task, "__name__", str(task))},
                )
            except Exception:
                logger.exception(
                    "Startup task failed",
                    extra={"task": getattr(task, "__name__", str(task))},
                )

        try:
            yield
        finally:
            logger.info("=== Application Shutdown ===")

            for task in reversed(config.shutdown_tasks):
                try:
                    await _resolve(task(app))
                    logger.debug(
                        "Shutdown task completed",
                        extra={"task": getattr(task, "__name__", str(task))},
                    )
                except Exception:
                    logger.exception(
                        "Shutdown task failed",
                        extra={"task": getattr(task, "__name__", str(task))},
                    )

            redis_pool = getattr(app.state, "redis_pool", None)
            if redis_pool:
                try:
                    if config.redis_pool_closer:
                        await _resolve(config.redis_pool_closer(redis_pool))
                    else:
                        await redis_pool.disconnect()
                    logger.info("Redis pool closed")
                except Exception:
                    logger.exception("Error closing Redis pool")

            arq_pool = getattr(app.state, "arq_pool", None)
            if arq_pool:
                try:
                    await arq_pool.close()
                    logger.info("ARQ pool closed")
                except Exception:
                    logger.exception("Error closing ARQ pool")

            engine = getattr(app.state, "engine", None)
            if engine:
                try:
                    await engine.dispose()
                    logger.info("Database connection closed")
                except Exception:
                    logger.exception("Error closing database")

            logger.info("=== Application Shutdown Complete ===")

    return lifespan
