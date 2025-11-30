import logging
from arq.connections import RedisSettings
from arq.cron import cron
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, AsyncEngine

from app import settings, logging_config, dependencies, repositories, services
from app.kafka_producer import kafka_producer

logger = logging.getLogger(__name__)

async def check_goals_deadlines_task(ctx):
    """
    ARQ-задача для проверки сроков целей.
    'ctx' содержит ресурсы из 'on_startup'.
    """
    db_maker: async_sessionmaker[AsyncSession] = ctx["db_session_maker"]
    kafka: services.KafkaProducer = ctx["kafka_producer"]
    
    if not db_maker or not kafka:
        logger.error("Worker context not properly initialized.")
        return

    async with db_maker() as session:
        try:
            repo = repositories.GoalRepository(session)
            service = services.GoalService(repo, kafka)
            await service.check_deadlines()
        except Exception as e:
            logger.error(f"Error in check_goals_deadlines_task: {e}")
            raise

async def on_startup(ctx):
    """Инициализирует ресурсы для воркера (DB, Kafka)."""
    logging_config.setup_logging()
    logger.info("Arq worker starting...")
    
    try:
        engine = dependencies.get_async_engine()
        db_maker = dependencies.get_async_session_maker()
        ctx["db_engine"] = engine
        ctx["db_session_maker"] = db_maker
    except Exception as e:
        logger.error(f"Failed to create DB engine/session maker: {e}")
        
    try:
        await kafka_producer.start()
        ctx["kafka_producer"] = kafka_producer
    except Exception as e:
        logger.error(f"Failed to start Kafka producer for worker: {e}")

async def on_shutdown(ctx):
    logger.info("Arq worker shutting down...")
    engine: AsyncEngine = ctx.get("db_engine")
    if engine:
        await engine.dispose()
        
    kafka: services.KafkaProducer = ctx.get("kafka_producer")
    if kafka:
        await kafka.stop()

class WorkerSettings:
    """Настройки Arq worker."""
    functions = [check_goals_deadlines_task]
    on_startup = on_startup
    on_shutdown = on_shutdown
    cron_jobs = [cron(check_goals_deadlines_task, hour=0, minute=0)]
    queue_name = settings.settings.arq.arq_queue_name
    redis_settings = RedisSettings.from_dsn(settings.settings.arq.redis_url)
    max_tries = 3