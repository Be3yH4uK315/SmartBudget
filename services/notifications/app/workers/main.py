import asyncio
import json
import logging
from pathlib import Path
from arq.connections import RedisSettings
from jinja2 import Environment, FileSystemLoader

from app.core.config import settings
from app.core.logging import setup_logging
from app.workers.tasks import send_email_task, send_push_task

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
HEALTH_FILE = Path("/tmp/healthy")

async def keep_alive_task() -> None:
    while True:
        try:
            HEALTH_FILE.touch(exist_ok=True)
        except OSError:
            pass
        await asyncio.sleep(5)

async def on_startup(ctx: dict) -> None:
    """Инициализация контекста воркера Arq."""
    setup_logging()
    logger.info("Starting Notification Arq Worker...")

    translations = {}
    i18n_dir = BASE_DIR / "i18n"
    if i18n_dir.exists():
        for file_path in i18n_dir.glob("*.json"):
            locale = file_path.stem
            with open(file_path, "r", encoding="utf-8") as f:
                translations[locale] = json.load(f)
    ctx["translations"] = translations
    logger.info("Loaded translations for locales: %s", list(translations.keys()))

    templates_dir = i18n_dir / "templates"
    if not templates_dir.exists():
        templates_dir.mkdir(parents=True, exist_ok=True)
    
    ctx["jinja_env"] = Environment(
        loader=FileSystemLoader(str(templates_dir)), 
        enable_async=True
    )
    ctx["health_task"] = asyncio.create_task(keep_alive_task())

async def on_shutdown(ctx: dict) -> None:
    """Очистка ресурсов при завершении работы воркера."""
    logger.info("Shutting down Notification Arq Worker...")
    health_task = ctx.get("health_task")
    if health_task:
        health_task.cancel()

class WorkerSettings:
    """Настройки воркера ARQ."""
    functions = [
        send_email_task,
        send_push_task,
    ]
    on_startup = on_startup
    on_shutdown = on_shutdown
    
    queue_name = settings.ARQ.ARQ_QUEUE_NAME
    redis_settings = RedisSettings.from_dsn(settings.ARQ.REDIS_URL)
    
    max_jobs = 100
    job_timeout = 60
    max_tries = 3 
