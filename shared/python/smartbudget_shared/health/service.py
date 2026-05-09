import logging
from typing import Any

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncEngine

from .checks import ArqHealthCheck, DatabaseHealthCheck, HealthCheck, RedisHealthCheck

logger = logging.getLogger(__name__)


class HealthCheckService:
    """Сервис выполнения health-check проверок компонентов приложения."""

    def __init__(self) -> None:
        self.checks: dict[str, HealthCheck] = {}

    def add_check(self, check: HealthCheck) -> None:
        """Добавляет проверку здоровья."""
        self.checks[check.name] = check

    def add_db_check(self, engine: AsyncEngine | None) -> None:
        """Добавляет проверку базы данных."""
        if engine:
            self.add_check(DatabaseHealthCheck(engine))

    def add_redis_check(self, redis_pool: Any) -> None:
        """Добавляет проверку Redis."""
        if redis_pool:
            self.add_check(RedisHealthCheck(redis_pool))

    def add_arq_check(self, arq_pool: Any) -> None:
        """Добавляет проверку ARQ."""
        if arq_pool:
            self.add_check(ArqHealthCheck(arq_pool))

    async def check_liveness(self) -> dict[str, str]:
        """Возвращает базовую liveness-проверку."""
        return {"status": "ok"}

    async def check_readiness(self) -> tuple[dict[str, Any], bool]:
        """Выполняет readiness-проверки всех зарегистрированных компонентов."""
        health_status: dict[str, str] = {}
        has_error = False

        for name, check in self.checks.items():
            try:
                status, is_healthy = await check.check()
                health_status[name] = status
                has_error = has_error or not is_healthy
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
    """Создает HealthCheckService на основе ресурсов из app.state."""
    service = HealthCheckService()
    app = request.app

    service.add_db_check(getattr(app.state, "engine", None))
    service.add_redis_check(getattr(app.state, "redis_pool", None))
    service.add_arq_check(getattr(app.state, "arq_pool", None))

    return service
