import logging
import pandas as pd

from app import models, repositories, settings
from app.services.ml_service import MLService

logger = logging.getLogger(__name__)

async def retrainModelTask(ctx):
    """
    ARQ-задача для дообучения модели.
    """
    logger.info("Starting scheduled model retraining...")
    dbSessionMaker = ctx.get("db_session_maker")
    if not dbSessionMaker:
        logger.error("No db_session_maker in arq context. Aborting.")
        return

    async with dbSessionMaker() as session:
        datasetReposity = repositories.DatasetRepository(session)
        modelReposity = repositories.ModelRepository(session)
        
        try:
            logger.info("Finding latest 'READY' training dataset...")
            dataset = await datasetReposity.getLatestReadyDataset()

            if not dataset:
                logger.info("No 'READY' training datasets found. Skipping training.")
                return
            
            logger.info(f"Found dataset: {dataset.version} (Path: {dataset.filePath})")

            try:
                trainingDf = pd.read_parquet(dataset.filePath)
            except FileNotFoundError:
                logger.error(f"Dataset file not found: {dataset.filePath}. Skipping.")
                return
            
            if trainingDf.empty:
                 logger.info("Training dataset file is empty. Skipping.")
                 return

            minSamples = 10 
            if len(trainingDf) < minSamples:
                logger.info(f"Insufficient data in dataset ({len(trainingDf)} < {minSamples}). Skipping.")
                return

            newVersion, metrics = MLService.train_model(trainingDf)
            
            if "val_f1" not in metrics:
                if "train_f1" in metrics:
                    logger.warning("No 'val_f1' metric found. Using 'train_f1' as fallback for 'val_f1'.")
                    metrics["val_f1"] = metrics["train_f1"]
                else:
                    logger.error("No 'val_f1' or 'train_f1' found in metrics. Setting 'val_f1' to 0.0.")
                    metrics["val_f1"] = 0.0

            modelEntry = models.Model(
                name="lightgbm_tfidf",
                version=newVersion,
                path=f"{settings.settings.ML.MODEL_PATH}/{newVersion}",
                metrics=metrics,
                isActive=False
            )
            await modelReposity.createModel(modelEntry)
            
            logger.info(f"Retraining task finished successfully. Metrics: {metrics}")

        except ValueError as e:
            logger.error(f"Training aborted due to business logic error: {e}")
            await session.rollback()
        except Exception as e:
            logger.exception("Model retraining task failed")
            await session.rollback()
            raise