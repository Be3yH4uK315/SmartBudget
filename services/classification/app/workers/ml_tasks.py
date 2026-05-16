import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from app.core.config import settings
from app.infrastructure.db.models import (
    ClassificationModel,
    TrainingDataset,
    TrainingDatasetStatus,
)
from app.infrastructure.db.uow import UnitOfWork
from app.services.ml.pipeline import MLPipeline

logger = logging.getLogger(__name__)

TRAINING_DATA_DAYS_LIMIT = 180
TRAINING_DATA_BATCH_SIZE = 5000
MIN_TRAINING_ROWS = 50
MIN_CANDIDATE_F1 = 0.6
MODEL_PROMOTION_TOLERANCE = 0.02


async def build_dataset_task(ctx: dict[str, Any]) -> None:
    """Собирает training dataset из feedback за последние 180 дней."""
    logger.info("Starting training dataset build task")

    db_session_maker = ctx.get("db_session_maker")
    if not db_session_maker:
        logger.error("No db_session_maker in ARQ context. Aborting")
        return

    dataset_id = uuid.uuid4()
    dataset_version = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    file_path = f"{settings.ML.DATASET_PATH}/dataset_{dataset_version}.parquet"

    os.makedirs(settings.ML.DATASET_PATH, exist_ok=True)

    await _create_dataset_entry(
        db_session_maker=db_session_maker,
        dataset_id=dataset_id,
        dataset_version=dataset_version,
        file_path=file_path,
    )

    writer: pq.ParquetWriter | None = None

    try:
        total_rows, class_distribution, writer = await _write_training_dataset(
            db_session_maker=db_session_maker,
            file_path=file_path,
        )

        if writer:
            writer.close()
            writer = None

        if total_rows == 0:
            raise ValueError("No training data collected")

        await _mark_dataset_ready(
            db_session_maker=db_session_maker,
            dataset_id=dataset_id,
            total_rows=total_rows,
            class_distribution=class_distribution,
        )
        await _mark_training_feedback_processed(db_session_maker)

        logger.info(
            "Dataset %s ready. Rows: %s",
            dataset_version,
            total_rows,
        )

    except Exception as exc:
        logger.exception("Training dataset build failed")

        if writer:
            try:
                writer.close()
            except Exception:
                logger.debug("Failed to close parquet writer", exc_info=True)

        await _mark_dataset_failed(
            db_session_maker=db_session_maker,
            dataset_id=dataset_id,
            error=exc,
        )


async def retrain_model_task(ctx: dict[str, Any]) -> None:
    """Обучает модель на последнем готовом датасете."""
    logger.info("Starting scheduled model retraining")

    db_session_maker = ctx.get("db_session_maker")
    if not db_session_maker:
        logger.error("No db_session_maker in ARQ context. Aborting")
        return

    dataset_path = await _get_latest_ready_dataset_path(db_session_maker)
    if not dataset_path:
        return

    try:
        if not os.path.exists(dataset_path):
            logger.error("Dataset file not found: %s", dataset_path)
            return

        training_df = pd.read_parquet(dataset_path)
        if len(training_df) < MIN_TRAINING_ROWS:
            logger.info(
                "Not enough training data: %s rows. Skipping",
                len(training_df),
            )
            return

        model_version, metrics = await MLPipeline.train_model(training_df)

        async with UnitOfWork(db_session_maker) as uow:
            model_entry = ClassificationModel(
                name="lightgbm_tfidf",
                version=model_version,
                path=settings.ML.MODEL_PATH,
                metrics=metrics,
                is_active=False,
            )
            uow.models.create(model_entry)

        logger.info(
            "Model %s created. Weighted F1: %.4f",
            model_version,
            metrics.get("val_f1_weighted", 0),
        )

    except Exception:
        logger.exception("Model retraining task failed")


async def promote_model_task(ctx: dict[str, Any]) -> None:
    """Проверяет кандидат-модель и при необходимости продвигает ее в active."""
    logger.info("Starting model promotion check")

    db_session_maker = ctx.get("db_session_maker")
    if not db_session_maker:
        logger.error("No db_session_maker in ARQ context. Aborting")
        return

    async with UnitOfWork(db_session_maker) as uow:
        active_model = await uow.models.get_active_model()
        candidate = await uow.models.get_latest_candidate()

        if not candidate:
            logger.info("No candidate model found")
            return

        if not _candidate_metrics_are_valid(candidate.metrics):
            logger.warning(
                "Candidate %s rejected. Missing or invalid metrics",
                candidate.version,
            )
            return

        artifacts_valid, artifacts_error, _metadata = (
            MLPipeline.validate_artifacts_sync(candidate.version)
        )
        if not artifacts_valid:
            logger.warning(
                "Candidate %s rejected. %s",
                candidate.version,
                artifacts_error,
            )
            return

        candidate_f1 = _extract_f1(candidate.metrics or {})
        if candidate_f1 < MIN_CANDIDATE_F1:
            logger.warning(
                "Candidate %s rejected. Low F1: %.3f",
                candidate.version,
                candidate_f1,
            )
            return

        if _should_promote_candidate(
            candidate_f1=candidate_f1,
            active_metrics=active_model.metrics if active_model else None,
        ):
            await uow.models.promote(candidate, active_model)
            logger.info(
                "Model %s promoted to ACTIVE",
                candidate.version,
            )


async def _create_dataset_entry(
    db_session_maker,
    dataset_id: uuid.UUID,
    dataset_version: str,
    file_path: str,
) -> None:
    """Создает запись датасета в статусе BUILDING."""
    async with UnitOfWork(db_session_maker) as uow:
        dataset_entry = TrainingDataset(
            training_dataset_id=dataset_id,
            version=dataset_version,
            file_path=file_path,
            status=TrainingDatasetStatus.BUILDING,
        )
        uow.datasets.create(dataset_entry)


async def _write_training_dataset(
    db_session_maker,
    file_path: str,
) -> tuple[int, dict[str, int], pq.ParquetWriter | None]:
    """Пишет training dataset в parquet пачками."""
    total_rows = 0
    class_distribution: dict[str, int] = {}
    writer: pq.ParquetWriter | None = None

    async with UnitOfWork(db_session_maker) as uow:
        async for batch_data in uow.feedback.stream_training_data(
            days_limit=TRAINING_DATA_DAYS_LIMIT,
            batch_size=TRAINING_DATA_BATCH_SIZE,
        ):
            if not batch_data:
                continue

            df_chunk = pd.DataFrame(batch_data)
            df_chunk.fillna(
                {
                    "merchant": "",
                    "description": "",
                    "mcc": 0,
                },
                inplace=True,
            )

            _update_class_distribution(
                class_distribution=class_distribution,
                df_chunk=df_chunk,
            )

            table = pa.Table.from_pandas(df_chunk)

            if writer is None:
                writer = pq.ParquetWriter(
                    file_path,
                    table.schema,
                    compression="snappy",
                )

            writer.write_table(table)
            total_rows += len(df_chunk)

    return total_rows, class_distribution, writer


def _update_class_distribution(
    class_distribution: dict[str, int],
    df_chunk: pd.DataFrame,
) -> None:
    """Обновляет распределение классов."""
    counts = df_chunk["label"].value_counts().to_dict()

    for class_id, count in counts.items():
        class_key = str(class_id)
        class_distribution[class_key] = (
            class_distribution.get(class_key, 0) + int(count)
        )


async def _mark_dataset_ready(
    db_session_maker,
    dataset_id: uuid.UUID,
    total_rows: int,
    class_distribution: dict[str, int],
) -> None:
    """Помечает датасет как READY."""
    async with UnitOfWork(db_session_maker) as uow:
        dataset = await uow.datasets.get_by_id(dataset_id)
        if not dataset:
            return

        await uow.datasets.update_status(
            dataset,
            TrainingDatasetStatus.READY,
            {
                "row_count": total_rows,
                "class_distribution": class_distribution,
            },
        )


async def _mark_dataset_failed(
    db_session_maker,
    dataset_id: uuid.UUID,
    error: Exception,
) -> None:
    """Помечает датасет как FAILED."""
    async with UnitOfWork(db_session_maker) as uow:
        dataset = await uow.datasets.get_by_id(dataset_id)
        if not dataset:
            return

        await uow.datasets.update_status(
            dataset,
            TrainingDatasetStatus.FAILED,
            {
                "error": str(error),
            },
        )


async def _mark_training_feedback_processed(db_session_maker) -> None:
    """Помечает feedback обработанным только после успешной сборки датасета."""
    async with UnitOfWork(db_session_maker) as uow:
        processed_count = await uow.feedback.mark_unprocessed_as_processed()

    logger.info("Marked %s feedback rows as processed", processed_count)


async def _get_latest_ready_dataset_path(db_session_maker) -> str | None:
    """Возвращает путь к последнему READY датасету."""
    async with UnitOfWork(db_session_maker) as uow:
        logger.info("Finding latest READY training dataset")
        dataset = await uow.datasets.get_latest_ready()
        if not dataset:
            logger.info("No READY training datasets found. Skipping")
            return None

        return dataset.file_path


def _extract_f1(metrics: dict[str, Any]) -> float:
    """Извлекает F1 из metrics."""
    return float(metrics.get("val_f1_weighted", metrics.get("val_f1", 0)))


def _candidate_metrics_are_valid(metrics: dict[str, Any] | None) -> bool:
    """Проверяет, что candidate содержит минимальные метрики качества."""
    if not metrics:
        return False

    return "val_f1_weighted" in metrics or "val_f1" in metrics


def _should_promote_candidate(
    candidate_f1: float,
    active_metrics: dict[str, Any] | None,
) -> bool:
    """Определяет, нужно ли продвигать кандидат-модель."""
    if not active_metrics:
        logger.info("No active model. Promoting candidate")
        return True

    active_f1 = _extract_f1(active_metrics)

    if candidate_f1 > active_f1:
        logger.info(
            "Promoting candidate: candidate F1 %.3f > active F1 %.3f",
            candidate_f1,
            active_f1,
        )
        return True

    if candidate_f1 > active_f1 - MODEL_PROMOTION_TOLERANCE:
        logger.info(
            "Candidate is close to active model but not better: "
            "candidate F1 %.3f, active F1 %.3f",
            candidate_f1,
            active_f1,
        )

    return False
