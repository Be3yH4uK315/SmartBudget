import logging
from datetime import datetime, timezone
import pandas as pd
from sqlalchemy.future import select
from app.models import Feedback, ClassificationResult, TrainingDataset, TrainingDatasetStatus
from app.settings import settings

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
        new_version = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        dataset_entry = TrainingDataset(
            version=new_version,
            file_path=f"{settings.dataset_path}/dataset_{new_version}.parquet",
            status=TrainingDatasetStatus.BUILDING,
        )
        session.add(dataset_entry)
        await session.commit()
        
        try:
            logger.info("Loading all feedback...")
            feedback_list = []
            batch_size = 1000
            offset = 0
            while True:
                feedback_query = await session.execute(
                    select(Feedback).order_by(Feedback.id).limit(batch_size).offset(offset)
                )
                batch = feedback_query.scalars().all()
                if not batch:
                    break
                feedback_list.extend(batch)
                offset += batch_size
            
            if not feedback_list:
                logger.info("No feedback found. Aborting dataset build.")
                dataset_entry.status = TrainingDatasetStatus.FAILED
                dataset_entry.metrics = {"error": "No feedback found"}
                await session.commit()
                return

            logger.info(f"Loaded {len(feedback_list)} feedback items.")

            data_for_training = []
            for i in range(0, len(feedback_list), batch_size):
                batch_fb = feedback_list[i:i+batch_size]
                feedback_transaction_ids = [fb.transaction_id for fb in batch_fb]
                
                results_stmt = await session.execute(
                    select(ClassificationResult)
                    .where(ClassificationResult.transaction_id.in_(feedback_transaction_ids))
                )
                results_map = {res.transaction_id: res for res in results_stmt.scalars().all()}
                
                for fb in batch_fb:
                    result_data = results_map.get(fb.transaction_id)
                    if not result_data:
                        logger.warning(f"No ClassificationResult for feedback {fb.id}. Skipping.")
                        continue

                    data_for_training.append({
                        "merchant": result_data.merchant,
                        "description": result_data.description,
                        "mcc": result_data.mcc,
                        "label": str(fb.correct_category_id)
                    })
            
            if not data_for_training:
                logger.info("No valid training data after ETL. Aborting.")
                dataset_entry.status = TrainingDatasetStatus.FAILED
                dataset_entry.metrics = {"error": "No valid data after ETL"}
                await session.commit()
                return

            logger.info(f"Converting {len(data_for_training)} rows to DataFrame...")
            df = pd.DataFrame(data_for_training)
            
            logger.info(f"Saving DataFrame to {dataset_entry.file_path}...")
            df.to_parquet(dataset_entry.file_path, index=False, engine='pyarrow')

            dataset_entry.status = TrainingDatasetStatus.READY
            dataset_entry.metrics = {
                "row_count": len(df),
                "class_distribution": df['label'].value_counts().to_dict()
            }
            await session.commit()
            logger.info(f"SUCCESS: Training dataset {new_version} is ready.")

        except Exception as e:
            logger.exception("Training dataset build task failed")
            if 'dataset_entry' in locals():
                dataset_entry.status = TrainingDatasetStatus.FAILED
                dataset_entry.metrics = {"error": str(e)}
                await session.commit()
            await session.rollback()
            raise