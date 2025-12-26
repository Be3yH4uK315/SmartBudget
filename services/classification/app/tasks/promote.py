import logging
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from app import unit_of_work

logger = logging.getLogger(__name__)

MIN_F1_THRESHOLD = 0.6 

async def validate_and_promote_model(ctx):
    """ARQ-задача для валидации и продвижения новой модели."""
    logger.info("Starting model validation...")
    db_session_maker: async_sessionmaker[AsyncSession] = ctx.get("db_session_maker")
    
    uow = unit_of_work.UnitOfWork(db_session_maker)

    async with uow:
        active_model = await uow.models.get_active_model()
        candidate_model = await uow.models.get_latest_candidate()

        if not candidate_model:
            logger.info("No new candidate models.")
            return
        
        candidateMetrics = candidate_model.metrics or {}
        candidateF1 = candidateMetrics.get("val_f1", 0.0)

        if candidateF1 < MIN_F1_THRESHOLD:
            logger.warning(f"Candidate {candidate_model.version} F1 ({candidateF1}) too low.")
            return

        should_promote = False
        if active_model:
            activeMetrics = active_model.metrics or {}
            activeF1 = activeMetrics.get("val_f1", 0.0)
            
            if candidateF1 > activeF1:
                logger.info(f"Promoting candidate {candidate_model.version} (F1 {candidateF1} > {activeF1})")
                should_promote = True
            else:
                logger.info("Candidate not better.")
        else:
            logger.info("No active model. Promoting candidate.")
            should_promote = True

        if should_promote:
            uow.models.promote(candidate_model, active_model)
            logger.info(f"SUCCESS: Model {candidate_model.version} is now active.")