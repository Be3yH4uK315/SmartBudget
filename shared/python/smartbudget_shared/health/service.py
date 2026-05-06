import logging
from typing import Optional

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncEngine

from .checks import ArqHealthCheck, DatabaseHealthCheck, HealthCheck, RedisHealthCheck

logger = logging.getLogger(__name__)


class HealthCheckService:
    """Сервис для управления и выполнения проверок здоровья различных компонентов приложения."""

    def __init__(self):
        self.checks: dict[str, HealthCheck] = {}

    def add_check(self, check: HealthCheck) -> None:
        """Добавляет проверку здоровья в сервис."""
        self.checks[check.name] = check

    def add_db_check(self, engine: Optional[AsyncEngine]) -> None:
        """Добавляет проверку здоровья базы данных."""
        if engine:
            self.add_check(DatabaseHealthCheck(engine))

    def add_redis_check(self, redis_pool) -> None:
        """Добавляет проверку здоровья Redis."""
        if redis_pool:
            self.add_check(RedisHealthCheck(redis_pool))

    def add_arq_check(self, arq_pool) -> None:
        """Добавляет проверку здоровья ARQ."""
        if arq_pool:
            self.add_check(ArqHealthCheck(arq_pool))

    async def check_liveness(self) -> dict:
        """Базовая проверка живости."""
        return {"status": "ok"}

    async def check_readiness(self) -> tuple[dict, bool]:
        """Проверка готовности приложения, выполняющая все зарегистрированные проверки здоровья."""
        health_status: dict[str, str] = {}
        has_error = False

        for name, check in self.checks.items():
            try:
                status, is_healthy = await check.check()
                health_status[name] = status
                if not is_healthy:
                    has_error = True
            except Exception:
                logger.exception("Health check failed", extra={"check": name})
                health_status[name] = "error"
                has_error = True

        response = {
            "status": "not_ready" if has_error else "ready",
            "components": health_status,
        }

        return response, not has_error


def create_health_check_service(request: Request) -> HealthCheckService:
    """Создает и настраивает сервис проверки здоровья на основе ресурсов."""
    service = HealthCheckService()
    app = request.app

    engine = getattr(app.state, "engine", None)
    service.add_db_check(engine)

    redis_pool = getattr(app.state, "redis_pool", None)
    service.add_redis_check(redis_pool)

    arq_pool = getattr(app.state, "arq_pool", None)
    service.add_arq_check(arq_pool)

    return service
