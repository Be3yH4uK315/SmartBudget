import asyncio
import logging
from fastapi import FastAPI
from contextlib import asynccontextmanager
from arq import create_pool
from arq.connections import RedisSettings
from prometheus_fastapi_instrumentator import Instrumentator

from app.core.config import settings
from app.core.logging import setup_logging
from app.core.database import get_db_engine, get_session_factory
from app.core.redis import create_redis_pool, close_redis_pool
from app.api.routes import router as api_router

from app.services.ml.manager import modelManager
from app.services.classification.rules import ruleManager

from app.infrastructure.kafka.consumer import consume_loop

setup_logging()
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=== Service Starting ===")
    
    engine = get_db_engine()
    session_factory = get_session_factory(engine)
    app.state.engine = engine
    app.state.db_session_maker = session_factory
    
    app.state.redis_pool = await create_redis_pool()
    
    try:
        arq_pool = await create_pool(RedisSettings.from_dsn(settings.ARQ.REDIS_URL))
        app.state.arq_pool = arq_pool
    except Exception as e:
        logger.warning(f"ARQ Pool init failed (is Redis ready?): {e}")
    
    logger.info("Pre-loading models and rules...")
    await modelManager.check_for_updates(session_factory)
    await ruleManager.check_for_updates(session_factory)
    
    import redis.asyncio as aioredis
    consumer_redis = aioredis.Redis(connection_pool=app.state.redis_pool)
    
    consumer_task = asyncio.create_task(
        consume_loop(consumer_redis, session_factory)
    )
    logger.info("Background Consumer Task started.")

    yield
    
    logger.info("=== Service Shutting Down ===")
    
    consumer_task.cancel()
    try:
        await consumer_task
    except asyncio.CancelledError:
        logger.info("Consumer task cancelled successfully.")
    
    if hasattr(app.state, "arq_pool"):
        await app.state.arq_pool.close()
        
    await consumer_redis.aclose()
    await close_redis_pool(app.state.redis_pool)
    await app.state.engine.dispose()

app = FastAPI(
    title="Classification Service", 
    version="1.0", 
    lifespan=lifespan,
    docs_url="/api/v1/class/docs",
    openapi_url="/api/v1/class/openapi.json"
)

Instrumentator().instrument(app).expose(app)
app.include_router(api_router, prefix="/api/v1/class")