import logging
from datetime import datetime, timezone
import pandas as pd

from app import models, settings, repositories

logger = logging.getLogger(__name__)

async def buildTrainingDatasetTask(ctx):
    """
    ARQ-задача (ETL) для создания "слепка" данных для обучения.
    """
    logger.info("Starting training dataset build task (ETL)...")
    dbSessionMaker = ctx.get("db_session_maker")
    if not dbSessionMaker:
        logger.error("No db_session_maker in arq context. Aborting.")
        return

    async with dbSessionMaker() as session:
        feedbackReposity = repositories.FeedbackRepository(session)
        datasetReposity = repositories.DatasetRepository(session)
        
        newVersion = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        datasetEntry = models.TrainingDataset(
            version=newVersion,
            file_path=f"{settings.settings.ML.DATASET_PATH}/dataset_{newVersion}.parquet",
            status=models.TrainingDatasetStatus.BUILDING,
        )
        await datasetReposity.createDatasetEntry(datasetEntry)
        
        try:
            logger.info("Loading feedback data (last 180 days)...")
            dataForTraining = await feedbackReposity.getAllFeedbackData(days_limit=180)
            
            if not dataForTraining:
                logger.info("No valid training data after ETL. Aborting.")
                await datasetReposity.updateDatasetStatus(
                    datasetEntry, 
                    models.TrainingDatasetStatus.FAILED, 
                    {"error": "No valid data after ETL"}
                )
                return

            logger.info(f"Converting {len(dataForTraining)} rows to DataFrame...")
            df = pd.DataFrame(dataForTraining)
            
            logger.info(f"Saving DataFrame to {datasetEntry.filePath}...")
            df.to_parquet(datasetEntry.filePath, index=False, engine='pyarrow')

            await datasetReposity.updateDatasetStatus(
                datasetEntry, 
                models.TrainingDatasetStatus.READY, 
                {
                    "row_count": len(df),
                    "class_distribution": df['label'].value_counts().to_dict()
                }
            )
            logger.info(f"SUCCESS: Training dataset {newVersion} is ready.")

        except Exception as e:
            logger.exception("Training dataset build task failed")
            await session.rollback()
            await datasetReposity.updateDatasetStatus(
                datasetEntry, 
                models.TrainingDatasetStatus.FAILED, 
                {"error": str(e)}
            )
            raise