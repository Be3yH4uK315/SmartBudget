import logging

from app import repositories

logger = logging.getLogger(__name__)

MIN_F1_THRESHOLD = 0.6 

async def validateAndPromoteModel(ctx):
    """
    ARQ-задача для валидации и продвижения новой модели.
    """
    logger.info("Starting model validation and promotion task...")
    dbSessionMaker = ctx.get("db_session_maker")
    if not dbSessionMaker:
        logger.error("No db_session_maker in arq context. Aborting.")
        return

    async with dbSessionMaker() as session:
        modelReposity = repositories.ModelRepository(session)
        try:
            activeModel = await modelReposity.getActiveModel()
            candidateModel = await modelReposity.getLatestCandidateModel()

            if not candidateModel:
                logger.info("No new candidate models found. Nothing to promote.")
                return
            
            candidateMetrics = candidateModel.metrics or {}
            candidateF1 = candidateMetrics.get("val_f1", 0.0)

            if candidateF1 < MIN_F1_THRESHOLD:
                logger.warning(
                    f"Candidate {candidateModel.version} (F1: {candidateF1:.4f}) "
                    f"is below minimum F1 threshold ({MIN_F1_THRESHOLD}). Rejecting."
                )
                return

            if activeModel:
                activeMetrics = activeModel.metrics or {}
                activeF1 = activeMetrics.get("val_f1", 0.0)
                
                logger.info(
                    f"Comparing candidate {candidateModel.version} (F1: {candidateF1:.4f}) "
                    f"with active {activeModel.version} (F1: {activeF1:.4f})."
                )

                if candidateF1 > activeF1:
                    logger.info("Candidate is better. Promoting...")
                    await modelReposity.promoteModel(candidateModel, activeModel)
                    logger.info(f"SUCCESS: Model {candidateModel.version} is now active.")
                else:
                    logger.info("Candidate is not better than active model. No changes made.")

            else:
                logger.info("No active model found. Promoting candidate...")
                await modelReposity.promoteModel(candidateModel, None)
                logger.info(f"SUCCESS: Model {candidateModel.version} is now active.")

        except Exception as e:
            logger.exception("Model promotion task failed")
            await session.rollback()
            raise