import logging

from app import repositories

logger = logging.getLogger(__name__)

MIN_F1_THRESHOLD = 0.6 

async def validate_and_promote_model(ctx):
    """
    ARQ-задача для валидации и продвижения новой модели.
    """
    logger.info("Starting model validation and promotion task...")
    db_session_maker = ctx.get("db_session_maker")
    if not db_session_maker:
        logger.error("No db_session_maker in arq context. Aborting.")
        return

    async with db_session_maker() as session:
        model_repository = repositories.ModelRepository(session)
        try:
            active_model = await model_repository.get_active_model()
            candidate_model = await model_repository.get_latest_candidate_model()

            if not candidate_model:
                logger.info("No new candidate models found. Nothing to promote.")
                return
            
            candidateMetrics = candidate_model.metrics or {}
            candidateF1 = candidateMetrics.get("val_f1", 0.0)

            if candidateF1 < MIN_F1_THRESHOLD:
                logger.warning(
                    f"Candidate {candidate_model.version} (F1: {candidateF1:.4f}) "
                    f"is below minimum F1 threshold ({MIN_F1_THRESHOLD}). Rejecting."
                )
                return

            if active_model:
                activeMetrics = active_model.metrics or {}
                activeF1 = activeMetrics.get("val_f1", 0.0)
                
                logger.info(
                    f"Comparing candidate {candidate_model.version} (F1: {candidateF1:.4f}) "
                    f"with active {active_model.version} (F1: {activeF1:.4f})."
                )

                if candidateF1 > activeF1:
                    logger.info("Candidate is better. Promoting...")
                    await model_repository.promote_model(candidate_model, active_model)
                    logger.info(f"SUCCESS: Model {candidate_model.version} is now active.")
                else:
                    logger.info("Candidate is not better than active model. No changes made.")

            else:
                logger.info("No active model found. Promoting candidate...")
                await model_repository.promote_model(candidate_model, None)
                logger.info(f"SUCCESS: Model {candidate_model.version} is now active.")

        except Exception as e:
            logger.exception("Model promotion task failed")
            await session.rollback()
            raise