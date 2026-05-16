import logging
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy import func, select

from app.core.config import settings
from app.infrastructure.db.models import ClassificationModel
from app.infrastructure.db.uow import UnitOfWork
from app.services.ml.pipeline import MLPipeline

logger = logging.getLogger(__name__)

SERVICE_ROOT = Path(__file__).resolve().parents[3]
SEED_DATASET_PATH = SERVICE_ROOT / "seed_data" / "seed_training.csv"
SEED_MODEL_NAME = "lightgbm_tfidf_seed"


async def seed_model_if_empty(session_factory) -> dict[str, Any] | None:
    """Создает первую active ML-модель из committed seed dataset, если registry пуст."""
    async with UnitOfWork(session_factory) as uow:
        model_count = await _count_models(uow)
        if model_count:
            logger.info("ML model registry already initialized: %s", model_count)
            return None

    if not SEED_DATASET_PATH.exists():
        logger.warning("Seed ML dataset not found: %s", SEED_DATASET_PATH)
        return None

    logger.info("ML model registry is empty. Training seed model from %s", SEED_DATASET_PATH)
    training_df = pd.read_csv(SEED_DATASET_PATH)
    version, metrics = await MLPipeline.train_model(training_df)

    async with UnitOfWork(session_factory) as uow:
        model_entry = ClassificationModel(
            name=SEED_MODEL_NAME,
            version=version,
            path=settings.ML.MODEL_PATH,
            metrics=metrics,
            is_active=False,
        )
        uow.models.create(model_entry)
        await uow.flush()
        await uow.models.promote(model_entry, active=None)

    result = {
        "version": version,
        "dataset_path": str(SEED_DATASET_PATH),
        "dataset_size": metrics.get("dataset_size"),
        "unique_classes": metrics.get("unique_classes_after_filter"),
        "val_f1_weighted": metrics.get("val_f1_weighted"),
    }
    logger.info("Seed ML model promoted: %s", result)

    return result


async def _count_models(uow: UnitOfWork) -> int:
    result = await uow.session.execute(
        select(func.count()).select_from(ClassificationModel),
    )

    return int(result.scalar_one())
