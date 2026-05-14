import asyncio
import json
import logging
from pathlib import Path
from typing import Any

from arq.connections import RedisSettings
from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.core.config import settings
from app.core.logging import setup_logging
from app.workers.tasks import send_email_task, send_push_task

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
I18N_DIR = BASE_DIR / "i18n"
TEMPLATES_DIR = I18N_DIR / "templates"
HEALTH_FILE = Path("/tmp/healthy")

KEEP_ALIVE_INTERVAL_SECONDS = 5
JOB_TIMEOUT_SECONDS = 60
MAX_JOBS = 100
MAX_TRIES = 3


async def keep_alive_task() -> None:
    """Периодически обновляет health-файл worker-процесса."""
    while True:
        try:
            HEALTH_FILE.touch(exist_ok=True)
        except OSError:
            logger.debug("Failed to touch worker health file", exc_info=True)

        await asyncio.sleep(KEEP_ALIVE_INTERVAL_SECONDS)


async def on_startup(ctx: dict[str, Any]) -> None:
    """Инициализирует контекст ARQ worker."""
    setup_logging()
    logger.info("Notification ARQ worker starting")

    translations = _load_translations(I18N_DIR)
    ctx["translations"] = translations

    logger.info(
        "Loaded translations for locales: %s",
        sorted(translations.keys()),
    )

    TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)

    ctx["jinja_env"] = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        enable_async=True,
        autoescape=select_autoescape(["html", "xml"]),
    )
    ctx["health_task"] = asyncio.create_task(keep_alive_task())

    logger.info("Notification ARQ worker started")


async def on_shutdown(ctx: dict[str, Any]) -> None:
    """Корректно завершает ARQ worker."""
    logger.info("Notification ARQ worker shutting down")

    health_task: asyncio.Task | None = ctx.get("health_task")
    if health_task:
        health_task.cancel()
        try:
            await health_task
        except asyncio.CancelledError:
            pass

    logger.info("Notification ARQ worker stopped")


def _load_translations(i18n_dir: Path) -> dict[str, dict[str, str]]:
    """Загружает JSON-переводы из i18n directory."""
    translations: dict[str, dict[str, str]] = {}

    if not i18n_dir.exists():
        logger.warning("i18n directory does not exist: %s", i18n_dir)
        return translations

    for file_path in i18n_dir.glob("*.json"):
        locale = file_path.stem

        try:
            with file_path.open("r", encoding="utf-8") as file:
                translations[locale] = json.load(file)

        except json.JSONDecodeError as exc:
            logger.error(
                "Failed to parse translation file %s: %s",
                file_path,
                exc,
                exc_info=True,
            )

        except OSError as exc:
            logger.error(
                "Failed to read translation file %s: %s",
                file_path,
                exc,
                exc_info=True,
            )

    return translations


class WorkerSettings:
    """Настройки ARQ worker."""

    functions = [
        send_email_task,
        send_push_task,
    ]

    on_startup = on_startup
    on_shutdown = on_shutdown

    queue_name = settings.ARQ.ARQ_QUEUE_NAME
    redis_settings = RedisSettings.from_dsn(settings.ARQ.REDIS_URL)

    max_jobs = MAX_JOBS
    job_timeout = JOB_TIMEOUT_SECONDS
    max_tries = MAX_TRIES
