import logging
import pandas as pd
import pyarrow as pa
import uuid
import os
from datetime import datetime, timezone
import pyarrow.parquet as pq

from app.core.config import settings
from app.infrastructure.db.uow import UnitOfWork
from app.infrastructure.db.models import (
    ClassificationModel,
    TrainingDataset,
    TrainingDatasetStatus,
)
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
    file_path = f"{settings.ML.DATASET_PATH}/dataset_{new_version}.parquet"
    os.makedirs(settings.ML.DATASET_PATH, exist_ok=True)

    async with UnitOfWork(db_session_maker) as uow:
        dataset_entry = TrainingDataset(
            training_dataset_id=dataset_id,
            version=new_version,
            file_path=file_path,
            status=TrainingDatasetStatus.BUILDING,
        )
        uow.datasets.create(dataset_entry)

    try:
        total_rows = 0
        class_distribution = {}
        writer = None
        
        async with UnitOfWork(db_session_maker) as uow:
            async for batch_data in uow.feedback.stream_training_data(days_limit=180, batch_size=5000):
                if not batch_data:
                    continue
                
                df_chunk = pd.DataFrame(batch_data)
                df_chunk.fillna({'merchant': '', 'description': '', 'mcc': 0}, inplace=True)
                
                counts = df_chunk['label'].value_counts().to_dict()
                for k, v in counts.items():
                    k_str = str(k)
                    class_distribution[k_str] = class_distribution.get(k_str, 0) + v
                
                table = pa.Table.from_pandas(df_chunk)
                
                if writer is None:
                    writer = pq.ParquetWriter(file_path, table.schema, compression='snappy')
                
                writer.write_table(table)
                total_rows += len(df_chunk)
            
            if writer:
                writer.close()
            
            await uow.feedback.mark_unprocessed_as_processed()

        if total_rows == 0:
            raise ValueError("No training data collected")

        async with UnitOfWork(db_session_maker) as uow:
            dataset = await uow.datasets.get_by_id(dataset_id)
            if dataset:
                await uow.datasets.update_status(
                    dataset, 
                    TrainingDatasetStatus.READY, 
                    {
                        "row_count": total_rows,
                        "class_distribution": class_distribution
                    }
                )
                logger.info(f"SUCCESS: Dataset {new_version} READY. Rows: {total_rows}")

    except Exception as e:
        logger.exception("Training dataset build failed")
        if writer:
            try: writer.close()
            except: pass
        
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
            model_entry = ClassificationModel(
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
