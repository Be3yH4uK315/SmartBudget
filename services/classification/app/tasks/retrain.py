import logging
import pandas as pd
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from app import models, unit_of_work, settings
from app.services.ml_service import MLService

logger = logging.getLogger(__name__)

async def retrain_model_task(ctx):
    """ARQ-задача для дообучения модели."""
    logger.info("Starting scheduled model retraining...")
    db_session_maker: async_sessionmaker[AsyncSession] = ctx.get("db_session_maker")
    
    if not db_session_maker:
        logger.error("No db_session_maker in arq context.")
        return

    uow = unit_of_work.UnitOfWork(db_session_maker)
    
    async with uow:
        logger.info("Finding latest 'READY' training dataset...")
        dataset = await uow.datasets.get_latest_ready()
        
        if not dataset:
            logger.info("No 'READY' training datasets found. Skipping.")
            return
        
        dataset_path = dataset.file_path
        dataset_ver = dataset.version

    logger.info(f"Found dataset: {dataset_ver} (Path: {dataset_path})")

    try:
        try:
            training_df = pd.read_parquet(dataset_path)
        except FileNotFoundError:
            logger.error(f"Dataset file not found: {dataset_path}. Skipping.")
            return

        if len(training_df) < 10:
            logger.info("Insufficient data. Skipping.")
            return

        new_version, metrics = await MLService.train_model(training_df)
        
        if "val_f1" not in metrics:
            metrics["val_f1"] = metrics.get("train_f1", 0.0)

        async with uow:
            model_entry = models.Model(
                name="lightgbm_tfidf",
                version=new_version,
                path=f"{settings.settings.ML.MODEL_PATH}",
                metrics=metrics,
                is_active=False
            )
            uow.models.create(model_entry)
            
            logger.info(f"Retraining finished. Model {new_version} created.")

    except Exception as e:
        logger.exception("Model retraining task failed")