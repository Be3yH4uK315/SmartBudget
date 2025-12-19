from concurrent.futures import ProcessPoolExecutor
import logging
import joblib
import re
import asyncio
from datetime import datetime
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score
from lightgbm import LGBMClassifier
from typing import Tuple

from app import settings, repositories

logger = logging.getLogger(__name__)

MODEL_FILE_NAME = "lgbm_model.pkl"
VECTORIZER_FILE_NAME = "tfidf_vectorizer.pkl"

def _preprocessText(text: str) -> str:
    """Очистка текста для TF-IDF."""
    if not text or pd.isna(text):
        return ""
    text = str(text).lower()
    text = re.sub(r'\d+', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    return text

def _createFeaturesFromDict(data: dict) -> str:
    """Собирает все текстовые поля в одну строку для TF-IDF."""
    merchant = data.get('merchant', '') if not pd.isna(data.get('merchant')) else ''
    description = data.get('description', '') if not pd.isna(data.get('description')) else ''
    mcc = data.get('mcc')
    mccStr = f"mcc_{mcc}" if mcc and not pd.isna(mcc) else ""
    return _preprocessText(f"{merchant} {description} {mccStr}")

def _sanitizeMetrics(metrics: dict) -> dict:
    clean = {}
    for k, v in metrics.items():
        if isinstance(v, (np.integer, np.int64, np.int32, np.int16, np.int8)):
            clean[k] = int(v)
        elif isinstance(v, (np.floating, np.float64, np.float32, np.float16)):
            clean[k] = float(v)
        elif isinstance(v, np.ndarray):
            clean[k] = v.tolist()
        elif isinstance(v, dict):
            clean[k] = _sanitizeMetrics(v)
        else:
            clean[k] = v
    return clean

def _trainInternalProcess(df_dict: dict) -> Tuple[str | None, dict]:
    try:
        df = pd.DataFrame(df_dict)
        df.fillna({'merchant': '', 'description': '', 'mcc': 0}, inplace=True)
        uniqueClasses = df['label'].nunique()
        
        if uniqueClasses < 2:
            return None, {"error": "Insufficient unique classes (need at least 2)"}

        if len(df) < 50:
            return None, {"error": "Insufficient data size (< 50 samples). Overfitting risk."}

        df['features'] = df.apply(lambda row: _createFeaturesFromDict(row.to_dict()), axis=1)
        X = df['features']
        y = df['label'].astype(int)

        X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)

        vectorizer = TfidfVectorizer(max_features=5000, ngram_range=(1, 2))
        X_train_tfidf = vectorizer.fit_transform(X_train)

        model = LGBMClassifier(n_estimators=100, learning_rate=0.1, objective='multiclass', n_jobs=1, verbose=-1)
        model.fit(X_train_tfidf, y_train)

        metrics = {"dataset_size": len(df), "uniqueClasses": int(uniqueClasses)}
        y_train_pred = model.predict(X_train_tfidf)
        metrics["train_accuracy"] = accuracy_score(y_train, y_train_pred)
        metrics["train_f1"] = f1_score(y_train, y_train_pred, average='macro')
        
        X_val_tfidf = vectorizer.transform(X_val)
        y_val_pred = model.predict(X_val_tfidf)
        metrics["val_accuracy"] = accuracy_score(y_val, y_val_pred)
        metrics["val_f1"] = f1_score(y_val, y_val_pred, average='macro')
        
        new_version = datetime.now().strftime("%Y%m%d_%H%M%S")
        modelPath = f"{settings.settings.ML.MODEL_PATH}/{new_version}_{MODEL_FILE_NAME}"
        vectorizerPath = f"{settings.settings.ML.MODEL_PATH}/{new_version}_{VECTORIZER_FILE_NAME}"
        
        joblib.dump(model, modelPath)
        joblib.dump(vectorizer, vectorizerPath)
        
        return new_version, metrics
    except Exception as e:
        return None, {"error": str(e)}

class MLService:
    """Управляет обучением, сохранением и загрузкой ML-моделей."""
    
    @staticmethod
    async def train_model(training_df: pd.DataFrame) -> Tuple[str, dict]:
        """Асинхронная обертка для обучения."""
        loop = asyncio.get_running_loop()
        df_data = training_df.to_dict(orient='list')
        
        with ProcessPoolExecutor(max_workers=1) as pool:
            result = await loop.run_in_executor(pool, _trainInternalProcess, df_data)
        
        if result[0] is None:
            raise ValueError(result[1].get("error"))
            
        version, metrics = result
        clean_metrics = _sanitizeMetrics(metrics)
        return version, clean_metrics

    @staticmethod
    def _loadInternal(model_version: str) -> Tuple[LGBMClassifier | None, TfidfVectorizer | None, list | None]:
        """Синхронная загрузка модели с диска."""
        try:
            model_path = f"{settings.settings.ML.MODEL_PATH}/{model_version}_{MODEL_FILE_NAME}"
            vectorizer_path = f"{settings.settings.ML.MODEL_PATH}/{model_version}_{VECTORIZER_FILE_NAME}"
            
            model = joblib.load(model_path)
            vectorizer = joblib.load(vectorizer_path)
            
            class_labels = list(range(model.n_classes_)) if hasattr(model, 'n_classes_') else None
            
            logger.info(f"Successfully loaded model version {model_version}")
            return model, vectorizer, class_labels
        except FileNotFoundError as e:
            logger.error(f"Model files not found for version {model_version}: {e}")
            return None, None, None
        except Exception as e:
            logger.error(f"Error loading model {model_version}: {e}")
            return None, None, None

    @staticmethod
    def _predictInternal(
        model: LGBMClassifier, 
        vectorizer: TfidfVectorizer, 
        transaction_data: dict
    ) -> Tuple[int, float]:
        """Синхронный предсказанный результат ML модели."""
        try:
            features_text = _createFeaturesFromDict(transaction_data)
            features_tfidf = vectorizer.transform([features_text])
            
            prediction = model.predict(features_tfidf)[0]
            probabilities = model.predict_proba(features_tfidf)[0]
            confidence = float(np.max(probabilities))
            
            return int(prediction), confidence
        except Exception as e:
            logger.error(f"Error during prediction: {e}")
            raise

    @staticmethod
    async def load_prediction_pipeline(model_version: str) -> Tuple[LGBMClassifier | None, TfidfVectorizer | None, list | None]:
        """Асинхронная загрузка модели."""
        logger.info(f"Loading ML pipeline version {model_version} from disk...")
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, MLService._loadInternal, model_version)

    @staticmethod
    async def predict_async(
        model: LGBMClassifier, 
        vectorizer: TfidfVectorizer, 
        class_labels: list, 
        transaction_data: dict
    ) -> Tuple[int, float]:
        """Асинхронное предсказание."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None, 
            MLService._predictInternal, 
            model, vectorizer, class_labels, transaction_data
        )

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
        """Получает текущий пайплайн."""
        if not self.model:
            return None
        return {
            "model": self.model,
            "vectorizer": self.vectorizer,
            "classLabels": self.class_labels,
            "modelVersion": self.model_version
        }

    async def check_for_updates(self, db_session_maker):
        """Проверяет наличие новой модели в БД."""
        now = datetime.now()
        if (now - self.last_check).total_seconds() < 60 and self.model_version:
            return 
        
        try:
            async with db_session_maker() as session:
                repository = repositories.ModelRepository(session)
                active_model = await repository.get_active_model()
                
                if not active_model:
                    if self.model_version is not None:
                        logger.warning("Active model removed from DB. Unloading.")
                        self.model = None
                        self.model_version = None
                    return

                if active_model.version != self.model_version:
                    logger.info(f"New active model: {active_model.version}")
                    model, vec, labels = await MLService.load_prediction_pipeline(active_model.version)
                    
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
            logger.error(f"Error checking for model updates: {e}")

modelManager = ModelManager()