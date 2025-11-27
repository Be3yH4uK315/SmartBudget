import logging
import pandas as pd
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Model, TrainingDataset, TrainingDatasetStatus
from app.services.ml_service import MLService
from app.settings import settings

logger = logging.getLogger(__name__)

async def retrain_model_task(ctx):
    """
    ARQ-задача для дообучения модели.
    """
    logger.info("Starting scheduled model retraining...")
    db_maker = ctx.get("db_session_maker")
    if not db_maker:
        logger.error("No db_session_maker in arq context. Aborting.")
        return

    async with db_maker() as session:
        try:
            logger.info("Finding latest 'READY' training dataset...")
            dataset_stmt = await session.execute(
                select(TrainingDataset)
                .where(TrainingDataset.status == TrainingDatasetStatus.READY)
                .order_by(TrainingDataset.created_at.desc())
                .limit(1)
            )
            dataset = dataset_stmt.scalar_one_or_none()

            if not dataset:
                logger.info("No 'READY' training datasets found. Skipping training.")
                return
            
            logger.info(f"Found dataset: {dataset.version} (Path: {dataset.file_path})")

            try:
                training_df = pd.read_parquet(dataset.file_path)
            except FileNotFoundError:
                logger.error(f"Dataset file not found: {dataset.file_path}. Skipping.")
                return
            
            if training_df.empty:
                 logger.info("Training dataset file is empty. Skipping.")
                 return

            min_samples = 10 
            if len(training_df) < min_samples:
                logger.info(f"Insufficient data in dataset ({len(training_df)} < {min_samples}). Skipping.")
                return

            new_version, metrics = MLService.train_model(training_df)
            
            if "val_f1" not in metrics:
                if "train_f1" in metrics:
                    logger.warning("No 'val_f1' metric found. Using 'train_f1' as fallback for 'val_f1'.")
                    metrics["val_f1"] = metrics["train_f1"]
                else:
                    logger.error("No 'val_f1' or 'train_f1' found in metrics. Setting 'val_f1' to 0.0.")
                    metrics["val_f1"] = 0.0

            model_entry = Model(
                name="lightgbm_tfidf",
                version=new_version,
                path=f"{settings.model_path}/{new_version}", 
                metrics=metrics,
                is_active=False
            )
            session.add(model_entry)
            
            await session.commit()
            logger.info(f"Retraining task finished successfully. Metrics: {metrics}")

        except ValueError as e:
            logger.error(f"Training aborted due to business logic error: {e}")
            await session.rollback()
        except Exception as e:
            logger.exception("Model retraining task failed")
            await session.rollback()
            raise