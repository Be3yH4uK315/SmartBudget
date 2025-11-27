import logging
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Model

logger = logging.getLogger(__name__)

MIN_F1_THRESHOLD = 0.6 

async def validate_and_promote_model(ctx):
    """
    ARQ-задача для валидации и продвижения новой модели.
    """
    logger.info("Starting model validation and promotion task...")
    db_maker = ctx.get("db_session_maker")
    if not db_maker:
        logger.error("No db_session_maker in arq context. Aborting.")
        return

    async with db_maker() as session:
        try:
            active_model_stmt = await session.execute(
                select(Model).where(Model.is_active == True)
            )
            active_model = active_model_stmt.scalar_one_or_none()

            candidate_model_stmt = await session.execute(
                select(Model)
                .where(Model.is_active == False)
                .order_by(Model.created_at.desc())
                .limit(1)
            )
            candidate_model = candidate_model_stmt.scalar_one_or_none()

            if not candidate_model:
                logger.info("No new candidate models found. Nothing to promote.")
                return
            
            candidate_metrics = candidate_model.metrics or {}
            candidate_f1 = candidate_metrics.get("val_f1", 0.0)

            if candidate_f1 < MIN_F1_THRESHOLD:
                logger.warning(
                    f"Candidate {candidate_model.version} (F1: {candidate_f1:.4f}) "
                    f"is below minimum F1 threshold ({MIN_F1_THRESHOLD}). Rejecting."
                )
                return

            if active_model:
                active_metrics = active_model.metrics or {}
                active_f1 = active_metrics.get("val_f1", 0.0)
                
                logger.info(
                    f"Comparing candidate {candidate_model.version} (F1: {candidate_f1:.4f}) "
                    f"with active {active_model.version} (F1: {active_f1:.4f})."
                )

                if candidate_f1 > active_f1:
                    logger.info("Candidate is better. Promoting...")
                    active_model.is_active = False
                    candidate_model.is_active = True
                    await session.commit()
                    logger.info(f"SUCCESS: Model {candidate_model.version} is now active.")
                else:
                    logger.info("Candidate is not better than active model. No changes made.")
            
            else:
                logger.info(
                    f"No active model found. Promoting candidate {candidate_model.version} "
                    f"(F1: {candidate_f1:.4f}) as it meets threshold."
                )
                candidate_model.is_active = True
                await session.commit()
                logger.info(f"SUCCESS: Model {candidate_model.version} is now active.")

        except Exception as e:
            logger.exception("Model promotion task failed")
            await session.rollback()
            raise