import logging
import pandas as pd
import uuid
import os
from datetime import datetime, timezone
from app.core.config import settings
from app.infrastructure.db.uow import UnitOfWork
from app.infrastructure.db.models import TrainingDataset, TrainingDatasetStatus, Model
from app.services.ml.pipeline import MLPipeline

logger = logging.getLogger(__name__)

async def build_dataset_task(ctx):
    """ETL: Сбор данных из Feedback за последние 180 дней."""
    logger.info("Starting training dataset build task (ETL)...")
    
    db_session_maker = ctx.get("db_session_maker")
    if not db_session_maker:
        logger.error("No db_session_maker in arq context. Aborting.")
        return
    
    dataset_id = uuid.uuid4()
    new_version = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    
    os.makedirs(settings.ML.DATASET_PATH, exist_ok=True)
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
        async with UnitOfWork(db_session_maker) as uow:
            logger.info("Loading feedback data...")
            data_rows = await uow.feedback.get_training_data(days_limit=180)
            marked_count = await uow.feedback.mark_unprocessed_as_processed()
            logger.info(f"Marked {marked_count} feedback rows as processed.")

        if not data_rows:
            raise ValueError("No training data found (empty list)")

        logger.info(f"Converting {len(data_rows)} rows to DataFrame...")
        df = pd.DataFrame(data_rows)
        df['label'] = df['label'].astype('int32')
        
        logger.info(f"Saving to {file_path}...")
        df.to_parquet(file_path, index=False, engine='pyarrow', compression='snappy')

        async with UnitOfWork(db_session_maker) as uow:
            dataset = await uow.datasets.get_by_id(dataset_id)
            if dataset:
                dist = df['label'].value_counts().to_dict()
                dist_str = {str(k): int(v) for k, v in dist.items()}
                
                await uow.datasets.update_status(
                    dataset, 
                    TrainingDatasetStatus.READY, 
                    {
                        "row_count": len(df),
                        "class_distribution": dist_str
                    }
                )
                logger.info(f"SUCCESS: Dataset {new_version} READY. Rows: {len(df)}")

    except Exception as e:
        logger.exception("Training dataset build failed")
        async with UnitOfWork(db_session_maker) as uow:
            dataset = await uow.datasets.get_by_id(dataset_id)
            if dataset:
                await uow.datasets.update_status(
                    dataset, 
                    TrainingDatasetStatus.FAILED, 
                    {"error": str(e)}
                )

async def retrain_model_task(ctx):
    """Обучение модели на последнем готовом датасете."""
    logger.info("Starting scheduled model retraining...")
    db_session_maker = ctx.get("db_session_maker")
    
    uow = UnitOfWork(db_session_maker)
    async with uow:
        logger.info("Finding latest 'READY' training dataset...")
        dataset = await uow.datasets.get_latest_ready()
        if not dataset:
            logger.info("No 'READY' training datasets found. Skipping.")
            return
        dataset_path = dataset.file_path

    try:
        if not os.path.exists(dataset_path):
            logger.error(f"File not found: {dataset_path}")
            return

        training_df = pd.read_parquet(dataset_path)
        
        if len(training_df) < 50:
            logger.info("Not enough data (<50 rows). Skipping.")
            return

        new_version, metrics = await MLPipeline.train_model(training_df)
        
        async with uow:
            model_entry = Model(
                name="lightgbm_tfidf",
                version=new_version,
                path=settings.ML.MODEL_PATH,
                metrics=metrics,
                is_active=False
            )
            uow.models.create(model_entry)
            logger.info(f"Model {new_version} created. F1: {metrics.get('val_f1_weighted', 0):.4f}")

    except Exception as e:
        logger.exception("Model retraining task failed")

async def promote_model_task(ctx):
    """Валидация и продвижение модели."""
    logger.info("Starting model promotion check...")
    db_session_maker = ctx.get("db_session_maker")
    uow = UnitOfWork(db_session_maker)

    async with uow:
        active_model = await uow.models.get_active_model()
        candidate = await uow.models.get_latest_candidate()

        if not candidate:
            return

        cand_metrics = candidate.metrics or {}
        cand_f1 = cand_metrics.get("val_f1_weighted", cand_metrics.get("val_f1", 0))
        
        if cand_f1 < 0.6:
            logger.warning(f"Candidate {candidate.version} rejected. Low F1: {cand_f1:.3f}")
            return

        should_promote = False
        
        if active_model:
            act_metrics = active_model.metrics or {}
            act_f1 = act_metrics.get("val_f1_weighted", act_metrics.get("val_f1", 0))
            
            if cand_f1 > act_f1:
                logger.info(f"Promoting: Candidate F1 {cand_f1:.3f} > Active {act_f1:.3f}")
                should_promote = True
            elif cand_f1 > (act_f1 - 0.02): 
                logger.info("Candidate not significantly better.")
        else:
            logger.info("No active model. Promoting candidate.")
            should_promote = True

        if should_promote:
            uow.models.promote(candidate, active_model)
            logger.info(f"SUCCESS: Model {candidate.version} promoted to ACTIVE.")
