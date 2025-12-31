import asyncio
import logging
from datetime import datetime
from app.infrastructure.db.uow import UnitOfWork
from app.services.ml.pipeline import MLPipeline

logger = logging.getLogger(__name__)

class ModelManager:
    """Singleton для управления моделью в памяти."""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ModelManager, cls).__new__(cls)
            cls._instance.model = None
            cls._instance.vectorizer = None
            cls._instance.class_labels = None
            cls._instance.model_version = None
            cls._instance.last_check = datetime.min
        return cls._instance

    def get_pipeline(self):
        """Возвращает текущий снапшот пайплайна (thread-safe for reading pointers)."""
        if not self.model: return None
        return {
            "model": self.model,
            "vectorizer": self.vectorizer,
            "classLabels": self.class_labels,
            "modelVersion": self.model_version
        }

    async def check_for_updates(self, db_session_maker):
        """Проверяет наличие новой модели в БД через UoW."""
        now = datetime.now()
        if (now - self.last_check).total_seconds() < 60 and self.model_version:
            return 
        
        try:
            uow = UnitOfWork(db_session_maker)
            async with uow:
                active_model = await uow.models.get_active_model()
                
                if not active_model:
                    if self.model_version:
                        logger.warning("No active model in DB. Unloading current.")
                        self.model = None
                        self.model_version = None
                    return

                if active_model.version != self.model_version:
                    logger.info(f"Loading new model version: {active_model.version}")
                    
                    loop = asyncio.get_running_loop()
                    model, vec, labels = await loop.run_in_executor(
                        None, 
                        MLPipeline.load_model_sync, 
                        active_model.version
                    )
                    
                    if model:
                        self.model = model
                        self.vectorizer = vec
                        self.class_labels = labels
                        self.model_version = active_model.version
                        logger.info(f"Hot Reload Success: v{self.model_version}")
                    else:
                        logger.error(f"Failed to load files for v{active_model.version}")
                
                self.last_check = now
        except Exception as e:
            logger.error(f"Error updating model: {e}")

modelManager = ModelManager()