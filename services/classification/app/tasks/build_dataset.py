import logging
from datetime import datetime, timezone
import pandas as pd

from app import models, settings, repositories

logger = logging.getLogger(__name__)

async def build_training_dataset_task(ctx):
    """
    ARQ-задача (ETL) для создания "слепка" данных для обучения.
    """
    logger.info("Starting training dataset build task (ETL)...")
    db_maker = ctx.get("db_session_maker")
    if not db_maker:
        logger.error("No db_session_maker in arq context. Aborting.")
        return

    async with db_maker() as session:
        feedback_repo = repositories.FeedbackRepository(session)
        dataset_repo = repositories.DatasetRepository(session)
        
        new_version = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        dataset_entry = models.TrainingDataset(
            version=new_version,
            file_path=f"{settings.settings.ml.dataset_path}/dataset_{new_version}.parquet",
            status=models.TrainingDatasetStatus.BUILDING,
        )
        await dataset_repo.create_dataset_entry(dataset_entry)
        
        try:
            logger.info("Loading feedback data (last 180 days)...")
            data_for_training = await feedback_repo.get_all_feedback_data(days_limit=180)
            
            if not data_for_training:
                logger.info("No valid training data after ETL. Aborting.")
                await dataset_repo.update_dataset_status(
                    dataset_entry, 
                    models.TrainingDatasetStatus.FAILED, 
                    {"error": "No valid data after ETL"}
                )
                return

            logger.info(f"Converting {len(data_for_training)} rows to DataFrame...")
            df = pd.DataFrame(data_for_training)
            
            logger.info(f"Saving DataFrame to {dataset_entry.file_path}...")
            df.to_parquet(dataset_entry.file_path, index=False, engine='pyarrow')

            await dataset_repo.update_dataset_status(
                dataset_entry, 
                models.TrainingDatasetStatus.READY, 
                {
                    "row_count": len(df),
                    "class_distribution": df['label'].value_counts().to_dict()
                }
            )
            logger.info(f"SUCCESS: Training dataset {new_version} is ready.")

        except Exception as e:
            logger.exception("Training dataset build task failed")
            await session.rollback()
            await dataset_repo.update_dataset_status(
                dataset_entry, 
                models.TrainingDatasetStatus.FAILED, 
                {"error": str(e)}
            )
            raise