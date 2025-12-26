import json
from datetime import date, datetime
from uuid import UUID
import logging
from pathlib import Path
from arq.connections import RedisSettings
from arq.cron import cron
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from aiokafka import AIOKafkaProducer

from app import settings, logging_config, unit_of_work
from app.tasks import retrain, promote, build_dataset

logger = logging.getLogger(__name__)
HEALTH_FILE = Path("/tmp/healthy")

async def touch_health_file() -> None:
    try: HEALTH_FILE.touch()
    except OSError: pass

class KafkaProducerWrapper:
    """Обертка, как в сервисе целей."""
    def __init__(self):
        self.producer = AIOKafkaProducer(
            bootstrap_servers=settings.settings.KAFKA.KAFKA_BOOTSTRAP_SERVERS
        )
    async def start(self): await self.producer.start()
    async def stop(self): await self.producer.stop()
    async def send_event(self, topic, data):
        
        def default_serializer(obj):
            if isinstance(obj, (datetime, date)): return obj.isoformat()
            if isinstance(obj, UUID): return str(obj)
            raise TypeError(f"Type {type(obj)} not serializable")

        try:
            val = json.dumps(data, default=default_serializer).encode('utf-8')
            await self.producer.send_and_wait(topic, val)
            return True
        except Exception as e:
            logger.error(f"Kafka send error: {e}")
            return False

async def process_outbox_task(ctx) -> None:
    db_session_maker = ctx["db_session_maker"]
    kafka: KafkaProducerWrapper = ctx["kafka_producer"]
    await touch_health_file()
    
    uow = unit_of_work.UnitOfWork(db_session_maker)
    async with uow:
        events = await uow.outbox.get_pending_events(limit=50)
        if not events: return
        
        sent_ids = []
        for event in events:
            if await kafka.send_event(event.topic, event.payload):
                sent_ids.append(event.event_id)
            else:
                await uow.outbox.handle_failed_event(event.event_id, "Send failed")
        
        await uow.outbox.delete_events(sent_ids)

async def on_startup(ctx):
    logging_config.setup_logging()
    logger.info("ARQ Worker starting...")
    
    engine = create_async_engine(settings.settings.DB.DB_URL)
    ctx["db_engine"] = engine
    ctx["db_session_maker"] = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    kafka = KafkaProducerWrapper()
    await kafka.start()
    ctx["kafka_producer"] = kafka

async def on_shutdown(ctx):
    if ctx.get("kafka_producer"): await ctx["kafka_producer"].stop()
    if ctx.get("db_engine"): await ctx["db_engine"].dispose()

class WorkerSettings:
    functions = [
        process_outbox_task,
        retrain.retrain_model_task,
        promote.validate_and_promote_model,
        build_dataset.build_training_dataset_task
    ]
    on_startup = on_startup
    on_shutdown = on_shutdown
    cron_jobs = [
        cron(process_outbox_task, minute=set(range(60))),
        cron(build_dataset.build_training_dataset_task, weekday=6, hour=0, minute=0),
        cron(retrain.retrain_model_task, hour=2, minute=0),
        cron(promote.validate_and_promote_model, hour=3, minute=0)
    ]
    redis_settings = RedisSettings.from_dsn(settings.settings.ARQ.REDIS_URL)
    queue_name = settings.settings.ARQ.ARQ_QUEUE_NAME