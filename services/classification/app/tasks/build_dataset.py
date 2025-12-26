import logging
import uuid
from datetime import datetime, timezone
import pandas as pd
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from app import models, settings, unit_of_work

logger = logging.getLogger(__name__)

async def build_training_dataset_task(ctx):
    """
    ARQ-задача (ETL) для создания "слепка" данных для обучения.
    Использует UnitOfWork для атомарности.
    """
    logger.info("Starting training dataset build task (ETL)...")
    
    db_session_maker: async_sessionmaker[AsyncSession] = ctx.get("db_session_maker")
    if not db_session_maker:
        logger.error("No db_session_maker in arq context. Aborting.")
        return
    
    dataset_id = uuid.uuid4()
    new_version = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    file_path = f"{settings.settings.ML.DATASET_PATH}/dataset_{new_version}.parquet"

    try:
        async with unit_of_work.UnitOfWork(db_session_maker) as uow:
            dataset_entry = models.TrainingDataset(
                training_dataset_id=dataset_id,
                version=new_version,
                file_path=file_path,
                status=models.TrainingDatasetStatus.BUILDING,
            )
            uow.datasets.create(dataset_entry)
            logger.info(f"Created dataset entry {dataset_id} with status BUILDING")
    except Exception as e:
        logger.error(f"Failed to create dataset entry: {e}")
        return

    try:
        data_for_training = []
        async with unit_of_work.UnitOfWork(db_session_maker) as uow:
            logger.info("Loading feedback data (last 180 days)...")
            data_for_training = await uow.feedback.get_training_data(days_limit=180)

        if not data_for_training:
            logger.info("No valid training data after ETL. Marking as FAILED.")
            async with unit_of_work.UnitOfWork(db_session_maker) as uow:
                dataset = await uow.datasets.get_by_id(dataset_id)
                if dataset:
                    await uow.datasets.update_status(
                        dataset, 
                        models.TrainingDatasetStatus.FAILED, 
                        {"error": "No valid data after ETL"}
                    )
            return

        logger.info(f"Converting {len(data_for_training)} rows to DataFrame...")
        df = pd.DataFrame(data_for_training)
        
        logger.info(f"Saving DataFrame to {file_path}...")
        df.to_parquet(file_path, index=False, engine='pyarrow')

        async with unit_of_work.UnitOfWork(db_session_maker) as uow:
            dataset = await uow.datasets.get_by_id(dataset_id)
            
            if dataset:
                await uow.datasets.update_status(
                    dataset, 
                    models.TrainingDatasetStatus.READY, 
                    {
                        "row_count": len(df),
                        "class_distribution": df['label'].value_counts().to_dict()
                    }
                )
                logger.info(f"SUCCESS: Training dataset {new_version} is READY.")
            else:
                logger.error(f"Dataset {dataset_id} not found during update!")

    except Exception as e:
        logger.exception("Training dataset build task failed")
        try:
            async with unit_of_work.UnitOfWork(db_session_maker) as uow:
                dataset = await uow.datasets.get_by_id(dataset_id)
                if dataset:
                    await uow.datasets.update_status(
                        dataset, 
                        models.TrainingDatasetStatus.FAILED, 
                        {"error": str(e)}
                    )
        except Exception:
            pass