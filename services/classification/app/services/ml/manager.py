import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.infrastructure.db.uow import UnitOfWork
from app.services.ml.pipeline import MLPipeline

logger = logging.getLogger(__name__)

MODEL_UPDATE_CHECK_INTERVAL_SECONDS = 60


@dataclass(frozen=True)
class ModelArtifacts:
    """Неизменяемый контейнер артефактов ML-модели."""

    model: Any
    vectorizer: Any
    class_labels: list[int]
    version: str


class ModelManager:
    """Singleton manager для активной ML-модели в памяти."""

    _instance = None
    _artifacts: ModelArtifacts | None = None
    last_check: datetime
    _lock: asyncio.Lock

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ModelManager, cls).__new__(cls)
            cls._instance._artifacts = None
            cls._instance.last_check = datetime.min
            cls._instance._lock = asyncio.Lock()

        return cls._instance

    def get_pipeline(self) -> dict[str, Any] | None:
        """Возвращает текущий ML pipeline."""
        artifacts = self._artifacts
        if not artifacts:
            return None

        return {
            "model": artifacts.model,
            "vectorizer": artifacts.vectorizer,
            "classLabels": artifacts.class_labels,
            "modelVersion": artifacts.version,
        }

    async def check_for_updates(self, db_session_maker) -> None:
        """Проверяет наличие новой активной модели и загружает ее."""
        now = datetime.now()
        if not self._should_check_for_updates(now):
            return

        if self._lock.locked():
            return

        async with self._lock:
            await self._load_active_model_if_needed(
                db_session_maker=db_session_maker,
                now=now,
            )

    def _should_check_for_updates(self, now: datetime) -> bool:
        """Проверяет, нужно ли обращаться к БД за новой моделью."""
        if self._artifacts is None:
            return True

        elapsed_seconds = (now - self.last_check).total_seconds()

        return elapsed_seconds >= MODEL_UPDATE_CHECK_INTERVAL_SECONDS

    async def _load_active_model_if_needed(
        self,
        db_session_maker,
        now: datetime,
    ) -> None:
        """Загружает активную модель, если версия изменилась."""
        try:
            active_model = await self._get_active_model(db_session_maker)

            if not active_model:
                self._unload_if_needed()
                self.last_check = now
                return

            current_version = self._artifacts.version if self._artifacts else None
            if active_model.version == current_version:
                self.last_check = now
                return

            await self._load_model_version(active_model.version)
            self.last_check = now

        except Exception as exc:
            logger.error("Error updating model: %s", exc, exc_info=True)

    @staticmethod
    async def _get_active_model(db_session_maker):
        """Получает активную модель из БД."""
        uow = UnitOfWork(db_session_maker)
        async with uow:
            return await uow.models.get_active_model()

    def _unload_if_needed(self) -> None:
        """Выгружает текущую модель, если в БД больше нет активной модели."""
        if not self._artifacts:
            return

        logger.warning("No active model in DB. Unloading current model")
        self._artifacts = None

    async def _load_model_version(self, version: str) -> None:
        """Загружает конкретную версию модели с диска."""
        logger.info("Found new model version: %s. Loading", version)

        loop = asyncio.get_running_loop()
        model, vectorizer, labels = await loop.run_in_executor(
            None,
            MLPipeline.load_model_sync,
            version,
        )

        if not model or not vectorizer:
            logger.error("Failed to load files for model version %s", version)
            return

        self._artifacts = ModelArtifacts(
            model=model,
            vectorizer=vectorizer,
            class_labels=labels or [],
            version=version,
        )

        logger.info("Hot reload success: model version %s", version)


modelManager = ModelManager()
