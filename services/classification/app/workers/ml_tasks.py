import logging
import pandas as pd
import uuid
from datetime import datetime, timezone
from app.core.config import settings
from app.infrastructure.db.uow import UnitOfWork
from app.infrastructure.db.models import TrainingDataset, TrainingDatasetStatus, Model
from app.services.ml.pipeline import MLPipeline

logger = logging.getLogger(__name__)

async def build_dataset_task(ctx):
    """ETL: Сбор данных из Feedback."""
    logger.info("Starting training dataset build task (ETL)...")
    
    db_session_maker = ctx.get("db_session_maker")
    if not db_session_maker:
        logger.error("No db_session_maker in arq context. Aborting.")
        return
    
    dataset_id = uuid.uuid4()
    new_version = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    file_path = f"{settings.ML.DATASET_PATH}/dataset_{new_version}.parquet"

    try:
        async with UnitOfWork(db_session_maker) as uow:
            dataset_entry = TrainingDataset(
                training_dataset_id=dataset_id,
                version=new_version,
                file_path=file_path,
                status=TrainingDatasetStatus.BUILDING,
            )
            uow.datasets.create(dataset_entry)
            logger.info(f"Created dataset entry {dataset_id} with status BUILDING")
    except Exception as e:
        logger.error(f"Failed to create dataset entry: {e}")
        return

    try:
        data_for_training = []
        async with UnitOfWork(db_session_maker) as uow:
            logger.info("Loading feedback data (last 180 days)...")
            data_for_training = await uow.feedback.get_training_data(days_limit=180)

        if not data_for_training:
            logger.info("No valid training data after ETL. Marking as FAILED.")
            async with UnitOfWork(db_session_maker) as uow:
                dataset = await uow.datasets.get_by_id(dataset_id)
                if dataset:
                    await uow.datasets.update_status(
                        dataset, 
                        TrainingDatasetStatus.FAILED, 
                        {"error": "No valid data after ETL"}
                    )
            return

        logger.info(f"Converting {len(data_for_training)} rows to DataFrame...")
        df = pd.DataFrame(data_for_training)
        
        logger.info(f"Saving DataFrame to {file_path}...")
        df.to_parquet(file_path, index=False, engine='pyarrow')

        async with UnitOfWork(db_session_maker) as uow:
            dataset = await uow.datasets.get_by_id(dataset_id)
            
            if dataset:
                await uow.datasets.update_status(
                    dataset, 
                    TrainingDatasetStatus.READY, 
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
            async with UnitOfWork(db_session_maker) as uow:
                dataset = await uow.datasets.get_by_id(dataset_id)
                if dataset:
                    await uow.datasets.update_status(
                        dataset, 
                        TrainingDatasetStatus.FAILED, 
                        {"error": str(e)}
                    )
        except Exception:
            pass

async def retrain_model_task(ctx):
    """ARQ-задача для дообучения модели."""
    logger.info("Starting scheduled model retraining...")
    db_session_maker = ctx.get("db_session_maker")
    
    if not db_session_maker:
        logger.error("No db_session_maker in arq context.")
        return

    uow = UnitOfWork(db_session_maker)
    
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

        new_version, metrics = await MLPipeline.train_model(training_df)
        
        if "val_f1" not in metrics:
            metrics["val_f1"] = metrics.get("train_f1", 0.0)

        async with uow:
            model_entry = Model(
                name="lightgbm_tfidf",
                version=new_version,
                path=f"{settings.ML.MODEL_PATH}",
                metrics=metrics,
                is_active=False
            )
            uow.models.create(model_entry)
            
            logger.info(f"Retraining finished. Model {new_version} created.")

    except Exception as e:
        logger.exception("Model retraining task failed")

async def promote_model_task(ctx):
    """ARQ-задача для валидации и продвижения новой модели."""
    logger.info("Starting model validation...")
    db_session_maker = ctx.get("db_session_maker")

    uow = UnitOfWork(db_session_maker)

    async with uow:
        active_model = await uow.models.get_active_model()
        candidate_model = await uow.models.get_latest_candidate()

        if not candidate_model:
            logger.info("No new candidate models.")
            return

        candidate_f1 = (candidate_model.metrics or {}).get("val_f1", 0)
        active_f1 = (active_model.metrics or {}).get("val_f1", 0) if active_model else 0

        if candidate_f1 < 0.6:
            logger.warning(f"Candidate {candidate_model.version} F1 ({candidate_f1}) too low.")
            return

        should_promote = False
        if active_model:
            activeMetrics = active_model.metrics or {}
            active_f1 = activeMetrics.get("val_f1", 0.0)

            if candidate_f1 > active_f1:
                logger.info(f"Promoting candidate {candidate_model.version} (F1 {candidate_f1} > {active_f1})")
                should_promote = True
            else:
                logger.info("Candidate not better.")
        else:
            logger.info("No active model. Promoting candidate.")
            should_promote = True

        if should_promote:
            uow.models.promote(candidate_model, active_model)
            logger.info(f"SUCCESS: Model {candidate_model.version} is now active.")