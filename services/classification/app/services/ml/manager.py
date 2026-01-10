import asyncio
from dataclasses import dataclass
import logging
from datetime import datetime
from typing import Any, Optional
from app.infrastructure.db.uow import UnitOfWork
from app.services.ml.pipeline import MLPipeline

logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class ModelArtifacts:
    """Неизменяемый контейнер для артефактов модели. Гарантирует целостность."""
    model: Any
    vectorizer: Any
    class_labels: list[int]
    version: str

class ModelManager:
    """Singleton для управления моделью в памяти."""
    _instance = None
    _artifacts: Optional[ModelArtifacts] = None
    last_check: datetime
    _lock: asyncio.Lock
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ModelManager, cls).__new__(cls)
            cls._instance._artifacts = None
            cls._instance.last_check = datetime.min
            cls._instance._lock = asyncio.Lock()
            
        return cls._instance

    def get_pipeline(self) -> dict | None:
        """Возвращает словарь с компонентами."""
        artifacts = self._artifacts
        if not artifacts:
            return None
            
        return {
            "model": artifacts.model,
            "vectorizer": artifacts.vectorizer,
            "classLabels": artifacts.class_labels,
            "modelVersion": artifacts.version
        }

    async def check_for_updates(self, db_session_maker):
        """Проверяет наличие новой модели в БД и загружает её атомарно."""
        now = datetime.now()
        if (now - self.last_check).total_seconds() < 60 and self._artifacts:
            return 
        
        if self._lock.locked():
            return

        async with self._lock:
            try:
                uow = UnitOfWork(db_session_maker)
                async with uow:
                    active_model = await uow.models.get_active_model()
                    
                    if not active_model:
                        if self._artifacts:
                            logger.warning("No active model in DB. Unloading current.")
                            self._artifacts = None
                        return

                    current_ver = self._artifacts.version if self._artifacts else None
                    if active_model.version != current_ver:
                        logger.info(f"Found new model version: {active_model.version}. Loading...")
                        
                        loop = asyncio.get_running_loop()
                        model, vec, labels = await loop.run_in_executor(
                            None, 
                            MLPipeline.load_model_sync, 
                            active_model.version
                        )
                        
                        if model and vec:
                            self._artifacts = ModelArtifacts(
                                model=model,
                                vectorizer=vec,
                                class_labels=labels,
                                version=active_model.version
                            )
                            logger.info(f"Hot Reload Success: v{active_model.version}")
                        else:
                            logger.error(f"Failed to load files for v{active_model.version}")
                    
                    self.last_check = now
            except Exception as e:
                logger.error(f"Error updating model: {e}")

modelManager = ModelManager()